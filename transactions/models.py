from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from categories.models import Category


class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions',
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f'{self.category.name}: {self.amount} ({self.date})'