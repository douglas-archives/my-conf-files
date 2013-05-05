#!/bin/bash
source /home/USER/.virtualenvs/DJANGO_PROJECT_NAME/bin/activate
cd ~/webapps/DJANGO_PROJECT_NAME
export DJANGO_SETTINGS_MODULE=DJANGO_PROJECT_NAME.settings.production
/home/USER/.virtualenvs/DJANGO_PROJECT_NAME/bin/python2.7 manage.py run_gunicorn -c etc/gunicorn.production.conf --daemon --settings=DJANGO_PROJECT_NAME.settings.production && sleep 3