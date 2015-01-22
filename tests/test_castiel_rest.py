#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import urllib2
import json
import sys

__author__ = 'viruzzz-kun'


ROOT = 'http://127.0.0.1:5001'


def get(path):
    return requests.get(ROOT + path)


def test_availability():
    print('Testing CAS availability')
    r = get('/cas/')
    if r.status_code != 200:
        print('Failed. Status code =', r.status_code)
        return
    if r.content != 'I am Castiel, angel of God':
        print('Failed. Wrong answer. "%s"' % r.content)
        return
    print('Passed.\n')
    return True


def test_acquire(u, p, user_id):
    print('Testing CAS acquire token')
    r = get('/cas/api/acquire?login=%s&password=%s' % (urllib2.quote(u), urllib2.quote(p)))
    if r.status_code != 200:
        print('Failed. Status code =', r.status_code)
        return
    j = r.json()
    print('received:', j)
    if not j['success']:
        print('Failed. "%r"' % j)
        return
    if j['user_id'] != user_id:
        print('Failed. user_id doesn\'t match')
        return
    print('Passed\n')
    return j


def test_release(token):
    print('Testing CAS release token')
    r = get('/cas/api/release?token=%s' % token)
    if r.status_code != 200:
        print('Failed. Status code =', r.status_code)
        return
    j = r.json()
    print('received:', j)
    if not j['success']:
        print('Failed. "%r"' % j)
        return
    print('Passed\n')
    return j


def test_prolong(token):
    print('Testing CAS prolong token')
    r = get('/cas/api/prolong?token=%s' % token)
    if r.status_code != 200:
        print('Failed. Status code =', r.status_code)
        return
    j = r.json()
    print('received:', j)
    if not j['success']:
        print('Failed. "%r"' % j)
        return
    print('Passed\n')
    return j


def test_check(token, user_id):
    print('Testing CAS check token')
    r = get('/cas/api/check?token=%s' % token)
    if r.status_code != 200:
        print('Failed. Status code =', r.status_code)
        return
    j = r.json()
    print('received:', j)
    if not j['success']:
        print('Failed. "%r"' % j)
        return
    if j['user_id'] != user_id:
        print('Failed. user_id doesn\'t match')
        return
    print('Passed\n')
    return j


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('\nUsage:\n  %s <username> <password> <user id>\n' % sys.argv[0])
        sys.exit(-1)
    username, password, user_id = sys.argv[1:4]
    user_id = int(user_id)

    if not test_availability():
        exit(-1)

    if not test_acquire(username, password, user_id):
        exit(-1)
    r = test_acquire(username, password, user_id)
    if not r:
        exit(-1)
    l = test_prolong(r['token'])
    if not l:
        exit(-1)
    c = test_check(r['token'], user_id)
    if not c:
        exit(-1)
    e = test_release(r['token'])
    if not e:
        exit(-1)
