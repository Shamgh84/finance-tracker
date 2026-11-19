from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

MONEY = DecimalField(max_digits=15, decimal_places=2)
ZERO = Decimal('0')


def annotate_saved(queryset):
    """مجموع واریزها منهای برداشت‌های هر هدف را با یک کوئری برای همه محاسبه می‌کند."""
    return queryset.annotate(
        saved=Coalesce(
            Sum('contributions__amount'),
            Value(ZERO, output_field=MONEY),
            output_field=MONEY,
        )
    )


def get_saved(goal):
    total = goal.contributions.aggregate(total=Sum('amount'))['total']
    return total or ZERO


def calculate_progress(saved, target, deadline, today):
    """پیشرفت یک هدف را حساب می‌کند (تابع خالص، بدون دیتابیس)."""
    saved = Decimal(saved)
    target = Decimal(target)
    percent = (saved / target * 100).quantize(Decimal('0.1')) if target > 0 else ZERO
    remaining = max(target - saved, ZERO)
    days_left = (deadline - today).days if deadline else None

    if saved >= target:
        status = 'done'
    elif days_left is not None and days_left < 0:
        status = 'overdue'
    else:
        status = 'active'

    # برای رسیدن به هدف تا مهلت، ماهانه چقدر باید پس‌انداز شود (حداقل یک ماه حساب می‌شود)
    monthly_needed = None
    if status == 'active' and days_left is not None:
        months = max(Decimal(days_left) / Decimal(30), Decimal(1))
        monthly_needed = (remaining / months).quantize(Decimal('0.01'))

    return {
        'saved': saved,
        'percent': percent,
        'remaining': remaining,
        'status': status,
        'days_left': days_left,
        'monthly_needed': monthly_needed,
    }