from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from transactions.models import Transaction

MONEY = DecimalField(max_digits=15, decimal_places=2)


def calculate_status(spent, limit, threshold):
    """وضعیت مصرف بودجه را برمی‌گرداند (بدون نیاز به دیتابیس، پس راحت تست می‌شود)."""
    spent = Decimal(spent)
    limit = Decimal(limit)
    percent = (spent / limit * 100).quantize(Decimal('0.1')) if limit > 0 else Decimal('0')

    if spent > limit:
        status = 'exceeded'
        message = 'از سقف بودجه عبور کرده‌اید.'
    elif percent >= threshold:
        status = 'warning'
        message = f'{percent}٪ از بودجه مصرف شده و به سقف نزدیک شده‌اید.'
    else:
        status = 'ok'
        message = 'مصرف بودجه در محدوده‌ی مجاز است.'

    return {
        'spent': spent,
        'remaining': limit - spent,
        'percent_used': percent,
        'status': status,
        'message': message,
    }


def get_spent(budget):
    """مجموع هزینه‌ی یک بودجه (برای وقتی که queryset محاسبه‌شده نداریم)."""
    total = Transaction.objects.filter(
        user=budget.user,
        category=budget.category,
        date__year=budget.year,
        date__month=budget.month,
    ).aggregate(total=Sum('amount'))['total']
    return total or Decimal('0')


def annotate_spent(queryset):
    """مصرف هر بودجه را با یک کوئری برای همه محاسبه می‌کند (جلوگیری از N+1)."""
    spent_subquery = (
        Transaction.objects.filter(
            user=OuterRef('user'),
            category=OuterRef('category'),
            date__year=OuterRef('year'),
            date__month=OuterRef('month'),
        )
        .order_by()
        .values('user')
        .annotate(total=Sum('amount'))
        .values('total')
    )
    return queryset.annotate(
        spent=Coalesce(
            Subquery(spent_subquery, output_field=MONEY),
            Value(Decimal('0'), output_field=MONEY),
        )
    )