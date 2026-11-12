from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/budgets/', include('budgets.urls')),
    path('api/analytics/', include('analytics.urls')),
    # صفحه‌های فرانت‌اند
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard-page'),
    path('transactions/', TemplateView.as_view(template_name='transactions.html'), name='transactions-page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register-page'),
]