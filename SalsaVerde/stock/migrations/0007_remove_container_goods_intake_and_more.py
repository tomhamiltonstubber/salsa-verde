# Generated by Django 4.2.9 on 2024-03-14 19:28

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('stock', '0006_remove_container_goods_intake_and_more')]

    operations = [
        migrations.RemoveField(model_name='container', name='goods_intake'),
        migrations.RemoveField(model_name='ingredient', name='goods_intake'),
        migrations.DeleteModel(name='GoodsIntake'),
    ]