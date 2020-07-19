# Generated by Django 2.1.5 on 2019-01-12 16:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20180918_0746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productingredient',
            name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='product_ingredients',
                to='main.Product',
                verbose_name='Product',
            ),
        ),
    ]
