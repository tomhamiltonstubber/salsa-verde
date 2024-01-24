import sys

WHITELISTED_FILES = {}

WHITELISTED_FUNCS = {
    '__init__',
    '__call__',
    '__enter__',
    '__exit__',
    '__str__',
    'list_func',
}
WHITELISTED_VARS = {'self', 'cls', 'args', 'kwargs', '__class__'}


class TEXTCOLOURS:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def _bl(s):
    return f'{TEXTCOLOURS.BLUE}{s}{TEXTCOLOURS.ENDC}'


def _cy(s):
    return f'{TEXTCOLOURS.CYAN}{s}{TEXTCOLOURS.ENDC}'


def _gr(s):
    return f'{TEXTCOLOURS.GREEN}{s}{TEXTCOLOURS.ENDC}'


def _profile_func(print_locals=False):
    def _tracefunc(frame, event, arg, indent=[0]):
        if 'TutorCruncher/' not in frame.f_code.co_filename:
            return _tracefunc
        file_name = frame.f_code.co_filename.split('TutorCruncher/')[-1]
        func = frame.f_code.co_name
        should_log_event = (
            file_name not in WHITELISTED_FILES
            and not file_name.endswith('.jinja')
            and func not in WHITELISTED_FUNCS
            and not func.startswith('<')
        )
        if should_log_event:
            if event == 'call':
                print(f'{"-" * indent[0] * 2}{indent[0]} {_bl(file_name.split("SalsaVerde/")[-1])}: {func}')
                if print_locals:
                    for loc_name, loc_value in frame.f_locals.items():
                        if loc_name in WHITELISTED_VARS:
                            continue
                        print(f'{"-" * indent[0] * 2}    {_gr(loc_name)}: {loc_value}')
                indent[0] += 1
            elif event == 'return':
                indent[0] -= 1
        return _tracefunc

    return _tracefunc


class _Profiler:
    """
    Used for profiling the call stack run. This is useful for finding out where a function is being called from, or what
    the system is calling and when.
    """

    def start(self, print_locals=False):
        sys.setprofile(_profile_func(print_locals))

    def finish(self):
        sys.setprofile(None)


call_stack_profiler = _Profiler()
