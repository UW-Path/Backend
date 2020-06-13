from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Communications
from app.serializer import CommunicationsSerializer


class Communications_API(APIView):
    def get(self, request, format=None):
        try:
            pk = str(request.GET['pk'])
            app = Communications.objects.get(pk=pk)
            serializer = CommunicationsSerializer(app)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self, request, pk, format=None):
        try:
            app = Communications.objects.get(pk=pk)
            return app
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class Communications_List(APIView):
    def get(self, request, format=None):
        list = Communications.objects.all()[:10]
        serializer = CommunicationsSerializer(list, many=True)
        return Response(serializer.data)

    def get_list(self):
        querySet = Communications.objects.values()
        return querySet