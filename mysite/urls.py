"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from userauth.views import UserRegistrationAPI
from upsheershak.views import AudioUploadAPI, TranscriptionAPI, TranscriptionStatusAPI, FileDetailsAPI, TranscriptionResultAPI

schema_view = get_schema_view(
   openapi.Info(
      title="Upsheershak API",
      default_version='v1',
      description="A subtitle generation service",
      terms_of_service="",
      contact=openapi.Contact(email="dewanshrawat15@gmail.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=[permissions.IsAuthenticated],
)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/user/', UserRegistrationAPI.as_view(), name='user_auth'),
    path('api/file/upload/', AudioUploadAPI.as_view(), name='subtitling'),
    path('api/file/transcribe/', TranscriptionAPI.as_view(), name='transcription'),
    path('api/file/status/', TranscriptionStatusAPI.as_view(), name='transcription_status'),
    path('api/file/details/', FileDetailsAPI.as_view(), name='transcription_details'),
    path('api/file/results/', TranscriptionResultAPI.as_view(), name='transcription_results')
]
