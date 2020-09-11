from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import *

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

    def validate_password(self, password) -> str:
        """ A function to save the password for storing the values """
        return make_password(password)


class UserShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uid', 'user_name', 'email']