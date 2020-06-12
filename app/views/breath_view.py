from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Breath
from app.serializer import BreathSerializer


class Breath_API(APIView):
    def get(self, request, format=None):
        try:
            # if no primary key, then default go by id
            pk = str(request.GET['pk'])
            app = Breath.objects.get(pk=pk)
            serializer = BreathSerializer(app)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class Breath_List(APIView):
    def get(self, request, format=None):
        list = Breath.objects.all()
        serializer = BreathSerializer(list, many=True)
        return Response(serializer.data)


class BreathAPI(APIView):
    def breadth(self, list_of_courses_taken):
        breadth_objects = Breath.objects.all()
        codes = list(map(lambda x: x.split()[0], list_of_courses_taken))

        human = 2
        soc_sci = 2
        pure_sci = 1
        app_sci = 1
        app_pure = 0

        for code in codes:
            for obj in breadth_objects:
                if obj.subject == code:
                    if obj.humanities and human > 0:
                        human -= 1
                    elif obj.social_science and soc_sci > 0:
                        soc_sci -= 1
                    elif obj.applied_science and obj.pure_science:
                        app_pure += 1
                    elif obj.applied_science and app_sci > 0:
                        app_sci -= 1
                    elif obj.pure_science and pure_sci > 0:
                        pure_sci -= 1

        return not (human or soc_sci or app_pure < app_sci+pure_sci)


    def get(self, request, format=None):
        list_of_courses_taken = request.GET.getlist("list_of_courses_taken[]")

        response_data = {}
        response_data["breadth_met"] = self.breadth(list_of_courses_taken)

        return Response(response_data)

