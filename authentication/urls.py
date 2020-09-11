from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import UserAuth

router = DefaultRouter()
router.register('user', UserAuth, basename="user")

urlpatterns = [
    path('', include(router.urls)),
]