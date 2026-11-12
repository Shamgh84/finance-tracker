from django.conf import settings
from django.db import models
from django.db.models import Q


class Category(models.Model):
    class Type(models.TextChoices):
        INCOME = 'income', 'درآمد'
        EXPENSE = 'expense', 'هزینه'

    # user = None یعنی دسته پیش‌فرض سیستم که برای همه کاربران نمایش داده می‌شود
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)
    color = models.CharField(max_length=7, default='#6c757d')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'type'],
                name='unique_category_per_user',
            ),
            models.UniqueConstraint(
                fields=['name', 'type'],
                condition=Q(user__isnull=True),
                name='unique_default_category',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'