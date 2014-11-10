#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os,re
from datetime import datetime
from fabric.api import *

#server login username
env.user = 'root'

#sudo user
env.sudo_user = 'root'

#server ip
env.hosts = ['192.168.56.200']

#server mysql user,password
db_user = 'root'
db_password = 'root'

_TAR_FILE = 'dist-awesome.tar.gz'

def build():
    with lcd(os.path.join(os.path.abspath('.'),'www')):
        local('rm -f dist/%s' % _TAR_FILE)
        includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
        excludes = ['test', '.*', '*.pyc', '*.pyo']
        cmd      = ['tar','--dereference','-zcvf','../dist/%s' % _TAR_FILE]
        cmd.extend('--exclude=\'%s\'' % ex for ex in excludes)
        cmd.extend(includes)
        print ' '.join(cmd)
        local(' '.join(cmd))


_REMOTE_TMP_TAR  = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/awesome'

def deploy():
    newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    run('rm -f %s' % _REMOTE_TMP_TAR)
    put('dist/%s' % _TAR_FILE,_REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        run('mkdir %s' % newdir)
    with cd('%s/%s' % (_REMOTE_BASE_DIR,newdir)):
        run('tar -zxvf %s' % _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        run('rm -f www')
        run('ln -s %s www' % newdir)
        run('chown root:root www')
        run('chown -R root:root %s' % newdir)
    with settings(warn_only=True):
        run('/etc/init.d/nginx reload')
        
