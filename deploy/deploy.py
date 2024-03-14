import argparse
import subprocess
import sys
from pathlib import Path
from time import time

THIS_DIR = Path(__file__).resolve().parent


parser = argparse.ArgumentParser(description='Deploy to Heroku')


def run(c, print_out=False, collect_output=True):
    if collect_output:
        p = subprocess.Popen(c.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        out = ''
        for line in iter(p.stdout.readline, ''):
            if print_out:
                sys.stdout.write(line)
            out += line
    else:
        out = 'not collected'
        p = subprocess.Popen(c.split())
    if p.wait():
        raise Exception('Error Running "%s"\n    stdout & stderr: \n%s\n' % (c, out))
    return out


def deploy():
    command = 'git push heroku master'
    print(f'\n\n    pushing to Heroku with "{command}"...\n')
    run(command, True)

    start = time()
    run('heroku maintenance:on --app salsaverde', True)
    print('\n\n    running django migrations on Heroku...\n')
    run('heroku run python manage.py migrate --app salsaverde', collect_output=False)
    run('heroku maintenance:off --app salsaverde', True)
    print('\n    migration complete, offline for {:0.0f}s\n'.format(time() - start))


if __name__ == '__main__':
    deploy()
