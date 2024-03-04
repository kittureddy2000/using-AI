# Generated by Django 4.2.7 on 2024-02-20 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='spinfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('avg_closing_price', models.DecimalField(decimal_places=2, max_digits=15)),
                ('year_open', models.DecimalField(decimal_places=2, max_digits=15)),
                ('year_high', models.DecimalField(decimal_places=2, max_digits=15)),
                ('year_low', models.DecimalField(decimal_places=2, max_digits=15)),
                ('year_close', models.DecimalField(decimal_places=2, max_digits=15)),
                ('spreturn', models.DecimalField(decimal_places=2, max_digits=15)),
                ('return_divident', models.DecimalField(decimal_places=2, max_digits=15)),
                ('inflation', models.DecimalField(decimal_places=2, max_digits=15)),
            ],
        ),
    ]
