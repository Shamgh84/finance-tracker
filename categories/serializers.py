from django.db.models import Q
from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'type', 'color', 'is_default')
        read_only_fields = ('id', 'is_default')

    def get_is_default(self, obj):
        return obj.user_id is None

    def validate(self, attrs):
        user = self.context['request'].user
        name = attrs.get('name', getattr(self.instance, 'name', None))
        type_ = attrs.get('type', getattr(self.instance, 'type', None))

        duplicates = Category.objects.filter(name=name, type=type_).filter(
            Q(user=user) | Q(user__isnull=True)
        )
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError('این دسته قبلاً وجود دارد.')

        if (
            self.instance
            and type_ != self.instance.type
            and self.instance.transactions.exists()
        ):
            raise serializers.ValidationError(
                'نوع دسته‌ای که تراکنش دارد قابل تغییر نیست.'
            )
        return attrs