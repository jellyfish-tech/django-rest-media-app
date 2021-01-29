from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from .models import Media


def retrieve_media_url(request: WSGIRequest, file_pk: str) -> JsonResponse:
    return JsonResponse(
        {"media_url": Media.objects.get_media_url_or_none(file_pk)}
    )
