from datetime import timedelta

import jdatetime

JALALI_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]


def to_jalali(value):
    """تاریخ میلادی را به (سال، ماه، روز) شمسی تبدیل می‌کند."""
    j = jdatetime.date.fromgregorian(date=value)
    return j.year, j.month, j.day


def from_jalali(year, month, day):
    """تاریخ شمسی را به تاریخ میلادی (datetime.date) تبدیل می‌کند."""
    return jdatetime.date(year, month, day).togregorian()


def jalali_month_range(year, month):
    """اولین و آخرین روز یک ماه شمسی، به صورت تاریخ میلادی."""
    start = from_jalali(year, month, 1)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)
    end = from_jalali(next_year, next_month, 1) - timedelta(days=1)
    return start, end


def shift_month(year, month, delta):
    """سال و ماه را به اندازه‌ی delta ماه جابه‌جا می‌کند (delta می‌تواند منفی باشد)."""
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def current_jalali_month(today):
    year, month, _ = to_jalali(today)
    return year, month


def month_label(year, month):
    return f'{JALALI_MONTHS[month - 1]} {year}'