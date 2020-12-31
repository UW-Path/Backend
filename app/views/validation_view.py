from django.http import HttpResponseNotFound
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from API.ValidationCheckAPI import ValidationCheckAPI
from app.models import CourseInfo
from app.views.antireq_view import Antireqs_API
from app.views.course_view import Course_Info_API
from app.views.prereq_view import Prereqs_API


class UWPath_API(APIView):
    def get(self, request, format=None):
        try:
            pk = str(request.GET['pk'])

            api = ValidationCheckAPI()

            #Check if valid course first
            courseInfo = Course_Info_API().get_object(None, pk)
            if (type(courseInfo) != CourseInfo):
                return HttpResponseNotFound('<h1>404 Not Found: Course not valid</h1>')

            prereqs = Prereqs_API().get_object(None, pk)
            antireqs = Antireqs_API().get_object(None, pk)

            api.set_prereqs(prereqs.logic, prereqs.courses)
            api.set_antireqs(antireqs.antireq)

            list_of_courses_taken = UWPath_API.__dup_E_courses(request.GET.getlist("list_of_courses_taken[]"))
            current_term_courses = UWPath_API.__dup_E_courses(request.GET.getlist("current_term_courses[]"))

            can_take, msg = api.can_take_course(list_of_courses_taken, current_term_courses, pk)

            response_data = {}

            if can_take:
                response_data["can_take"] = True
            else:
                response_data["can_take"] = False
                response_data["msg"] = msg

            return Response(response_data)

        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def __dup_E_courses(courses):
        """Some courses may end with E. In this case, we handle as taken with E and without"""
        n = len(courses)
        for i in range(n):
            if courses[i][-1] == "E":
                courses.append(courses[i][:-1])
        return courses
