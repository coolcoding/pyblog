#!/usr/bin/env python

from models import User, Blog, Comment
from transwarp import db

db.create_engine(user='root',password='root',database='awesome')
u = User(name='Test', email='test1@example.com', password='1234567890', image='about:blank')
u.insert()
print 'new user id:', u.id

u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name
u1.delete()
