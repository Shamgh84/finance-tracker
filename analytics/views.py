from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    CategoryBreakdownQuerySerializer,
    DateRangeSerializer,
    MonthQuerySerializer,
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


class ComparisonView(APIView):
    def get(self, request):
        query = MonthQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        today = timezone.localdate()
        year = query.validated_data.get('year', today.year)
        month = query.validated_data.get('month', today.month)
        return Response(
            services.get_month_comparison(request.user, year, month, today)
        )


class ForecastView(APIView):
    def get(self, request):
        return Response(services.get_forecast(request.user, timezone.localdate()))


class HealthScoreView(APIView):
    def get(self, request):
        return Response(services.get_health_score(request.user, timezone.localdate()))


class ReportView(APIView):
    def get(self, request):
        today = timezone.localdate()
        comparison = services.get_month_comparison(
            request.user, today.year, today.month, today
        )
        forecast = services.get_forecast(request.user, today)
        health = services.get_health_score(request.user, today)
        return Response({
            'month': f'{today.year}-{today.month:02d}',
            'insights': services.build_insights(comparison, forecast, health),
            'health_score': health,
            'forecast': forecast,
            'comparison': comparison,
        })