from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum

from budgets.models import Budget
from budgets.services import annotate_spent
from config.jalali import (
    current_jalali_month,
    jalali_month_range,
    shift_month,
    to_jalali,
)
from transactions.models import Transaction

ZERO = Decimal('0')
INCOME = Q(category__type='income')
EXPENSE = Q(category__type='expense')


def month_range(year, month):
    """بازه‌ی میلادی یک ماه شمسی."""
    return jalali_month_range(year, month)


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
    """درآمد و هزینه‌ی چند ماه شمسی اخیر؛ ماه‌های بدون تراکنش با صفر پر می‌شوند."""
    end_year, end_month = current_jalali_month(today)
    start_year, start_month = shift_month(end_year, end_month, -(months - 1))
    start, _last = month_range(start_year, start_month)

    # ابتدا به تفکیک روز جمع می‌زنیم و بعد در پایتون به ماه شمسی تبدیل می‌کنیم
    rows = (
        Transaction.objects.filter(user=user, date__gte=start)
        .values('date')
        .annotate(
            income=Sum('amount', filter=INCOME),
            expense=Sum('amount', filter=EXPENSE),
        )
        .order_by()
    )
    buckets = {}
    for row in rows:
        row_year, row_month, _day = to_jalali(row['date'])
        bucket = buckets.setdefault((row_year, row_month), [ZERO, ZERO])
        bucket[0] += row['income'] or ZERO
        bucket[1] += row['expense'] or ZERO

    result = []
    for i in range(months):
        year, month = shift_month(start_year, start_month, i)
        income, expense = buckets.get((year, month), (ZERO, ZERO))
        date_from, date_to = month_range(year, month)
        result.append({
            'month': f'{year}-{month:02d}',
            'date_from': date_from,
            'date_to': date_to,
            'income': income,
            'expense': expense,
            'net': income - expense,
        })
    return result


# ----------------------------------------------------------------------
# تحلیل مالی: مقایسه‌ی ماه‌ها، پیش‌بینی، امتیاز سلامت مالی و گزارش
# ----------------------------------------------------------------------

def get_expense_by_category(user, year, month, day_limit=None):
    """هزینه‌ی هر دسته در یک ماه شمسی؛ با day_limit فقط تا آن روز از ماه حساب می‌شود."""
    start, end = month_range(year, month)
    if day_limit:
        length = (end - start).days + 1
        end = start + timedelta(days=min(day_limit, length) - 1)
    rows = (
        Transaction.objects.filter(
            user=user, category__type='expense', date__gte=start, date__lte=end
        )
        .values('category_id', 'category__name')
        .annotate(total=Sum('amount'))
        .order_by()
    )
    return {
        row['category_id']: {'name': row['category__name'], 'total': row['total']}
        for row in rows
    }


def calc_change(current, previous):
    """تغییر بین دو مقدار را برمی‌گرداند (تابع خالص، بدون دیتابیس)."""
    current = Decimal(current)
    previous = Decimal(previous)
    change = current - previous
    percent = None
    if previous > 0:
        percent = (change / previous * 100).quantize(Decimal('0.1'))

    if current == previous:
        trend = 'same'
    elif previous == 0:
        trend = 'new'
    elif change > 0:
        trend = 'up'
    else:
        trend = 'down'
    return {'change': change, 'change_percent': percent, 'trend': trend}


def _sum_totals(by_category):
    return sum((item['total'] for item in by_category.values()), ZERO)


def get_month_comparison(user, year, month, today):
    """year و month شمسی‌اند و today تاریخ میلادی امروز است."""
    prev_year, prev_month = shift_month(year, month, -1)
    today_year, today_month, today_day = to_jalali(today)
    is_current = (year, month) == (today_year, today_month)
    day_limit = today_day if is_current else None

    current = get_expense_by_category(user, year, month, day_limit)
    previous = get_expense_by_category(user, prev_year, prev_month, day_limit)

    categories = []
    for category_id in current.keys() | previous.keys():
        info = current.get(category_id) or previous.get(category_id)
        cur_total = current[category_id]['total'] if category_id in current else ZERO
        prev_total = previous[category_id]['total'] if category_id in previous else ZERO
        categories.append({
            'category_id': category_id,
            'category_name': info['name'],
            'current': cur_total,
            'previous': prev_total,
            **calc_change(cur_total, prev_total),
        })
    categories.sort(key=lambda item: abs(item['change']), reverse=True)

    current_expense = _sum_totals(current)
    previous_expense = _sum_totals(previous)
    start, end = month_range(year, month)
    prev_start, prev_end = month_range(prev_year, prev_month)
    return {
        'month': f'{year}-{month:02d}',
        'previous_month': f'{prev_year}-{prev_month:02d}',
        'date_from': start,
        'date_to': end,
        'previous_date_from': prev_start,
        'previous_date_to': prev_end,
        'compared_through_day': day_limit,
        'current_expense': current_expense,
        'previous_expense': previous_expense,
        **calc_change(current_expense, previous_expense),
        'categories': categories,
    }


