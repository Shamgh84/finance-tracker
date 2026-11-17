import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from config.jalali import (
    current_jalali_month,
    jalali_month_range,
    month_label,
    shift_month,
)
from transactions.models import Transaction

DEMO_USERNAME = 'demo'
DEMO_EMAIL = 'demo@example.com'
DEMO_PASSWORD = 'Demo@12345'

CATEGORY_NAMES = {
    'food': 'خوراک',
    'transport': 'حمل‌ونقل',
    'shopping': 'خرید',
    'bills': 'قبوض',
    'other': 'سایر',
}

# (تعداد تراکنش در یک ماه کامل، کمترین مبلغ، بیشترین مبلغ) به تومان
SPEC = {
    'food': (12, 120_000, 650_000),
    'transport': (6, 60_000, 350_000),
    'shopping': (3, 400_000, 2_500_000),
    'bills': (4, 250_000, 1_200_000),
    'other': (2, 150_000, 900_000),
}

# ضریب هزینه‌ی هر دسته در ۴ ماه (از قدیمی‌ترین تا ماه جاری)؛
# تا در مقایسه‌ی ماه‌ها هم افزایش دیده شود هم کاهش
FACTORS = {
    'food': [0.85, 0.95, 0.90, 1.30],
    'transport': [1.00, 1.10, 1.20, 0.70],
    'shopping': [0.80, 1.40, 0.90, 1.10],
    'bills': [1.00, 1.00, 1.05, 1.05],
    'other': [0.60, 1.00, 0.80, 0.90],
}

DESCRIPTIONS = {
    'food': ['ناهار', 'سوپرمارکت', 'رستوران', 'نان و لبنیات', 'میوه و سبزی', 'کافه'],
    'transport': ['اسنپ', 'بنزین', 'مترو', 'تاکسی'],
    'shopping': ['لباس', 'کفش', 'لوازم خانه', 'هدیه'],
    'bills': ['قبض برق', 'قبض گاز', 'اینترنت', 'قبض آب', 'شارژ ساختمان'],
    'other': ['متفرقه', 'دارو', 'تعمیرات'],
}


def _normalize(text):
    return text.replace('\u200c', '').replace(' ', '')


def find_category(type_, name):
    for category in Category.objects.filter(user=None, type=type_):
        if _normalize(category.name) == _normalize(name):
            return category
    raise CommandError(
        f'دسته‌ی پیش‌فرض «{name}» پیدا نشد. اول python manage.py migrate را اجرا کن.'
    )


def round_limit(value):
    return max(500_000, int(round(value / 100_000)) * 100_000)


class Command(BaseCommand):
    help = 'یک کاربر نمونه با چند ماه تراکنش و بودجه می‌سازد (برای دمو و اسکرین‌شات).'

    def handle(self, *args, **options):
        rng = random.Random(1405)
        today = timezone.localdate()
        year, month = current_jalali_month(today)

        self._remove_old_demo_user()
        user = User.objects.create_user(
            username=DEMO_USERNAME, email=DEMO_EMAIL, password=DEMO_PASSWORD
        )

        expense = {key: find_category('expense', name) for key, name in CATEGORY_NAMES.items()}
        salary = find_category('income', 'حقوق')
        side = find_category('income', 'درآمد جانبی')

        rows = []
        spent_now = {key: 0 for key in expense}

        for index in range(4):          # ۰ = سه ماه قبل ... ۳ = ماه جاری
            m_year, m_month = shift_month(year, month, index - 3)
            start, end = jalali_month_range(m_year, m_month)
            last = min(end, today)
            span = (last - start).days
            fraction = (span + 1) / ((end - start).days + 1)

            rows.append(Transaction(
                user=user, category=salary, amount=Decimal(25_000_000 + 500_000 * index),
                date=start, description='حقوق ماهانه',
            ))
            if index != 2:
                rows.append(Transaction(
                    user=user, category=side,
                    amount=Decimal(rng.randrange(3_000_000, 6_000_000, 100_000)),
                    date=start + timedelta(days=min(11, span)), description='پروژه‌ی فریلنسری',
                ))

            for key, category in expense.items():
                base_count, low, high = SPEC[key]
                count = max(1, round(base_count * fraction))
                factor = FACTORS[key][index]
                for _ in range(count):
                    day = start + timedelta(days=rng.randint(0, span))
                    amount = int(rng.randrange(low, high, 10_000) * factor) // 10_000 * 10_000
                    amount = max(amount, 10_000)
                    rows.append(Transaction(
                        user=user, category=category, amount=Decimal(amount),
                        date=day, description=rng.choice(DESCRIPTIONS[key]),
                    ))
                    if index == 3:
                        spent_now[key] += amount

        Transaction.objects.bulk_create(rows)

        # بودجه‌ی ماه جاری: خوراک نزدیک سقف، حمل‌ونقل از سقف گذشته، دو دسته در محدوده
        plans = {'food': 1 / 0.85, 'transport': 0.8, 'shopping': 2.0, 'bills': 1.3}
        for key, ratio in plans.items():
            Budget.objects.create(
                user=user, category=expense[key], year=year, month=month,
                limit_amount=Decimal(round_limit(spent_now[key] * ratio)),
                alert_threshold=80,
            )

        self.stdout.write(self.style.SUCCESS(
            f'کاربر نمونه ساخته شد: {len(rows)} تراکنش در ۴ ماه تا {month_label(year, month)}، و ۴ بودجه.'
        ))
        self.stdout.write(f'نام کاربری: {DEMO_USERNAME}   رمز عبور: {DEMO_PASSWORD}')

    def _remove_old_demo_user(self):
        old = User.objects.filter(username=DEMO_USERNAME).first()
        if old:
            Transaction.objects.filter(user=old).delete()
            Budget.objects.filter(user=old).delete()
            old.delete()