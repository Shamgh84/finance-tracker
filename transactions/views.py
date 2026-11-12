import csv

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination

from .filters import TransactionFilter
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def csv_safe(value):
    """جلوگیری از اجرای فرمول در Excel (CSV injection)."""
    value = '' if value is None else str(value)
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'category__name']
    ordering_fields = ['date', 'amount', 'created_at']

    def get_queryset(self):
        # هر کاربر فقط تراکنش‌های خودش را می‌بیند
        return Transaction.objects.filter(
            user=self.request.user
        ).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary='خروجی CSV از تراکنش‌ها (با همان فیلترهای لیست)',
        filters=True,
        responses={200: OpenApiTypes.BINARY},
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        response.write('\ufeff')  # برای اینکه Excel فارسی را درست نشان بدهد

        writer = csv.writer(response)
        writer.writerow(['date', 'type', 'category', 'amount', 'description'])
        for item in queryset:
            writer.writerow([
                item.date.isoformat(),
                item.category.type,
                csv_safe(item.category.name),
                item.amount,
                csv_safe(item.description),
            ])
        return response