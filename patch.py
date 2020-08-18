import json
import os
import re
import sys
from itertools import groupby
from pathlib import Path

import click
from django.db import connection
from django.db.transaction import commit, set_autocommit

sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalsaVerde.settings')

import django

django.setup()

from SalsaVerde.stock.models import ProductType, ProductTypeSize, Company, User
from SalsaVerde.company.models import Company as NewCompany
from SalsaVerde.company.models import User as NewUser

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
    'GoodsIntake',
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
            cursor.execute(f"ALTER TABLE main_{model} RENAME TO stock_{model}")
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
def create_new_items(live):
    for company in Company.objects.order_by('id'):
        NewCompany.objects.create(name=company.name, website=company.website)
    companies = {c.name: c.id for c in NewCompany.objects.all()}
    for user in User.objects.order_by('id'):
        kwargs = {f: getattr(user, f) for f in user_fields if getattr(user, f, None)}
        kwargs['company_id'] = companies[user.company.name]
        NewUser.objects.create(**kwargs)


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
