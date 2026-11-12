from django.urls import path

from .views import CategoryBreakdownView, SummaryView, TrendView

urlpatterns = [
    path('summary/', SummaryView.as_view(), name='analytics-summary'),
    path('by-category/', CategoryBreakdownView.as_view(), name='analytics-by-category'),
    path('trend/', TrendView.as_view(), name='analytics-trend'),
]