def project_month_end(spent, elapsed_days, days_in_month):
    spent = Decimal(spent)
    if elapsed_days <= 0:
        return spent
    return (spent / elapsed_days * days_in_month).quantize(Decimal('0.01'))


def get_forecast(user, today):
    year, month, day = to_jalali(today)
    start, end = month_range(year, month)
    days_in_month = (end - start).days + 1
    spent = (
        Transaction.objects.filter(
            user=user, category__type='expense', date__gte=start, date__lte=today
        ).aggregate(total=Sum('amount'))['total']
        or ZERO
    )
    prev_year, prev_month = shift_month(year, month, -1)
    previous_expense = _sum_totals(get_expense_by_category(user, prev_year, prev_month))
    return {
        'month': f'{year}-{month:02d}',
        'date_from': start,
        'date_to': end,
        'days_elapsed': day,
        'days_in_month': days_in_month,
        'spent_so_far': spent,
        'daily_average': (spent / day).quantize(Decimal('0.01')),
        'projected_expense': project_month_end(spent, day, days_in_month),
        'previous_month_expense': previous_expense,
    }


def _clamp(value, low, high):
    return max(low, min(high, value))


def calculate_health_score(
    income, expense, projected_expense, avg_previous_expense,
    budget_count, budgets_exceeded,
):
    """امتیاز سلامت مالی (۰ تا ۱۰۰) از سه بخش؛ تابع خالص و راحت برای تست."""
    income = Decimal(income)
    expense = Decimal(expense)
    projected_expense = Decimal(projected_expense)
    avg_previous_expense = Decimal(avg_previous_expense)
    zero, one = Decimal('0'), Decimal('1')

    # ۱) پس‌انداز (۵۰ امتیاز): نرخ پس‌انداز ۲۰٪ یا بیشتر = امتیاز کامل
    if income > 0:
        savings_rate = (income - expense) / income
        savings_points = _clamp(savings_rate / Decimal('0.2'), zero, one) * 50
    else:
        savings_rate = None
        savings_points = zero

    # ۲) رعایت بودجه (۳۰ امتیاز): بدون بودجه، امتیاز خنثی
    if budget_count > 0:
        budget_points = Decimal(budget_count - budgets_exceeded) / budget_count * 30
    else:
        budget_points = Decimal('15')

    # ۳) ثبات هزینه (۲۰ امتیاز): پیش‌بینی ماه در برابر میانگین ماه‌های قبل
    if avg_previous_expense > 0:
        ratio = projected_expense / avg_previous_expense
        stability_points = _clamp(
            (Decimal('1.5') - ratio) / Decimal('0.5'), zero, one
        ) * 20
    else:
        stability_points = Decimal('10')

    score = int(round(savings_points + budget_points + stability_points))
    if score >= 80:
        level, label = 'excellent', 'عالی'
    elif score >= 60:
        level, label = 'good', 'خوب'
    elif score >= 40:
        level, label = 'fair', 'متوسط'
    else:
        level, label = 'poor', 'ضعیف'

    tenth = Decimal('0.1')
    return {
        'score': score,
        'level': level,
        'level_label': label,
        'savings_rate_percent': (
            (savings_rate * 100).quantize(tenth) if savings_rate is not None else None
        ),
        'components': {
            'savings': {'points': savings_points.quantize(tenth), 'max': 50},
            'budget': {'points': budget_points.quantize(tenth), 'max': 30},
            'stability': {'points': stability_points.quantize(tenth), 'max': 20},
        },
    }


