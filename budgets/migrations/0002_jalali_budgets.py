import datetime

import jdatetime
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def convert_to_jalali(apps, schema_editor):
    """ماه میلادی قدیمی را با روز ۱۵ آن به ماه شمسی تبدیل می‌کند."""
    Budget = apps.get_model('budgets', 'Budget')
    for budget in Budget.objects.all():
        if budget.year < 1700:      # قبلاً شمسی بوده
            continue
        mid = jdatetime.date.fromgregorian(
            date=datetime.date(budget.year, budget.month, 15)
        )
        year, month = mid.year, mid.month
        start = jdatetime.date(year, month, 1).togregorian()
        next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)
        end = jdatetime.date(next_year, next_month, 1).togregorian() - datetime.timedelta(days=1)
        Budget.objects.filter(pk=budget.pk).update(
            year=year, month=month, start_date=start, end_date=end
        )


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='start_date',
            field=models.DateField(default=datetime.date(2000, 1, 1), editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='budget',
            name='end_date',
            field=models.DateField(default=datetime.date(2000, 1, 1), editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='budget',
            name='year',
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1300), MaxValueValidator(1600)]
            ),
        ),
        migrations.RunPython(convert_to_jalali, migrations.RunPython.noop),
    ]