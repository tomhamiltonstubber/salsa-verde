#!/usr/bin/env python3.7
import subprocess
import sys
from time import time


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
    branch = run('git rev-parse --abbrev-ref HEAD').strip('\n')
    if branch == 'HEAD':
        # on a tag, take tag name as branch
        branch = run('git describe --tags').strip('\n')
    if branch != 'master':
        print('Not on master if you proceed you will deploy from %s' % branch)
        if input('Do you wish to continue? [y/N] ') != 'y':
            return

    print('On branch %r' % branch)

    app_name = 'salsaverde'
    command = f'git push heroku {branch}:master'

    print('\n    pushing to Heroku with "%s"...\n' % command)
    run(command, True)

    start = time()
    run('heroku maintenance:on --app %s' % app_name, True)
    print('\n\n    running django migrations on Heroku...\n')
    run('heroku run python manage.py migrate --app %s' % app_name, collect_output=False)
    run('heroku maintenance:off --app %s' % app_name, True)
    print('\n    migration complete, offline for {:0.0f}s\n'.format(time() - start))


if __name__ == '__main__':
    deploy()
