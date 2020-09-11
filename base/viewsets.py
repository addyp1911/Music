from django.contrib.auth.hashers import make_password

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.validators import ValidationError

from .permissions import IsOwnerAttributes, IsOwnerAttributes, BaseViewSetPermissionMixin, IsSuperAdminOrStaff

class BaseAPIViewSet(BaseViewSetPermissionMixin, ModelViewSet):
    model_class = None
    serializer_class = None
    instance_name = None

    def list(self, request):
        queryset = self.model_class.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(
            data={
                "status": True,
                "message":
                f"{self.instance_name}s list retrieved sucessfully",
                "data": serializer.data
            })

    def create(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data={
                "status": True,
                "message": f"{self.instance_name} is created sucessfully",
                "data": serializer.data
            },
                            status=status.HTTP_201_CREATED)

        return Response(data={
            "status": False,
            "message": serializer.errors,
            "data": {}
        },
                        status=status.HTTP_400_BAD_REQUEST)
    
    def get_object(self, pk):
        try:
            return self.model_class.objects.get(pk=pk)
        except self.model_class.DoesNotExist:
            raise ValidationError({
                'status': False,
                'message': f"failed to find {self.instance_name}",
                "data": {}
            })

    def retrieve(self, request, pk=None):
        obj = self.get_object(pk)
        serializer = self.serializer_class(obj)
        return Response(
            data={
                "status": True,
                "message": f"{self.instance_name} is retrieved sucessfully",
                "data": serializer.data
            })

    def update(self, request, pk=None):
        if request.data.get("password"):
            request.data["password"] = make_password(request.data.get("password"))
        if not request.data.get("user"):
            request.data["user"] = request.user.uid
        obj = self.get_object(pk)
        serializer = self.serializer_class(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                data={
                    "status": True,
                    "message": f"{self.instance_name} is updated sucessfully",
                    "data": serializer.data
                })
        return Response(data={
            "status": False,
            "message": f"{self.instance_name} update failed",
            "data": serializer.errors
        },
                        status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        obj = self.get_object(pk)
        serializer = self.serializer_class(obj,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                data={
                    "status": True,
                    "message": f"{self.instance_name} is updated sucessfully",
                    "data": serializer.data
                })
        return Response(data={
            "status": False,
            "message": f"{self.instance_name} update failed",
            "data": serializer.errors
        },
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        obj = self.get_object(pk)
        obj.delete()
        return Response(data={
            "status": True,
            "message": f"{self.instance_name} is deleted sucessfully",
            "data": {}
        },
                        status=status.HTTP_200_OK)