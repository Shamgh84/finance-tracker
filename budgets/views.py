from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Budget
from .serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'month', 'category']

    def get_queryset(self):
        queryset = Budget.objects.filter(
            user=self.request.user
        ).select_related('category')
        return services.annotate_spent(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """بودجه‌های ماه جاری که به سقف نزدیک شده‌اند یا از آن گذشته‌اند."""
        today = timezone.localdate()
        queryset = self.get_queryset().filter(year=today.year, month=today.month)
        data = self.get_serializer(queryset, many=True).data
        return Response([item for item in data if item['status'] != 'ok'])