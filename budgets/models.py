from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from categories.models import Category
from config.jalali import jalali_month_range


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    # سال و ماه شمسی
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1300), MaxValueValidator(1600)]
    )
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    # بازه‌ی میلادی همان ماه شمسی (خودکار محاسبه می‌شود)
    start_date = models.DateField(editable=False)
    end_date = models.DateField(editable=False)
    limit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    alert_threshold = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='درصدی از بودجه که با رسیدن به آن هشدار داده می‌شود',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month', 'category__name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'year', 'month'],
                name='unique_budget_per_category_month',
            ),
        ]
        indexes = [models.Index(fields=['user', 'year', 'month'])]

    def save(self, *args, **kwargs):
        self.start_date, self.end_date = jalali_month_range(self.year, self.month)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.category.name} {self.year}/{self.month}: {self.limit_amount}'