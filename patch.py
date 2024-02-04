import json
import os
import re
import sys
from itertools import groupby
from pathlib import Path

import click
import requests
from django.db import connection
from django.db.transaction import commit, set_autocommit

sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalsaVerde.settings')

import django

django.setup()

from SalsaVerde.company.models import Country
from SalsaVerde.orders.models import Order
from SalsaVerde.stock.models import ProductType, ProductTypeSize

commands = []


def command(func):
    commands.append(func)
    return func


@command
def correct_product_types(**kwargs):
    with open('product_types.json') as f:
        data = json.load(f)
    data = sorted(data, key=lambda x: x['code'])
    bad_names = []
    flavour_ids = []
    for code, pts in groupby(data, key=lambda x: x['code']):
        flavour_name = ''
        flavour = ProductType.objects.filter(code=code).first()
        flavour_ids.append(flavour.id)
        for pt in pts:
            name = pt['name']
            m = re.search('(.*?(Vinegar|Condiment|The Balsamic)) (.*)', name)
            if not flavour_name:
                try:
                    flavour_name = m.group(1)
                except AttributeError:
                    bad_names.append(name)
                    continue
            try:
                name = m.group(3).strip()
            except RuntimeError:
                print('Error in', name)
                continue
            ProductTypeSize.objects.create(product_type=flavour, bar_code=pt['sku_code'], size=0.250, name=name)
        ProductType.objects.exclude(id__in=flavour_ids).filter(code=code).delete()


stock_models = {
    'Company',
    'Supplier',
    'IngredientType',
    'Ingredient',
    'ContainerType',
    'Container',
    'YieldContainer',
    'ProductType',
    'ProductTypeSize',
    'Product',
    'ProductIngredient',
    'Document',
    'Area',
    'Complaint',
    'GlassAudit',
    'GlassBreakagereport',
    'PlasterReport',
    'User',
}


@command
def rename_stock_app(live):
    # Rename app from main to stock
    with connection.cursor() as cursor:
        cursor.execute("UPDATE django_content_type SET app_label='stock' WHERE app_label='main'")
        # Rename models in app
        for model in stock_models:
            cursor.execute(f'ALTER TABLE main_{model} RENAME TO stock_{model}')
        cursor.execute("UPDATE django_migrations SET app='stock' WHERE app='main'")


user_fields = [
    'email',
    'password',
    'first_name',
    'last_name',
    'last_logged_in',
    'street',
    'town',
    'country',
    'postcode',
    'phone',
]


@command
def delete_all_migrations(**kwargs):
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM django_migrations')


@command
def create_countries(**kwargs):
    r = requests.get('https://restcountries.eu/rest/v2/all?fields=name;alpha2Code;alpha3Code')
    r.raise_for_status()
    countries = [Country(name=c['name'], iso_2=c['alpha2Code'], iso_3=c['alpha3Code']) for c in r.json()]
    created = Country.objects.bulk_create(countries)
    print(f'Created {len(created)} countries')


@command
def delete_wrong_orders(live):
    fulfilled = Order.objects.filter(status=Order.STATUS_FULFILLED).values_list('shopify_id', flat=True)
    Order.objects.filter(status=Order.STATUS_UNFULFILLED, shopify_id__in=fulfilled).delete()
    for order in Order.objects.all():
        orders = Order.objects.filter(shopify_id=order.shopify_id)
        if orders.count() > 1:
            orders.exclude(id=orders[0].id).delete()


@click.command()
@click.argument('command', type=click.Choice([c.__name__ for c in commands]))
@click.option('--live', is_flag=True)
def patch(command, live):
    command_lookup = {c.__name__: c for c in commands}

    set_autocommit(False)
    command_lookup[command](live=live)

    if live:
        click.echo('live, committing transaction...')
        commit()
    else:
        click.echo('not live, not committing.')


if __name__ == '__main__':
    patch()
