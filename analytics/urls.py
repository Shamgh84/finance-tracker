from django.urls import path

from .views import (
    CategoryBreakdownView,
    ComparisonView,
    ForecastView,
    HealthScoreView,
    ReportView,
    SummaryView,
    TrendView,
)

urlpatterns = [
    path('summary/', SummaryView.as_view(), name='analytics-summary'),
    path('by-category/', CategoryBreakdownView.as_view(), name='analytics-by-category'),
    path('trend/', TrendView.as_view(), name='analytics-trend'),
    path('comparison/', ComparisonView.as_view(), name='analytics-comparison'),
    path('forecast/', ForecastView.as_view(), name='analytics-forecast'),
    path('health-score/', HealthScoreView.as_view(), name='analytics-health-score'),
    path('report/', ReportView.as_view(), name='analytics-report'),
]