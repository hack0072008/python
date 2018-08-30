#!/usr/bin/python
# -*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2016 , Inc.
# All Rights Reserved.


import time
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import resolve_url
from django.contrib.auth.views import redirect_to_login


from functools import wraps

def login_required(function = None, redirect_field_name = None, login_url=None):
    def _login_required(request, *args, **kwargs):
        if not request.session.get('user_uuid', default = None):
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            return redirect_to_login(path, resolved_login_url, redirect_field_name)
        else:
            return function(request, *args, **kwargs)
    return _login_required

def print_log(function = None, LOG = None):
    def decorator(function):
        @wraps(function)
        def _print_log(request, *args, **kwargs):
            LOG.info('{0} {1}'.format(request.method, request.path))
            return function(request, *args, **kwargs)
        return _print_log
    return decorator
