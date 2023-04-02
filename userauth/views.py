from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema

from .serializer import UserSerializer

# Create your views here.

class UserRegistrationAPI(APIView):

    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAdminUser]

    serializer_class = UserSerializer

    @swagger_auto_schema(
        request_body=UserSerializer
    )
    def post(self, request):
        try:
            serializer = self.serializer_class(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "message": "New user created"
            })
        except Exception as e:
            return Response({
                "message": "Uh oh an error occurred"
            })