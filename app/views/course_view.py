from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import CourseInfo
from app.serializer import CourseInfoSerializer


class Course_Info_API(APIView):
    def get(self, request, format=None):
        try:
            pk = str(request.GET['pk'])
            app = CourseInfo.objects.get(pk=pk)
            serializer = CourseInfoSerializer(app)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self, request, pk, format=None):
        try:
            app = CourseInfo.objects.get(pk=pk)
            return app
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @api_view(('GET',))
    def filter(request):
        try:
            start = int(request.GET['start'])
            end = int(request.GET['end'])
            code = request.GET['code'] #CS, MATH ... ETC

            #Generalization
            if code == "MATH": code = "ACTSC, AMATH, CO, CS, MATH, MATBUS, PMATH, STAT"
            elif code == "SCIENCE": code = "BIOL, CHEM, EARTH, PHYS, SCI"
            elif code == "LANGUAGE": code = "ARABIC, CHINA, CROAT, DUTCH, FR, GER, GRK, ITAL, JAPAN, KOREA, LAT, PORT, RUSS, SPAN"

            if code == "NON-MATH":
                code = ["ACTSC", "AMATH", "CO", "CS", "MATH","MATBUS", "PMATH", "STAT"]
                app = CourseInfo.objects.exclude(course_abbr__in=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            elif "LAB" in code:
                code = code.split(" ")[0]
                app = CourseInfo.objects.filter(course_abbr=code)
                app = app.filter(course_code__contains='L')
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)

            elif code.startswith("~") and any(char.isdigit() for char in code):
                code = code[1:].split(",")
                app = CourseInfo.objects.exclude(course_code__in=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            elif code.startswith("~"):
                code = code[1:].split(",")
                app = CourseInfo.objects.exclude(course_abbr__in=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            elif any(char.isdigit() for char in code):
                code = code.split(",")
                app = CourseInfo.objects.filter(course_code__in=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            elif "," in code:
                code = code.split(", ")
                app = CourseInfo.objects.filter(course_abbr__in=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            elif code != "none":
                app = CourseInfo.objects.filter(course_abbr__exact=code)
                app = app.filter(course_number__gte=start).filter(course_number__lte=end)
            else:
                app = CourseInfo.objects.filter(course_number__gte=start).filter(course_number__lte=end)
            serializer = CourseInfoSerializer(app, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_404_NOT_FOUND)


class Course_Info_List(APIView):
    def get(self, request, format=None):
        list = CourseInfo.objects.all()[:10]
        serializer = CourseInfoSerializer(list, many=True)
        return Response(serializer.data)
