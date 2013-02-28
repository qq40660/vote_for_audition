#!/usr/bin/env python
#coding=utf-8
# 数据库操作
# Version 1 by Dongwm 2013/02/22

import sys
import motor
import pymongo
from pymongo.errors import ConnectionFailure

def asyncdb(database, host='localhost', port=27017):
	'''操作motor,其实底层还是封装pymongo'''
	try:
		return motor.MotorClient(host, port).open_sync()[database]
	except ConnectionFailure, e:
		sys.stderr.write("Could not connect to MongoDB: %s" % e)
		sys.exit(1)


def db(database, host='localhost', port=27017):
	'''操作pymongo'''
	try:
		return pymongo.Connection(host, port)[database]
	except ConnectionFailure, e:
		sys.stderr.write("Could not connect to MongoDB: %s" % e)
		sys.exit(1)


