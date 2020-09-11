from django.shortcuts import render

# Create your views here.
#django imports
from django.shortcuts import render
from .constants import *
import datetime
from random import randint

#rest_framework imports
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

#project imports
from base.utils import responsedata
from base.viewsets import BaseAPIViewSet
from .models import *
from .serializers import *


class UserAuth(BaseAPIViewSet):
    model_class = User
    serializer_class = UserSerializer
    instance_name = "user"
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        data = request.data
        if User.objects.filter(user_name=data.get("user_name")).values().exists():
            return Response(responsedata(False, USERNAME_TAKEN), status=status.HTTP_409_CONFLICT)
        
        elif User.objects.filter(email=data.get("email")).values().exists():
            return Response(responsedata(False, MAIL_EXISTS), status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                res_data = User.objects.filter(uid=user.uid).values("first_name", "last_name", "uid", "user_name", "email").first()
                return Response(responsedata(True, f"{self.instance_name} created successfully", res_data),
                                status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(responsedata(False, GENERIC_ERR), status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def login(self, request):
        if User.objects.filter(email=request.data.get('email')).exists():
            user = User.objects.get(email=request.data.get('email'))

            if not user.check_password(request.data.get('password')):
                return Response(responsedata(False, PASSWORD_ERR), status=status.HTTP_401_UNAUTHORIZED)

            if user.is_active:
                token = RefreshToken.for_user(user)
                user.last_login = datetime.datetime.now()
                user.save()
                data = dict(user=user.first_name + ' ' + user.last_name, 
                            accessToken=str(token.access_token),
                            email=user.email,
                            uid=user.uid)

                return Response(responsedata(True, LOGIN_SUCCESS, data),
                                headers={"accessToken": str(token.access_token)}, status=status.HTTP_200_OK)

            elif not user.is_active:
                return Response(responsedata(True, DEACTIVATED_ERR),
                                status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(responsedata(False, USER_NOT_FOUND), status=status.HTTP_400_BAD_REQUEST)


