import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth

from transactions.models import Transaction

ZERO = Decimal('0')
INCOME = Q(category__type='income')
EXPENSE = Q(category__type='expense')


def month_range(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def shift_month(year, month, delta):
    """سال و ماه را به اندازه‌ی delta ماه جابه‌جا می‌کند (delta می‌تواند منفی باشد)."""
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _filter_dates(queryset, date_from, date_to):
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    return queryset


def _income_expense(queryset):
    totals = queryset.aggregate(
        income=Sum('amount', filter=INCOME),
        expense=Sum('amount', filter=EXPENSE),
    )
    return totals['income'] or ZERO, totals['expense'] or ZERO


def get_summary(user, date_from, date_to):
    base = Transaction.objects.filter(user=user)
    total_income, total_expense = _income_expense(base)
    period_income, period_expense = _income_expense(
        _filter_dates(base, date_from, date_to)
    )
    return {
        'period': {'date_from': date_from, 'date_to': date_to},
        'period_income': period_income,
        'period_expense': period_expense,
        'period_net': period_income - period_expense,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
    }


def get_category_breakdown(user, type_, date_from, date_to):
    queryset = _filter_dates(
        Transaction.objects.filter(user=user, category__type=type_),
        date_from,
        date_to,
    )
    rows = list(
        queryset.values('category_id', 'category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    grand_total = sum((row['total'] for row in rows), ZERO)

    categories = []
    for row in rows:
        percent = ZERO
        if grand_total > 0:
            percent = (row['total'] / grand_total * 100).quantize(Decimal('0.1'))
        categories.append({
            'category_id': row['category_id'],
            'category_name': row['category__name'],
            'color': row['category__color'],
            'total': row['total'],
            'percent': percent,
        })
    return {
        'type': type_,
        'date_from': date_from,
        'date_to': date_to,
        'total': grand_total,
        'categories': categories,
    }


def get_monthly_trend(user, months, today):
    """درآمد و هزینه‌ی چند ماه اخیر؛ ماه‌های بدون تراکنش با صفر پر می‌شوند."""
    start_year, start_month = shift_month(today.year, today.month, -(months - 1))
    start = date(start_year, start_month, 1)

    rows = (
        Transaction.objects.filter(user=user, date__gte=start)
        .annotate(m=TruncMonth('date'))
        .values('m')
        .annotate(
            income=Sum('amount', filter=INCOME),
            expense=Sum('amount', filter=EXPENSE),
        )
        .order_by('m')
    )
    by_month = {(row['m'].year, row['m'].month): row for row in rows}

    result = []
    for i in range(months):
        year, month = shift_month(start_year, start_month, i)
        row = by_month.get((year, month))
        income = (row['income'] if row else None) or ZERO
        expense = (row['expense'] if row else None) or ZERO
        result.append({
            'month': f'{year}-{month:02d}',
            'income': income,
            'expense': expense,
            'net': income - expense,
        })
    return result