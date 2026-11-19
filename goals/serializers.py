from django.utils import timezone
from rest_framework import serializers

from . import services
from .models import Goal


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ('id', 'name', 'target_amount', 'deadline')
        read_only_fields = ('id',)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('نام هدف نمی‌تواند خالی باشد.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        saved = getattr(instance, 'saved', None)
        if saved is None:
            saved = services.get_saved(instance)
        data.update(
            services.calculate_progress(
                saved, instance.target_amount, instance.deadline, timezone.localdate()
            )
        )
        return data


class ContributionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError('مبلغ نمی‌تواند صفر باشد.')
        return value