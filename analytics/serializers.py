from rest_framework import serializers


class DateRangeSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError('date_from نباید بعد از date_to باشد.')
        return attrs


class CategoryBreakdownQuerySerializer(DateRangeSerializer):
    type = serializers.ChoiceField(choices=['income', 'expense'], default='expense')


class TrendQuerySerializer(serializers.Serializer):
    months = serializers.IntegerField(min_value=1, max_value=24, default=6)

class MonthQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)

    def validate(self, attrs):
        if ('year' in attrs) != ('month' in attrs):
            raise serializers.ValidationError('year و month باید با هم ارسال شوند.')
        return attrs