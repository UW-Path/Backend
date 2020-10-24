from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

import io
import csv

from app.models import Requirements
from app.serializer import RequirementsSerializer
from app.views.communication_view import Communications_List

from django.http import HttpResponse


class Requirements_API(APIView):
    def get(self, request, pk, format=None):
        try:
            pk = str(request.GET['pk'])
            app = Requirements.objects.get(pk=pk)
            serializer = RequirementsSerializer(app)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self, request, pk, format=None):
        try:
            app = Requirements.objects.get(pk=pk)
            return app
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @api_view(('GET',))
    def requirements(request):
        # Note option includes requirement
        try:
            major = request.GET['major']
            option = request.GET['option']
            minor = request.GET['minor']

            if not major:
                Response(status=status.HTTP_400_BAD_REQUEST)


            # Renders the requiremnts + table for major/minor requested for
            # communications for math
            table1 = Communications_List().get_list()
            # Basic honors math req
            table2 = Requirements_List().get_major_requirement("Table II")
            # so we don't exclude courses from requirement
            table2_course_codes = [r["course_codes"] for r in table2 if ("Table II" in r["additional_requirements"])]

            option_list = Requirements_List().get_unique_major_website()
            # Prevent duplicate courses in table II and major
            requirements = Requirements_List().get_major_requirement(major).exclude(course_codes__in=table2_course_codes)

            # check for additional req in major
            if requirements:
                additional_req = requirements.first()["additional_requirements"]
                if "Honours" or "BCS" in additional_req:
                    # find additional req
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

            if not requirements:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # filter options returned
            majorName = requirements.first()['major_name']
            option_list = option_list.filter(Q(major_name=majorName) | Q(plan_type="Joint")).exclude(
                Q(plan_type="Major") | Q(plan_type="Minor"))
            option_list = option_list.order_by('plan_type', 'program_name')

            # filter minor returned
            minor_list = Requirements_List().get_unique_major_website().filter(plan_type="Minor")
            minor_list = minor_list.order_by('program_name')

            # specializations and options
            if option:
                option_requirements = Requirements_List().get_minor_requirement(option)
                requirements_course_codes_list = [r["course_codes"] for r in requirements]
                option_requirements = option_requirements.filter(Q(major_name=majorName) | Q(plan_type="Joint"))
                option_requirements = option_requirements.exclude(course_codes__in=requirements_course_codes_list)
                if not option_requirements:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            if minor:
                minor_requirements = Requirements_List().get_minor_requirement(minor)
                requirements_course_codes_list = [r["course_codes"] for r in requirements]
                if option:
                    option_course_codes_list = [r["course_codes"] for r in option_requirements]

                minor_requirements = minor_requirements.exclude(course_codes__in=requirements_course_codes_list)

                if option:
                    minor_requirements = minor_requirements.exclude(course_codes__in=option_course_codes_list)
                if not minor_requirements:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                print("fetch minor req")


            #return Response

            # AllReqs = namedtuple('AllRequirement', ('option_list', 'minor_list'))
            # allReqs = AllReqs(option_list=option_list, minor_list=minor_list)
            #
            # return Response(status=status.HTTP_404_NOT_FOUND)




            if option and minor:
                return JsonResponse({'option_list': list(option_list), 'minor_list': list(minor_list), 'major': major,
                               'requirements': list(requirements), 'option': option,
                               'option_requirements': list(option_requirements), 'minor': minor,
                               'minor_requirements': list(minor_requirements),
                               'table1': list(table1), 'table2': list(table2)})

            elif option:
                return JsonResponse({'option_list': list(option_list), 'minor_list': list(minor_list), 'major': major,
                                                      'requirements': list(requirements), 'option': option,
                                                      'option_requirements': list(option_requirements), 'table1': list(table1),
                                                      'table2': list(table2)})
            elif minor:
                return JsonResponse({'option_list': list(option_list), 'minor_list': list(minor_list), 'major': major,
                               'requirements': list(requirements), 'minor': minor,
                               'minor_requirements': list(minor_requirements), 'table1': list(table1), 'table2': list(table2)})

            else:
                return JsonResponse({'option_list':list(option_list), 'minor_list':list(minor_list), 'major':major,
                                     'requirements': list(requirements), 'table1': list(table1), 'table2': list(table2)})
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @api_view(('POST',))
    def download_course_schedule(request):
        """
        return a excel file for users to click download
        """
        courses = request.data["table"]
        if not courses or not len(courses):
            Response(status=status.HTTP_400_BAD_REQUEST)

        buffer = io.StringIO()
        wr = csv.writer(buffer, quoting=csv.QUOTE_ALL)

        terms = []
        for i in range(len(courses)):
            term = str(i//2 + 1) + chr(i % 2 + 65)
            terms.append(term)

        wr.writerow(terms)

        rows = []
        for j, term in enumerate(courses):
            for i, course in enumerate(term):
                if course[-1] != "WAITING":
                    c = course[-1]
                else:
                    c = "/".join(course[:-1])
                while len(rows) <= i:
                    rows.append([])
                print(rows, i)
                while len(rows[i]) < j:
                    rows[i].append("")
                if len(rows[i]) > j:
                    rows[i][j] = c
                else:
                    rows[i].append(c)

        wr.writerows(rows)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=uwpath-schedule.csv'

        return response



class Requirements_List(APIView):
    def get(self, request, format=None):
        list = Requirements.objects.all()[:10]
        serializer = RequirementsSerializer(list, many=True)
        return Response(serializer.data)

    @api_view(('GET',))
    def get_unique_major(self, format=None):
        querySet = Requirements.objects.values('program_name', 'plan_type', 'major_name', 'link').filter(plan_type="Major").order_by('program_name').distinct()
        return JsonResponse({'Major': list(querySet)})

    def get_unique_major_website(self, format=None):
        querySet = Requirements.objects.values('program_name', 'plan_type', 'major_name', 'link').order_by('program_name').distinct()
        return querySet

    def get_major_requirement(self, major):
        querySet = Requirements.objects.values().filter(program_name=major).order_by('program_name')
        return querySet

    def get_minor_requirement(self, minor):
        querySet = Requirements.objects.values().filter(program_name=minor).order_by('program_name')
        return querySet
