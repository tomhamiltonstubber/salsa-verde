# Generated by Django 3.0.9 on 2020-08-20 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
        ('orders', '0002_packagetemplate'),
    ]

    operations = [
        migrations.AddField(model_name='order', name='fulfilled', field=models.BooleanField(default=False)),
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='products', to='stock.Product'),
        ),
        migrations.AlterField(
            model_name='order', name='shopify_id', field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
