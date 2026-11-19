from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals',
    )
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return self.name


class GoalContribution(models.Model):
    """واریز (مبلغ مثبت) یا برداشت (مبلغ منفی) از یک هدف پس‌انداز."""

    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='contributions',
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.goal.name}: {self.amount}'