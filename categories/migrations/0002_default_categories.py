from django.db import migrations

# (نام، نوع، رنگ)
DEFAULT_CATEGORIES = [
    ('خوراک', 'expense', '#e67e22'),
    ('حمل‌ونقل', 'expense', '#3498db'),
    ('خرید', 'expense', '#9b59b6'),
    ('قبوض', 'expense', '#e74c3c'),
    ('سایر', 'expense', '#95a5a6'),
    ('حقوق', 'income', '#27ae60'),
    ('درآمد جانبی', 'income', '#16a085'),
    ('سایر', 'income', '#7f8c8d'),
]


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    for name, type_, color in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            user=None,
            name=name,
            type=type_,
            defaults={'color': color},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
    ]
