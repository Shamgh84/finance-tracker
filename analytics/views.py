from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    CategoryBreakdownQuerySerializer,
    DateRangeSerializer,
    TrendQuerySerializer,
)


def resolve_range(params):
    """اگر بازه‌ای داده نشده باشد، ماه جاری را برمی‌گرداند."""
    date_from = params.get('date_from')
    date_to = params.get('date_to')
    if date_from is None and date_to is None:
        today = timezone.localdate()
        date_from, date_to = services.month_range(today.year, today.month)
    return date_from, date_to


class SummaryView(APIView):
    def get(self, request):
        query = DateRangeSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date_from, date_to = resolve_range(query.validated_data)
        return Response(services.get_summary(request.user, date_from, date_to))


class CategoryBreakdownView(APIView):
    def get(self, request):
        query = CategoryBreakdownQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date_from, date_to = resolve_range(query.validated_data)
        return Response(
            services.get_category_breakdown(
                request.user, query.validated_data['type'], date_from, date_to
            )
        )


class TrendView(APIView):
    def get(self, request):
        query = TrendQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(
            services.get_monthly_trend(
                request.user,
                query.validated_data['months'],
                timezone.localdate(),
            )
        )