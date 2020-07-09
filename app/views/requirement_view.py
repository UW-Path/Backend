from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import json as js
from collections import namedtuple

from xlwt import Borders

from app.models import Requirements
from app.serializer import RequirementsSerializer
from app.views.communication_view import Communications_List

import xlwt
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

    @api_view(('GET',))
    def download_course_schedule(request):
        """
        return a excel file for users to click download
        """
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="schedule.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Course_Schedule')  # this will make a sheet named Users Data

        # Sheet header, first row
        row_num = 0

        title_font = xlwt.XFStyle()
        title_font.font.bold = True
        ws.write(0, 0, "UWPath", title_font)
        row_num += 2

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        font_style.borders.bottom = Borders.THIN

        #should get from front end
        columns = ['1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B' ]
        courses = [['MATH 100','MATH 101','MATH 102', 'MATH 103', 'MATH 104'],
                   ['MATH 110', 'MATH 111', 'MATH 112', 'MATH 113', 'MATH 114'],
                   ['MATH 200', 'MATH 201', 'MATH 202', 'MATH 203', 'MATH 204'],
                   ['MATH 220', 'MATH 221', 'MATH 222', 'MATH 223', 'MATH 224'],
                   ['MATH 300', 'MATH 301', 'MATH 302', 'MATH 303', 'MATH 304'],
                   ['AMATH 350', 'PHYCH 101', 'PHIL 102', 'ENGL 103', 'MATH 314'],
                   ['MATH 400', 'MATH 401', 'MATH 402', 'MATH 403', 'MATH 404'],
                   ['MATH 440', 'MATH 441', 'AMATH 122', 'CS 103', 'BIO 104']
                  ]


        for i in range(len(columns)):
            ws.col(i).width = 256 * 15 #10 char width

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)  # at 0 row 0 column

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        c = len(courses)
        r = len((courses[0]))

        for i in range(r):
            row_num += 1
            for col_num in range(c):
                ws.write(row_num, col_num, courses[col_num][i], font_style)

        wb.save(response)

        return response



class Requirements_List(APIView):
    def get(self, request, format=None):
        list = Requirements.objects.all()[:10]
        serializer = RequirementsSerializer(list, many=True)
        return Response(serializer.data)

    @api_view(('GET',))
    def get_unique_major(self, format=None):
        querySet = Requirements.objects.values('program_name', 'plan_type', 'major_name').filter(plan_type="Major").order_by('program_name').distinct()
        return JsonResponse({'Major': list(querySet)})

    def get_unique_major_website(self, format=None):
        querySet = Requirements.objects.values('program_name', 'plan_type', 'major_name').order_by('program_name').distinct()
        return querySet

    def get_major_requirement(self, major):
        querySet = Requirements.objects.values().filter(program_name=major).order_by('program_name')
        return querySet

    def get_minor_requirement(self, minor):
        querySet = Requirements.objects.values().filter(program_name=minor).order_by('program_name')
        return querySet
