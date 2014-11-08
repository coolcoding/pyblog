#!/usr/bin/env python
#-*- coding: utf-8 -*-

import time,logging,functools,threading,uuid

class Dict(dict):

    def __init__(self,names=(),values=(),**kw):
        super(Dict,self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v


    def __getattr__(self,k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError('Dict object has no attribute %s' % k)

    def __setattr__(self, k, v):
        self[k] = v



def next_id(t=None):
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t*1000),uuid.uuid4().hex)

#global engine object
engine = None


class _Engine(object):

    def __init__(self,connect):
        self._connect = connect


    def connect(self):
        return self._connect


def create_engine(user,password,database,host='127.0.0.1',port=3306,**kw):
    import mysql.connector
    global engine
    if engine is not None:
        raise DBError('Engine is already initalized.')
    params   = dict(user        = user, password = password, database = database, host                = host, port = port)
    defaults = dict(use_unicode = True, charset  = 'utf8', collation  = 'utf8_general_ci', autocommit = False)
    params[
