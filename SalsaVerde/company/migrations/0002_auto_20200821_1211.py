# Generated by Django 3.0.9 on 2020-08-21 12:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def set_country_blank(apps, schema):
    apps.get_model('company', 'user').objects.update(country=None)


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_country_blank),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('iso_2', models.CharField(max_length=2, verbose_name='2 Letter ISO')),
                ('iso_3', models.CharField(max_length=3, verbose_name='3 Letter ISO')),
            ],
        ),
        migrations.AddField(
            model_name='company', name='dhl_account_code', field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='company',
            name='main_contact',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contact_company',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Phone'),
        ),
        migrations.AddField(
            model_name='company',
            name='postcode',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Postcode'),
        ),
        migrations.AddField(
            model_name='company',
            name='street',
            field=models.TextField(blank=True, null=True, verbose_name='Street Address'),
        ),
        migrations.AddField(
            model_name='company',
            name='town',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Town'),
        ),
        migrations.AlterField(
            model_name='user',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='company.Company',
                verbose_name='Company',
            ),
        ),
        migrations.AddField(
            model_name='company',
            name='country',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='company.Country'
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='country',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='company.Country'
            ),
        ),
    ]
