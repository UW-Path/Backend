from django.core.mail import get_connection, send_mail, EmailMessage
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from app.models import ContactForm, UwpathApp
from app.serializer import AppSerializer
from app.views.communication_view import Communications_List
from app.views.requirement_view import Requirements_List
from uwpath_backend import settings
from django.db.models import Q
from django.core import serializers



'''
This section of code is required for django front end to run.
'''

def index(request):
    #Renders Home page with a drop down of major users can select form
    programs = Requirements_List().get_unique_major_website()
    return render(request, 'index.html', {'programs': programs})


def requirements(request):
    ##### !important this is depricated code
    # Note option includes requirement
    # One major and option allowed, allow flexibility for multiple minors

    major = str(request.GET['major'])
    option = str(request.GET['option'])
    #minors is a string seperated by commas
    minors = request.GET['minors']

    if not major:
        return Response(status=status.HTTP_404_NOT_FOUND)

    minors = minors.split(", ")

    #flag to include table
    has_table1 = False
    has_table2 = False

    #Renders the requiremnts + table for major/minor requested for
    #communications for math
    table1 = Communications_List().get_list()
    #Basic honors math req
    table2 = Requirements_List().get_major_requirement("Table II")
    # so we don't exclude courses from requirement
    table2_course_codes = [r["course_codes"] for r in table2 if("Table II" in r["additional_requirements"])]

    option_list = Requirements_List().get_unique_major_website()
    #Prevent duplicate courses in table II and major
    requirements = Requirements_List().get_major_requirement(major).exclude(course_codes__in = table2_course_codes)

    #check for additional req in major
    if requirements:
        additional_req = requirements.first()["additional_requirements"]
        if "Table I" in additional_req:
            has_table1 = True
        if "Table II" in additional_req:
            has_table2 = True

        if "Honours" or "BCS" in additional_req:
            #find additional req
            additional_req_list = additional_req.split(",")
            for i in additional_req_list:
                if "Honours" in i or "BCS" in i:
                    if i == "BCS":
                        bcs_req = Requirements_List().get_major_requirement("Bachelor of Computer Science")
                        requirements = bcs_req | requirements
                        if "Table II" in bcs_req.first()["additional_requirements"]:
                            requirements = table2 | requirements
                        requirements = requirements.distinct()
                    else:
                        i = str(i).replace("Honours ", "")
                        new_req = Requirements_List().get_major_requirement(i)
                        requirements = new_req | requirements
                        if "Table II" in new_req.first()["additional_requirements"]:
                            requirements = table2 | requirements
                        requirements = requirements.distinct()
                    break
    else:
        return HttpResponseNotFound('Major not valid')

    #filter options returned
    majorName = requirements.first()['major_name']
    option_list = option_list.filter(Q(major_name = majorName) | Q(plan_type = "Joint")).exclude(Q(plan_type = "Major") | Q(plan_type = "Minor"))
    option_list = option_list.order_by('plan_type', 'program_name')

    #filter minor returned
    minor_list = Requirements_List().get_unique_major_website().filter(plan_type="Minor")
    minor_list = minor_list.order_by('program_name')

    # specializations and options
    if option:
        option_requirements = Requirements_List().get_minor_requirement(option)
        requirements_course_codes_list = [r["course_codes"] for r in requirements]
        option_requirements = option_requirements.filter(Q(major_name = majorName) | Q(plan_type = "Joint"))
        option_requirements = option_requirements.exclude(course_codes__in = requirements_course_codes_list)
        if not option_requirements:
            return HttpResponseNotFound('404 Not Found: Minor not valid')

    if minors:
        minor_requirements = dict()
        for minor in minors:
            minor_requirements[minor] = Requirements_List().get_minor_requirement(minor)
            requirements_course_codes_list = [r["course_codes"] for r in requirements]
            if option:
                option_course_codes_list = [r["course_codes"] for r in option_requirements]

            minor_requirements[minor] = minor_requirements[minor].exclude(course_codes__in=requirements_course_codes_list)

            if option:
                minor_requirements[minor] = minor_requirements[minor].exclude(course_codes__in=option_course_codes_list)

            if not minor_requirements[minor]:
                return HttpResponseNotFound('404 Not Found: Minor not valid')
            else: minor_requirements[minor] = list(minor_requirements[minor])

    data = {
        'option_list': list(option_list),
        'minor_list': list(minor_list),
        'major': major,
        'requirements': list(requirements)
    }

    if has_table1:
        data['table1'] = list(table1)
    if has_table2:
        data['table2'] = list(table2)

    if option:
        data['option'] = option
        data['option_requirements'] = list(option_requirements)

    if minors:
        data['minor'] = minors
        # This is a dictionary of all the minors! Since we can have multiple minors
        # minor_requirements is a dictionary object
        data['minor_requirements'] = minor_requirements

    return JsonResponse(data)




def contact(request):
    #Contact me form
    submitted = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # for debugging
            # con = get_connection('django.core.mail.backends.console.EmailBackend')
            try:
                subject = cd['subject'] + ' from ' + cd['email']
                msg = EmailMessage(subject,
                          cd['message'],
                          settings.EMAIL_HOST_USER,
                          [settings.EMAIL_HOST_USER])
                msg.send()
            except:
                return render(request, 'contact.html', {'form': form, 'submitted': submitted, 'error': True})

            return HttpResponseRedirect('/contact?submitted=True')
    else:
        form = ContactForm()
        if 'submitted' in request.GET:
            submitted = True
    return render(request, 'contact.html', {'form': form, 'submitted': submitted})



# Anything that starts with class (APIView) can be accessed through url.py via Django Restframework
class AllApp(APIView):
    queryset = UwpathApp.objects.all()
    serializer_class = AppSerializer

    def post(self, request, format=None):
        serializer = AppSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppView(APIView):
    def get(self, request, format=None):
        try:
            pk = str(request.GET['pk'])
            app = UwpathApp.objects.get(pk=pk)
            serializer = AppSerializer(app)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, format=None):
        app = UwpathApp.objects.get(pk=pk)
        app.delete()
        return Response(status=status.HTTP_200_OK)






