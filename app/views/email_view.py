from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from uwpath_backend import settings



class email_API(APIView):
    def post(self, request, format=None):
        try:
            email = str(request.data['email'])
            name = str(request.data['name'])
            subject = str(request.data['subject'])
            body = str(request.data['message'])

            subject = subject + ' from ' + name + " (" + email + ")"
            msg = EmailMessage(subject,
                               body,
                               settings.EMAIL_HOST_USER,
                               [settings.EMAIL_HOST_USER])
            msg.send()
            return Response(status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
