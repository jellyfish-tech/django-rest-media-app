from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from .views import retrieve_media_url


urlpatterns = [path("media/<str:file_pk>/", retrieve_media_url)]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
