from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'category', 'category_name', 'category_type',
            'amount', 'date', 'description', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_category(self, category):
        user = self.context['request'].user
        # فقط دسته‌های پیش‌فرض یا دسته‌های شخصی خود کاربر مجازند
        if category.user_id not in (None, user.id):
            raise serializers.ValidationError('دسته‌ی نامعتبر است.')
        return category