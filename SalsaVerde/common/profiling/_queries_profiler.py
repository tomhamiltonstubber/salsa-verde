import re
import traceback
from dataclasses import dataclass
from textwrap import indent
from time import time

import sqlparse
from devtools import sformat, sprint
from django.db import connection
from django.db.backends.postgresql.base import CursorDebugWrapper
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.python import PythonTracebackLexer
from pygments.lexers.sql import PlPgsqlLexer

from SalsaVerde.common.profiling._call_stack_profiler import WHITELISTED_FILES, WHITELISTED_FUNCS


def _format_query(sql):
    """Format SQL with syntax highlighting and indentation."""
    sql = indent(sqlparse.format(str(sql), reindent=True), ' ' * 4)
    return highlight(sql, PlPgsqlLexer(), Terminal256Formatter(style='fruity')).strip('\n')


def _shorten_sql(sql):
    for t in ['SELECT', 'AS']:
        select_statement = re.search(rf'{t} (.*?) FROM', sql)
        if select_statement:
            models = select_statement.group(1).split(', ')
            models = set(f'{m.split(".")[0].strip()}."X…"' for m in models)
            sql = re.sub(rf'{t} (.*?) FROM', '{} {} FROM'.format(t, ', '.join(models)), sql)
    return sql


@dataclass
class DebugQuery:
    raw_sql: str
    sql: str
    time: int
    stack: list[str]


class DebugDBQueries:
    def __init__(self):
        self.queries: list[DebugQuery] = []

    def add(self, query: DebugQuery):
        self.queries.append(query)

    def reset(self):
        self.queries = []


db_queries = DebugDBQueries()


def _parse_stack(q: DebugQuery) -> str:
    parsed_stack = []
    for line in q.stack:
        if '/TutorCruncher/' not in line:
            continue
        file_name = re.search(r'File "(.*?)"', line).group(1).split('TutorCruncher/')[-1]
        line_number = re.search(r'line (\d+)', line).group(1)
        func = re.search(r', in (.*?)\n', line).group(1)
        if file_name in WHITELISTED_FILES:
            continue
        if func in WHITELISTED_FUNCS:
            continue
        if file_name.endswith('py'):
            call = re.search(r'\n(.*)\n', line).group(1).strip()
            parsed_stack.append(f'File "/TutorCruncher/{file_name}", line {line_number}, in {func}\n    {call}')
        else:
            parsed_stack.append(f'File "/TutorCruncher/{file_name}", line {line_number}, in {func}')
    return indent(
        highlight('\n'.join(parsed_stack), PythonTracebackLexer(), Terminal256Formatter(style='fruity')).strip('\n'),
        ' ' * 4,
    )


def _print_grouped_queries(queries: list[DebugQuery], shorten=True, min_count=0, min_time=300, print_stack=False):
    """
    Print a list of queries grouped by their anon SQL, arranged by the number of times they were run.
    """
    grouped_queries = {}
    total_time = 0
    for query in queries:
        # We use the raw_sql as it has no params, so can be grouped easily
        sql = query.raw_sql
        if shorten:
            sql = _shorten_sql(query.raw_sql)
        if sql not in grouped_queries:
            grouped_queries[sql] = {'time': 0, 'count': 0, 'example': query.sql}
        total_time += float(query.time)
        grouped_queries[sql]['time'] += float(query.time)
        grouped_queries[sql]['count'] += 1
        if print_stack and not grouped_queries[sql].get('stack'):
            grouped_queries[sql]['stack'] = _parse_stack(query)
    for sql, data in sorted(grouped_queries.items(), key=lambda x: x[1]['count']):
        print_query = data['count'] >= min_count or data['time'] >= min_time
        if not print_query:
            continue
        print(f'\n  Query made {data["count"]} times ({round(data["time"])}ms):\n{_format_query(sql)}')
        print('  Example:', _format_query(data['example']))
        if print_stack:
            print(f'  Stack:\n{data["stack"]}')
        print('-' * 80)
    sprint(f'  Ran {len(queries)} queries in {round(total_time)}ms', sformat.yellow, sformat.bold)


class _CustomCursorDebugWrapper(CursorDebugWrapper):
    """
    A custom CursorDebugWrapper that adds queries to a list for later printing.
    """

    def execute(self, sql, params=None):
        start = time()
        try:
            return super().execute(sql, params)
        finally:
            duration = time() - start
            raw_sql = sql
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            db_queries.add(
                DebugQuery(raw_sql=raw_sql, sql=sql, time=int(duration * 1000), stack=traceback.format_stack())
            )

    def executemany(self, sql, param_list):
        start = time()
        try:
            return super().executemany(sql, param_list)
        finally:
            duration = time() - start
            try:
                count = len(param_list)
            except TypeError:  # param_list could be an iterator
                count = -1
            for i in range(count):
                db_queries.add(
                    DebugQuery(
                        raw_sql=sql, sql=sql, time=int((duration * 1000) / count), stack=traceback.format_stack()
                    )
                )


def custom_make_debug_cursor(cursor):
    return _CustomCursorDebugWrapper(cursor, connection)


@dataclass
class _Profiler:
    """
    Used for profiling queries run. We set the connection's cursor to use our custom wrapper and then change it back.
    """

    short_queries: bool = True
    print_stack: bool = False
    min_count: int = 3
    min_time: int = 300

    def post_init(self):
        self.original_make_debug_cursor = None

    def start(self, **kwargs):
        for k, v in kwargs.items():
            assert hasattr(self, k), f'Profiler has no attribute {k}'
            setattr(self, k, v)
        self.original_make_debug_cursor = connection.make_debug_cursor
        connection.make_debug_cursor = custom_make_debug_cursor

    def finish(self, print_queries=True):
        connection.make_debug_cursor = self.original_make_debug_cursor
        if print_queries:
            _print_grouped_queries(
                db_queries.queries,
                shorten=self.short_queries,
                print_stack=self.print_stack,
                min_count=self.min_count,
                min_time=self.min_time,
            )
        db_queries.reset()


queries_profiler = _Profiler()
