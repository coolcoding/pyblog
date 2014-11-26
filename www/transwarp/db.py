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
        return self._connect()


def create_engine(user,password,database,host='127.0.0.1',port=3306,**kw):
    import mysql.connector
    global engine
    if engine is not None:
        raise DBError('Engine is already initalized.')
    params   = dict(user = user, password = password, database = database, host= host, port = port)
    defaults = dict(use_unicode = True, charset  = 'utf8', collation  = 'utf8_general_ci', autocommit = False)
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params['buffered'] = True
    engine = _Engine(lambda: mysql.connector.connect(**params))
    logging.info('Init mysql engine <%s> ok.' % hex(id(engine)))


class _LasyConnection(object):

    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            connection = engine.connect() 
            logging.info('open connection<%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()


    def rollback(self):
        self.connection.rollback()


    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            logging.info('close connection <%s>...' % hex(id(connection)))
            connection.close()


class _DbCtx(threading.local):

    def __init__(self):
        self.connection = None
        self.transactions = 0

    def isInit(self):
        return not self.connection is None

    def init(self):
        logging.info('open lasy connection...')
        self.connection = _LasyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None


    def cursor(self):
        return self.connection.cursor()
_db_ctx = _DbCtx()

class _ConnectionCtx(object):

    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        if not _db_ctx.isInit():
            _db_ctx.init()
            self.should_cleanup = True
        return self

    def __exit__(self,exctype,excvalue,traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()

def connection():
    return _ConnectionCtx()



def with_connection(func):

    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper


def _select(sql,first,*args):

    global _db_ctx
    cursor = None
    sql = sql.replace('?','%s')
    logging.info('SQL: %s, ARGS: %s' % (sql,args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql,args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names,values)
        return [Dict(names,x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()

@with_connection
def select_one(sql, *args):

    return _select(sql, True, *args)


@with_connection
def select(sql, *args):

    return _select(sql,False,*args)

@with_connection
def _update(sql,*args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?','%s')
    logging.info('SQL: %s ARGS: %s' % (sql,args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql,args)
        r = cursor.rowcount
        return r
    finally:
        if cursor:
            cursor.close()


def update(sql, *args):

    return _update(sql, *args)


def insert(table, **kw):

    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values(%s)' % (table,','.join(['`%s`' % col for col in cols]),','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    create_engine('root','root','awesome')
    print select_one('select * from users')
