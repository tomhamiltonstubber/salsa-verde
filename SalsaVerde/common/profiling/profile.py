import os
import threading
from dataclasses import asdict, dataclass
from functools import wraps

import psutil
from devtools import sformat, sprint
from django.conf import settings

from SalsaVerde.common.profiling._call_stack_profiler import call_stack_profiler
from SalsaVerde.common.profiling._queries_profiler import queries_profiler


@dataclass
class ProfilerSettings:
    """
    Settings passed to the profiler when executing a job or request. It takes the settings.PROFILING_SETTINGS if they
    exist.
    """

    _profile_requests: bool = settings.DEBUG and not settings.TESTING
    _profile_jobs: bool = settings.DEBUG and not settings.TESTING

    profile_call_stack: bool = False
    pcs_vars: bool = False
    profile_queries: bool = False
    pq_short_queries: bool = True
    pq_min_count: int = 3
    pq_print_stack: bool = False
    pq_min_time: int = 300
    profile_memory: bool = False

    @property
    def profile_requests(self):
        return self._profile_requests

    @property
    def profile_jobs(self):
        return self._profile_jobs

    def dict(self):
        return {k: v for k, v in asdict(self).items() if not k.startswith('_')}


try:
    profiling_settings = ProfilerSettings(**settings.PROFILING_SETTINGS)
except AttributeError:
    profiling_settings = ProfilerSettings()


@dataclass
class _TCProfile(threading.local):
    """
    A context manager that can be called to profile code.
    For example:

    def foo():
        with tc_profile(profile_queries=True):
            generate_all_accounting()
        print('did the thing')

    The main two options are profile_call_stack and profile_queries, others are options for them.
    """

    # A description to show what's being profiled
    description: str = ''

    # For profiling the called functions, will print the call stack of the functions that have been run
    profile_call_stack: bool = False
    # When profile_call_stack = True, will print all the variables passed to the function.
    # NOTE: Be careful here as this evaluates the variables so can give a false impressions of query count/speed etc.
    pcs_vars: bool = False

    # For profiling queries. print_queries will print all the queries that have been run within the context manager,
    # showing the count of each one and the time taken to execute
    profile_queries: bool = False
    # When profile_queries = True, will only print a shortened version of the queries
    pq_short_queries: bool = True
    # When profile_queries = True, will only print queries that have been duplicated >= pq_min_count
    pq_min_count: int = 3
    # When profile_queries = True, will only print queries that have taken >= pq_min_time ms to execute
    pq_min_time: int = 300
    # When profile_queries = True, will print the stack trace of the queries that have been run
    # (the python that caused the query to be run)
    pq_print_stack: bool = False

    # For profiling memory usage
    profile_memory: bool = False

    def __post_init__(self):
        self.defaults = self.__dict__.copy()
        self.mem_usage_start = None

    def __enter__(self):
        if any(bool(v) for v in [self.profile_call_stack, self.profile_queries]):
            sprint(f'\n  Start: {self.description}', sformat.green, sformat.bold)
        if self.profile_call_stack:
            call_stack_profiler.start(print_vars=self.pcs_vars)

        if self.profile_queries:
            queries_profiler.start(
                short_queries=self.pq_short_queries,
                print_stack=self.pq_print_stack,
                min_count=self.pq_min_count,
                min_time=self.pq_min_time,
            )

        if self.profile_memory:
            self.mem_usage_start = psutil.Process(os.getpid()).memory_info().rss

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profile_call_stack:
            call_stack_profiler.finish()

        if self.profile_queries:
            queries_profiler.finish()

        for k in self.defaults.keys():
            setattr(self, k, self.defaults[k])
        if any(bool(v) for v in [self.profile_call_stack, self.profile_queries]):
            sprint(f'  Finish: {self.description}\n', sformat.green, sformat.bold)

        if self.profile_memory:
            mem_used = psutil.Process(os.getpid()).memory_info().rss - self.mem_usage_start
            sprint(f'Memory used: {round(mem_used / 1024 / 1024, 2)}MB', sformat.green, sformat.bold)


profile = _TCProfile


def tc_profile_decorator(**profiler_kwargs):
    """
    A decorator for profiling a function
    """

    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            with profile(**profiler_kwargs, description=f'Profiling decorated function "{func.__qualname__}"...'):
                return func(*args, **kwargs)

        return inner

    return outer
