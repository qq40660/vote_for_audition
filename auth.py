#!/usr/bin/env python
#coding=utf-8
# 腾讯微博验证(openid&oauth2)
# Version 1 by Dongwm 2013/02/21

import logging
import urllib
import mimetools
import itertools

from tornado import escape
from tornado.httputil import url_concat
from tornado.auth import httpclient, OAuth2Mixin, OpenIdMixin


class WeiboMixin(OpenIdMixin, OAuth2Mixin):

    _OAUTH_ACCESS_TOKEN_URL = "https://open.t.qq.com/cgi-bin/oauth2/access_token"
    _OAUTH_AUTHORIZE_URL = "https://open.t.qq.com/cgi-bin/oauth2/authorize"
    _OAUTH_GETUSER_URL = "http://open.t.qq.com/api/user/info" # 获取用户信息
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, redirect_uri=None, client_id=None,
                           client_secret=None, extra_params=None):
        args = {
            "redirect_uri": redirect_uri,
            "client_id": client_id
        }
        if extra_params:
            args.update(extra_params)
        self.redirect(
            # QQ微博不能直接使用concat，需要解码url
            urllib.unquote(url_concat(self._OAUTH_AUTHORIZE_URL, args))) 

    def get_authenticated_user(self, redirect_uri, client_id, client_secret,
                               code, openkey, callback, extra_fields=None):

        http = httpclient.AsyncHTTPClient()
        args = {
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "extra_params": {"grant_type": "authorization_code"},
            }
        post_args = args.copy()
        post_args.update({"grant_type": "authorization_code"})

        fields = set(['data'])
        if extra_fields:
            fields.update(extra_fields)
        http.fetch(
        self._oauth_request_token_url(**args),
            method="POST",
            body=urllib.urlencode(post_args),
            callback=self.async_callback(self._on_access_token, redirect_uri,
                client_id, client_secret, openkey, callback, fields))

    def _on_access_token(self, redirect_uri, client_id, client_secret, openkey, 
                         callback, fields, response):
        if response.error:
            logging.warning('Weibo auth error: %s' % str(response))
            callback(None)
            return
        json = escape.parse_qs(response.body)
        session = {
            "access_token": json["access_token"],
            "expires": json.get("expires_in"),
            "openid": ''.join(json.get("openid")),
        }

        self.weibo_request(
            client_id, session["openid"], openkey, 
            callback=self.async_callback(
                self._on_get_user_info, callback, session, fields),
            access_token=session["access_token"],
            fields=",".join(fields)
        )

    def _on_get_user_info(self, callback, session, fields, user):
        if user is None:
            callback(None)
            return

        fieldmap = {}
        for field in fields:
            fieldmap[field] = user.get(field)

        fieldmap.update({"access_token": session["access_token"], "session_expires": session.get("expires")})
        callback(fieldmap)

    def weibo_request(self, client_id, openid, openkey, callback, 
            access_token=None, **args):
        http = httpclient.AsyncHTTPClient()
        get_args = {
            "format": "json",
            "sig":"exLAAn3qYWhlm13yjz+yAxc5924=", #这是QQ微博要求的字段
            "appid": client_id,
            "openid": openid,
            "openkey": openkey,
            "wbversion": 1, #这是QQ微博要求的字段
            }

        url = url_concat(self._OAUTH_GETUSER_URL, get_args)
        callback = self.async_callback(self._on_weibo_request, callback)
        http.fetch(url, callback=callback)

    def _on_weibo_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))
