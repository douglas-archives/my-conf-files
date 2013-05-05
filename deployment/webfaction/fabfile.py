# -*- coding: utf-8 -*-
import os
import sys
import time
import xmlrpclib
from fabric.api import cd, env, roles, run, local
from fabric.contrib.files import exists, upload_template


env.root = os.path.dirname(os.path.abspath(__file__))
env.repo = 'git@bitbucket.org:MY_USER/MY_PROJECT.git'  # where is your repo?
env.project = 'MY_PROJECT'
env.project_root = '/home/MY_PROJECT/webapps/%(project)s' % env
env.app_root = os.path.join(env.project_root, 'project')
env.virtualenv_dir = '/home/MY_PROJECT/.virtualenvs/MY_PROJECT'
env.user = 'MY_USER'
env.roledefs = {
    'server': ['MY_PROJECT.com'],
}


@roles('server')
def install_app():
    def write_output(output):
        f = file('output_app_installed.txt', 'w')
        f.write(output)
        f.close()

    output = _webfaction_create_app()
    run('git clone %(repo)s %(project_root)s' % env)

    _install_pip()
    _install_virtualenv()
    _create_virtualenv()
    write_output(output)
    print 'check the output in output_app_installed.txt'


def _webfaction_create_app():
    """
        creates a "custom app with port" app on webfaction using the webfaction public API.
    """
    password = raw_input('Pass for "%(user)s":' % env)
    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    session_id, account = server.login(env.user, password)

    try:
        response = server.create_app(session_id, env.project, 'custom_app_with_port', False, '')
        print "App on webfaction created: %s" % response
        return str(response)

    except xmlrpclib.Fault:
        print "Could not create app on webfaction %s, app name maybe already in use" % env.project
        sys.exit(1)


@roles('server')
def _install_pip():
    run('mkdir -p ~/lib/python2.7')
    run("easy_install-2.7 pip")


@roles('server')
def _install_virtualenv():
    run("pip install virtualenv")


@roles('server')
def _create_virtualenv():
    run("virtualenv --no-site-packages --python=python2.7 %(virtualenv_dir)s" % env)


@roles('server')
def update_app():
    with cd(env.project_root):
        run("git pull origin master")


def push():
    local("git push bitbucket master")


@roles('server')
def pip_install():
    run("%(virtualenv_dir)s/bin/pip install -r %(project_root)s/requirements.txt" % env)


@roles('server')
def collect_static_files():
    with cd(env.project_root):
        run("%(virtualenv_dir)s/bin/python manage.py collectstatic -v 0 --noinput  --settings=MY_PROJECT.settings.prod" % env)


@roles('server')
def start_migration():
    with cd(env.project_root):
        run("%(virtualenv_dir)s/bin/python manage.py db-migrate" % env)


@roles('server')
def start_gunicorn():
    with cd(env.project_root):
        run('./start_gunicorn_prod.py')


@roles('server')
def stop_gunicorn():
    with cd(env.project_root):
        if exists('gunicorn.pid'):
            run('kill `cat gunicorn.pid`')


@roles('server')
def restart_gunicorn():
    stop_gunicorn()
    time.sleep(10)
    start_gunicorn()


@roles('server')
def create_user():
    with cd(env.project_root):
        run("%(virtualenv_dir)s/bin/python manage.py createsuperuser --settings=MY_PROJECT.settings.prod" % env)


@roles('server')
def example_upload_something():
    upload_template('somefile.sh', '%(project_root)s' % env)
    # do something with the file (on the server)
    run("chmod +x %(project_root)s/somefile.sh" % env)


@roles('server')
def syncdb():
    with cd(env.project_root):
        run("%(virtualenv_dir)s/bin/python manage.py syncdb --settings=MY_PROJECT.settings.prod --noinput" % env)
        run("%(virtualenv_dir)s/bin/python manage.py migrate --noinput  --settings=MY_PROJECT.settings.prod" % env)


@roles('server')
def deploy():
    update_app()
    pip_install()
    syncdb()
    collect_static_files()
    restart_gunicorn()
