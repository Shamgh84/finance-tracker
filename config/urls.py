from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/budgets/', include('budgets.urls')),
    path('api/analytics/', include('analytics.urls')),
    # مستندات API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # صفحه‌های فرانت‌اند
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard-page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register-page'),
    path('transactions/', TemplateView.as_view(template_name='transactions.html'), name='transactions-page'),
    path('budgets/', TemplateView.as_view(template_name='budgets.html'), name='budgets-page'),
    path('analysis/', TemplateView.as_view(template_name='analysis.html'), name='analysis-page'),
]