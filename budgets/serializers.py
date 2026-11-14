from rest_framework import serializers
from config.jalali import month_label

from categories.models import Category
from . import services
from .models import Budget

class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    period_label = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = (
            'id', 'category', 'category_name', 'year', 'month', 'period_label',
            'start_date', 'end_date', 'limit_amount', 'alert_threshold',
        )
        read_only_fields = ('id', 'start_date', 'end_date')

    def get_period_label(self, obj)  -> str:
        return month_label(obj.year, obj.month)

    def validate_category(self, category):
        user = self.context['request'].user
        if category.user_id not in (None, user.id):
            raise serializers.ValidationError('دسته‌ی نامعتبر است.')
        if category.type != Category.Type.EXPENSE:
            raise serializers.ValidationError('بودجه فقط برای دسته‌های هزینه تعریف می‌شود.')
        return category

    def validate(self, attrs):
        user = self.context['request'].user

        def get(key):
            return attrs.get(key, getattr(self.instance, key, None))

        duplicates = Budget.objects.filter(
            user=user,
            category=get('category'),
            year=get('year'),
            month=get('month'),
        )
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                'برای این دسته در این ماه قبلاً بودجه تعریف شده است.'
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        spent = getattr(instance, 'spent', None)
        if spent is None:
            spent = services.get_spent(instance)
        data.update(
            services.calculate_status(
                spent, instance.limit_amount, instance.alert_threshold
            )
        )
        return data