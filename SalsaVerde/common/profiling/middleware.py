from statistics import mean
from time import time

from devtools import sformat, sprint
from django.db import connection

from SalsaVerde.common.profiling.profile import profile, profiling_settings


def profiling_middleware(get_response):
    """
    Middleware to profile requests. Will only be called for URLs not whitelisted.
    """

    def middleware(request):
        start_time = time()
        if not profiling_settings.profile_requests:
            return get_response(request)
        with profile(**profiling_settings.dict(), description=f'Profiling request to {request.path}...'):
            response = get_response(request)

        if response.status_code in [200, 301]:
            query_times = [float(q['time']) for q in connection.queries]  # Apparently the q['time'] can be '0.001'
            info = {
                'queries': len(query_times),
                'sum_query_time': f'{sum(query_times):0.0f}ms',
                'mean_query_time': f'{mean(query_times or [0]):0.0f}ms',
                'max_query_time': f'{max(query_times or [0]):0.0f}ms',
                'total_time': f'{(time() - start_time) * 1000:0.0f}ms',
            }
            info = ' '.join(f'{n}={v}' for n, v in info.items())
            sprint(f'{request.get_full_path():>50} | {info}', sformat.cyan)
        return response

    return middleware
