from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from config.jalali import current_jalali_month
from . import services
from .models import Budget
from .serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'month', 'category']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Budget.objects.none()
        queryset = Budget.objects.filter(
            user=self.request.user
        ).select_related('category')
        return services.annotate_spent(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """بودجه‌های ماه شمسی جاری که به سقف نزدیک شده‌اند یا از آن گذشته‌اند."""
        year, month = current_jalali_month(timezone.localdate())
        queryset = self.get_queryset().filter(year=year, month=month)
        data = self.get_serializer(queryset, many=True).data
        return Response([item for item in data if item['status'] != 'ok'])