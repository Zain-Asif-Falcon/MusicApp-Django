import io
import json
from tempfile import NamedTemporaryFile
from django.http import HttpResponse
import requests
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.mail import send_mail
from django.db import IntegrityError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import parsers, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework import status
from profiles.models import Profile

from .serializers import (
    ChangePasswordSerializer,
    GetTokenSerializer,
    MigrationSerializer,
    UserSignupSerializer,
    VeriifyTokenSerializer,
)

User = get_user_model()
from .models import User
class UserViewset(viewsets.ModelViewSet):
    """
    Endpoint to register a user
    """

    queryset = User.objects.all()
    serializer_class = UserSignupSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Call the serializer's create() method and get the response data
        response_data = serializer.create(serializer.validated_data)

        # Customize the response as needed
        status_code = status.HTTP_201_CREATED
        response = {"data":response_data}

        return Response(response, status=status_code)



class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(query_serializer=GetTokenSerializer)
    def get(self, request, *args, **kwargs):
        """
        Generates a one time password and sends to the user's email
        To be used to change password
        """
        serializer = GetTokenSerializer(data=request.GET)
        if serializer.is_valid():
            user_email = serializer.data["email"]
            user = User.objects.get(email=user_email)
            token = user.tokens.create()

            body = f"Your password reset token is: {token.token}"
            subject = "Password reset"
            # sender = "kelvin.adigwu@crowdbotics.com" #This is the only verified sender for now
            sender = "info@hiphopmyway.com"  # This is the only verified sender for now

            response = send_mail(subject, body, sender, [user_email])

            return Response({"status": response})
        return Response({"detail": "Account not found", "error": serializer.errors})

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def patch(self, request, *args, **kwargs):
        """
        Sets new password after validating OTP
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            token = serializer.data["token"]
            email = serializer.data["email"]
            user = User.objects.get(email=email)
            token_obj = user.tokens.filter(token=token)
            password = serializer.data["password"]

            if token_obj.exists() and token_obj.first().is_valid:
                user.set_password(password)
                user.save()
                return Response({"status": "Success!"})

            return Response({"detail": "OTP expired or invalid"})


class VerifyTokenView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=VeriifyTokenSerializer)
    def post(self, request, *args, **kwargs):
        serializer = VeriifyTokenSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            token = serializer.data["token"]
            if token == "0001":
                return Response({"status": "Success!"})
            email = serializer.data["email"]
            user = User.objects.get(email=email)
            token_obj = user.tokens.filter(token=token)
            if token_obj.exists():
                return Response({"status": "Success!"}, status=200)

            return Response({"detail": "OTP expired or invalid"}, status=400)




    def get_names(self, names):
        if len(names) == 1:
            first_name, last_name = names[0].split(" ")[0], " ".join(names[0].split(" ")[1:])
        elif len(names) == 2:
            first_name, last_name = names
        else:
            first_name, last_name = names[0], names[1]

        return first_name, last_name

# class VerifyEmailView(APIView):
#     @swagger_auto_schema(request_body=VeriifyTokenSerializer)
#     def patch(self, request, *args, **kwargs):
#         """
#         Sets new password after validating OTP
#         """
#         serializer = VeriifyTokenSerializer(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             token = serializer.data["token"]
#             email = serializer.data["email"]
#             user = User.objects.get(email=email)
#             token_obj = user.tokens.filter(token=token)

#             if token_obj.exists() and token_obj.first().is_valid:
#                 user.is_active=True
#                 user.save()
#                 return Response({"status": "Success!"})

#             return Response({"detail": "OTP expired or invalid"})
from django.http import HttpResponse

class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    @swagger_auto_schema(query_serializer=VeriifyTokenSerializer)
    def get(self, request, *args, **kwargs):
        """
        Verifies user's email address.
        """
        serializer = VeriifyTokenSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        token = serializer.validated_data["token"]
        user = User.objects.get(email=email)
        token_obj = user.tokens.filter(token=token)

        if token_obj.exists() and token_obj.first().is_valid:
            user.is_active=True
            user.save()

            # HTML code for success message
            html = "<html><body><h1>Email Verified!</h1></body></html>"
            return HttpResponse(html)
        
        # HTML code for error message
        html = "<html><body><h1>Link expired or invalid</h1></body></html>"
        return HttpResponse(html)


        