def get_health_score(user, today):
    year, month, _day = to_jalali(today)
    start, _end = month_range(year, month)
    income, expense = _income_expense(
        Transaction.objects.filter(user=user, date__gte=start, date__lte=today)
    )
    forecast = get_forecast(user, today)

    # میانگین هزینه‌ی ۳ ماه شمسی قبل (فقط ماه‌هایی که تراکنش داشته‌اند)
    previous_totals = []
    for i in range(1, 4):
        prev_year, prev_month = shift_month(year, month, -i)
        total = _sum_totals(get_expense_by_category(user, prev_year, prev_month))
        if total > 0:
            previous_totals.append(total)
    average = sum(previous_totals, ZERO) / len(previous_totals) if previous_totals else ZERO

    budgets = annotate_spent(
        Budget.objects.filter(user=user, year=year, month=month)
    )
    budget_count = 0
    exceeded = 0
    for budget in budgets:
        budget_count += 1
        if budget.spent > budget.limit_amount:
            exceeded += 1

    result = calculate_health_score(
        income, expense, forecast['projected_expense'], average,
        budget_count, exceeded,
    )
    result['month'] = f'{year}-{month:02d}'
    result['income'] = income
    result['expense'] = expense
    result['budgets'] = {'count': budget_count, 'exceeded': exceeded}
    return result


def _fmt(value):
    return f'{Decimal(value):,.0f}'


def build_insights(comparison, forecast, health):
    """جمله‌های تحلیلی فارسی برای گزارش (تابع خالص)."""
    if (
        health['income'] == 0
        and health['expense'] == 0
        and comparison['previous_expense'] == 0
    ):
        return ['هنوز تراکنشی برای تحلیل ثبت نشده است. با ثبت درآمد و هزینه، گزارش شما ساخته می‌شود.']

    insights = []

    percent = comparison['change_percent']
    if percent is not None and comparison['trend'] in ('up', 'down'):
        word = 'افزایش' if comparison['trend'] == 'up' else 'کاهش'
        insights.append(
            f'مجموع هزینه‌ها نسبت به ماه قبل (در همین بازه‌ی روزها) {abs(percent)}٪ {word} داشته است.'
        )

    rising = [
        c for c in comparison['categories']
        if c['trend'] == 'up' and c['change_percent'] is not None
    ]
    if rising:
        top = max(rising, key=lambda c: c['change'])
        insights.append(
            f'بیشترین افزایش هزینه در دسته‌ی «{top["category_name"]}» بوده ({top["change_percent"]}٪ بیشتر از ماه قبل).'
        )

    falling = [
        c for c in comparison['categories']
        if c['trend'] == 'down' and c['change_percent'] is not None
    ]
    if falling:
        top = min(falling, key=lambda c: c['change'])
        insights.append(
            f'بیشترین کاهش هزینه در دسته‌ی «{top["category_name"]}» بوده ({abs(top["change_percent"])}٪ کمتر از ماه قبل).'
        )

    if forecast['spent_so_far'] > 0 and forecast['previous_month_expense'] > 0:
        projected = forecast['projected_expense']
        previous = forecast['previous_month_expense']
        compare = 'بیشتر' if projected > previous else 'کمتر'
        insights.append(
            f'با روند فعلی، هزینه‌ی پایان ماه حدود {_fmt(projected)} می‌شود که از کل هزینه‌ی ماه قبل ({_fmt(previous)}) {compare} است.'
        )

    budgets = health['budgets']
    if budgets['exceeded'] > 0:
        insights.append(f'در {budgets["exceeded"]} دسته از بودجه‌ی تعیین‌شده عبور کرده‌اید.')
    elif budgets['count'] > 0:
        insights.append('در هیچ دسته‌ای از بودجه‌ی تعیین‌شده عبور نکرده‌اید.')

    rate = health['savings_rate_percent']
    if rate is not None:
        if rate < 0:
            insights.append('هزینه‌های این ماه تا الان از درآمدها بیشتر شده است.')
        elif rate >= 20:
            insights.append(f'نرخ پس‌انداز این ماه {rate}٪ است که وضعیت خوبی است.')
        else:
            insights.append(f'نرخ پس‌انداز این ماه {rate}٪ است؛ هدف مناسب حدود ۲۰٪ است.')

    insights.append(
        f'امتیاز سلامت مالی شما {health["score"]} از ۱۰۰ ({health["level_label"]}) است.'
    )
    return insights