import re
from mimetypes import guess_type
from urllib.parse import urljoin

from django.core.handlers.wsgi import WSGIRequest
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from .utils import get_field_field, get_all_media, get_model_media, get_model_field_media


@require_GET
def retrieve_all_media_urls(request: WSGIRequest) -> JsonResponse:
    response = get_all_media(request.get_raw_uri())
    return JsonResponse(response, status=200)


@require_GET
def retrieve_model_media_urls(request: WSGIRequest, model_name) -> JsonResponse:
    response = get_model_media(request.get_raw_uri(), model_name)
    return JsonResponse(response, status=200)


@require_GET
def retrieve_model_field_media_urls(request: WSGIRequest, model_name, ff_tag) -> JsonResponse:
    response = get_model_field_media(request.get_raw_uri(), model_name, ff_tag)
    return JsonResponse(response, status=200)


@require_GET
def retrieve_specific_media_url(request: WSGIRequest, model_name, ff_tag, pk) -> JsonResponse:
    file_field = get_field_field(model_name, ff_tag, pk)
    if isinstance(file_field, JsonResponse):
        return file_field
    url = file_field.url
    return JsonResponse(
        {"media_url": urljoin(request.get_raw_uri(), url),
         "rest_url": urljoin(
             request.get_raw_uri(),
             reverse(
                 retrieve_media_file,
                 kwargs=dict(
                         model_name=model_name,
                         ff_tag=ff_tag,
                         pk=pk
                     )
                 )
             )
         }
    )


@require_GET
def retrieve_media_file(request, model_name, ff_tag, pk):
    file_field = get_field_field(model_name, ff_tag, pk)
    if isinstance(file_field, JsonResponse):
        return file_field
    storage = file_field.storage
    if storage.__class__.__name__ == 'SaveLocal':
        file, filename = storage.retrieve(file_field.name)
        return FileResponse(file, filename=filename, content_type=guess_type(filename)[0])
    elif storage.__class__.__name__ == 'SaveS3':
        file_url = storage.retrieve(file_field.name)
        return redirect(file_url)


@require_GET
def download_media_file(request, model_name, ff_tag, pk):
    file_field = get_field_field(model_name, ff_tag, pk)
    if isinstance(file_field, JsonResponse):
        return file_field
    storage = file_field.storage
    if storage.__class__.__name__ == 'SaveLocal':
        file, filename = storage.download(file_field.name)
        return FileResponse(file, filename=filename, content_type=guess_type(filename)[0], as_attachment=True)
    elif storage.__class__.__name__ == 'SaveS3':
        file_url = storage.download(file_field.name)
        return redirect(file_url)


@require_GET
def download_stream(request):
    fs = open('MEDIA/crisis.avi', 'rb')
    content_type = 'application/octet-stream'
    range_header = request.META.get('HTTP_RANGE', None)
    if range_header:
        range_match = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I).match(range_header)
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte)
        length = last_byte - first_byte + 1
        fs.seek(first_byte, 0)
        resp = StreamingHttpResponse(
            iter(fs.read(length-1)), status=206, content_type=content_type)
        resp['Content-Range'] = 'bytes %s-%s' % (first_byte, last_byte)
    else:
        resp = StreamingHttpResponse(fs, content_type=content_type)
    resp['Accept-Ranges'] = 'bytes'
    return resp
