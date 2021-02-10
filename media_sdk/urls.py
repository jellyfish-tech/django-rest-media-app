from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (download_media_file, retrieve_media_file,
                    retrieve_all_media_urls, retrieve_model_media_urls,
                    retrieve_model_field_media_urls, retrieve_specific_media_url)

urlpatterns = [
    path("media-url/", retrieve_all_media_urls),
    path("media-url/<str:model_name>/", retrieve_model_media_urls),
    path("media-url/<str:model_name>/<str:ff_tag>/", retrieve_model_field_media_urls),
    path("media-url/<str:model_name>/<str:ff_tag>/<int:pk>/", retrieve_specific_media_url),
    path("retrieve/<str:model_name>/<str:ff_tag>/<int:pk>/", retrieve_media_file),
    path("download/<str:model_name>/<str:ff_tag>/<int:pk>/", download_media_file),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
