from django.core.management import BaseCommand, call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Recreates database schema and populates it with fake data'

    def add_arguments(self, parser):
        parser.add_argument('--create-demo-data', action='store_true', dest='create_demo_data', default=False, help='')

    def handle(self, *args, **options):
        cur = connection.cursor()
        cur.execute('DROP SCHEMA public CASCADE;')
        cur.execute('CREATE SCHEMA public;')

        call_command('migrate', run_syncdb=True)

        if options['create_demo_data']:
            call_command('create_demo_data')
        else:
            print('\nnot creating demo data, use the "--create-demo-data" option if you require one.')
