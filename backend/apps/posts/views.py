"""기록 API (API 명세서 4.3). 지금은 이미지 올리기와 골목 목록만 있다."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsMember

from .images import image_payload, save_upload
from .models import Topic


class ImageUploadView(APIView):
    """POST /api/images — 이미지 올리기 (multipart/form-data, 필드 file)."""

    permission_classes = [IsMember]

    def post(self, request):
        image = save_upload(request.FILES.get("file"), request.user)
        return Response(image_payload(image, request), status=status.HTTP_201_CREATED)


class TopicListView(APIView):
    """GET /api/topics — 골목 10개."""

    def get(self, request):
        return Response([{"slug": t.slug, "name": t.name} for t in Topic.objects.all()])
