from django.db.models import ProtectedError, Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category
from .permissions import IsOwnerOrReadOnlyDefault
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnlyDefault]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Category.objects.none()
        user = self.request.user
        return Category.objects.filter(Q(user=user) | Q(user__isnull=True))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'این دسته تراکنش دارد و قابل حذف نیست.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
