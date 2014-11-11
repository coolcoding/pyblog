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

_TAR_FILE        = 'dist-awesome.tar.gz'
_REMOTE_TMP_TAR  = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/awesome'

def _current_path():
    return os.path.abspath('.')

def _now():
    return datetime.now().strftime('%y-%m-%d_%H.%M.%S')

def build():
    '''
    compress www dir
    '''
    with lcd(os.path.join(os.path.abspath('.'),'www')):
        local('rm -f dist/%s' % _TAR_FILE)
        includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
        excludes = ['test', '.*', '*.pyc', '*.pyo']
        cmd      = ['tar','--dereference','-zcvf','../dist/%s' % _TAR_FILE]
        cmd.extend('--exclude=\'%s\'' % ex for ex in excludes)
        cmd.extend(includes)
        print ' '.join(cmd)
        local(' '.join(cmd))



def deploy():
    newdir = 'www-%s' % _now()
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
        

def restore2local():
    '''
    restore db to local
    '''

    backup_dir = os.path.join(_current_path(),'backup')
    fs = os.listdir(backup_dir)
    files = [f for f in fs if f.startswith('backup-') and f.endswith('.sql.tar.gz')]
    files.sort(cmp=lambda x, y: 1 if x < y else -1)
    if len(files)==0:
        print 'No backup files found.'
        return
    print ('Found %s backup files:' % len(files))
    print ('=========================================================')
    n = 0
    for f in files:
        print ('%s: %s' % (n,f))
        n = n + 1
    print ('=========================================================')
    print ('')
    try:
        num = int(raw_input('restore file: '))
    except ValueError:
        print ('Invalid file number.')
        return
    restore_file = files[num]
    yn = raw_input('Restore file %s: %s? y/n' % (num,restore_file))
    if yn != 'y' and yn != 'Y':
        print ('Restore cancelled.')
        return
    print ('start restore to local database...')
    p = raw_input('input mysql root password:')
    sqls = [
        'drop database if exists awesome;',
        'create database awesome;',
        'grant select, insert, update, delete on awesome.* to \'%s\'@\'localhost\' identified by \'%s\';'
    ]

    for sql in sqls:
        local(r'mysql -uroot -p%s -e "%s"' % (p,sql))
    with lcd(backup_dir):
        local('tar zxvf %s' % restore_file)
    local(r'mysql -uroot -p%s awesome < backup/%s' % (p,restore_file[:-7]))
    with lcd(backup_dir):
        local('rm -f %s' % restore_file[:-7])
