# Generated by Django 3.0.9 on 2020-08-20 16:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_product_finished'),
        ('orders', '0003_auto_20200820_1425'),
    ]

    operations = [
        migrations.RemoveField(model_name='order', name='products',),
        migrations.CreateModel(
            name='ProductOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='products', to='orders.Order'
                    ),
                ),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='stock.Product'
                    ),
                ),
            ],
        ),
    ]
