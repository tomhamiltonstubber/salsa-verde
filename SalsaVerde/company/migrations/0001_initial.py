# Generated by Django 3.0.8 on 2020-08-18 15:41

import datetime
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('website', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                (
                    'is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status',
                    ),
                ),
                (
                    'is_staff',
                    models.BooleanField(
                        default=False,
                        help_text='Designates whether the user can log into this admin site.',
                        verbose_name='staff status',
                    ),
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                        verbose_name='active',
                    ),
                ),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='Last name')),
                (
                    'last_logged_in',
                    models.DateTimeField(
                        default=datetime.datetime(2018, 1, 1, 0, 0, tzinfo=utc), verbose_name='Last Logged in'
                    ),
                ),
                ('street', models.TextField(blank=True, null=True, verbose_name='Street Address')),
                ('town', models.CharField(blank=True, max_length=50, null=True, verbose_name='Town')),
                ('country', models.CharField(blank=True, max_length=50, null=True, verbose_name='Country')),
                ('postcode', models.CharField(blank=True, max_length=20, null=True, verbose_name='Postcode')),
                ('phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='Phone')),
                (
                    'company',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='company.Company', verbose_name='Company'
                    ),
                ),
            ],
            options={'verbose_name': 'User', 'verbose_name_plural': 'Users',},
        ),
    ]
