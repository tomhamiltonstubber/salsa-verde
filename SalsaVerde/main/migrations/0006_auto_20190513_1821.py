# Generated by Django 2.1.7 on 2019-05-13 18:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20190325_2025'),
    ]

    operations = [
        migrations.RemoveField(model_name='container', name='status',),
        migrations.RemoveField(model_name='ingredient', name='status',),
        migrations.AddField(
            model_name='container',
            name='intake_quality_check',
            field=models.BooleanField(
                default=False, help_text='Goods are free from damage and pests', verbose_name='Accept goods'
            ),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='intake_quality_check',
            field=models.BooleanField(
                default=False, help_text='Goods are free from damage and pests', verbose_name='Accept goods'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='batch_code_applied',
            field=models.BooleanField(default=False, verbose_name='Batch code applied'),
        ),
        migrations.AddField(
            model_name='product',
            name='best_before_applied',
            field=models.BooleanField(default=False, verbose_name='Best before applied'),
        ),
        migrations.AddField(
            model_name='product',
            name='quality_check_successful',
            field=models.BooleanField(default=False, verbose_name='Quality check successful'),
        ),
        migrations.AlterField(
            model_name='container',
            name='container_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='containers',
                to='main.ContainerType',
                verbose_name='Container',
            ),
        ),
    ]
