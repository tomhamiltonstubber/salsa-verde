import json
import os
import re
import sys
from itertools import groupby
from pathlib import Path

import click
from django.db.transaction import commit, set_autocommit

sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalsaVerde.settings')

import django

django.setup()

from SalsaVerde.main.models import ProductType, ProductTypeSize

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
