# Generated by Django 3.0.7 on 2020-07-19 16:04

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stock', '0006_auto_20190513_1821'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping_id', models.CharField(max_length=255)),
                ('shopify_id', models.CharField(max_length=255)),
                ('tracking_url', models.CharField(max_length=255)),
                (
                    'label_urls',
                    django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), size=None),
                ),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.Company')),
            ],
        ),
    ]
