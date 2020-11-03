# Generated by Django 3.1.2 on 2020-10-26 15:24

from django.db import migrations, models
from django.utils import timezone


def add_status(apps, schema):
    Order = apps.get_model('orders', 'Order')
    updated = Order.objects.filter(fulfilled=True).update(status='fulfilled')
    print(f'{updated} orders updated')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_auto_20201026_1015'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('unfulfilled', 'Unfulfilled'),
                    ('fulfilled', 'Fulfilled'),
                    ('cancelled', 'Cancelled/Deleted'),
                ],
                default='unfulfilled',
                max_length=120,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='carrier',
            field=models.CharField(
                blank=True, choices=[('dhl', 'DHL'), ('dhl', 'ExpressFreight')], max_length=20, null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now, verbose_name='Created'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order', name='shipping_id', field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order', name='tracking_url', field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(add_status),
        migrations.RemoveField(model_name='order', name='fulfilled',),
        migrations.AddField(
            model_name='order', name='extra_data', field=models.JSONField(blank=True, null=True, default=dict),
        ),
        migrations.AlterModelOptions(name='order', options={'ordering': ('-created',)},),
    ]
