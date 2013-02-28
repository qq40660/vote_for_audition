#!/usr/bin/env python
#coding=utf-8
# 主程序
# Version 1 by Dongwm 2013/02/24

import os
import datetime
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
#import redis
from os import path as op

from tornadio2 import SocketConnection, TornadioRouter, SocketServer, event
import opermongo
import auth

ROOT = op.normpath(op.dirname(__file__))


class BaseHandler(tornado.web.RequestHandler):
    '''继承的子类，重载get_current_user'''
    def get_current_user(self):
        # 这里需要解码我设置的json格式的cookie
        json = self.get_secure_cookie("user")
        return tornado.escape.json_decode(json)  if json else None
         
class MainHandler(BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        img = tornado.escape.xhtml_escape(self.current_user["img"])
        name = tornado.escape.xhtml_escape(self.current_user["nick"])
        self.render("public/index.html", name=name, img=img) 

class VoteConnection(SocketConnection):
    @event
    def vote(self, c):
        self.db = opermongo.db(database='test')
        # 获取vote集合里面的赞成和反对票数实时展现到前端
        data = self.db.vote.find_one({},{'_id':0}) 

        return [data.get('approve', 0), data.get('refuse', 0)]

class WeiboAuthHandler(BaseHandler, auth.WeiboMixin):

    @tornado.web.asynchronous
    def get(self):
        next = self.get_argument("next",None)

        redirect_uri = '%s://%s%s' % (self.request.protocol, 
            self.request.host, self.settings["login_url"] )
        if self.get_argument("code", None):
             self.get_authenticated_user(
                redirect_uri=redirect_uri,
                client_id=self.settings["weibo_consumer_key"],
                client_secret=self.settings["weibo_consumer_secret"],
                code=self.get_argument("code"),
                openkey=self.get_argument("openkey"),
                callback=self.async_callback(self._on_auth),
                )
             return
        if next:
            self.authorize_redirect(
                redirect_uri=redirect_uri,
                client_id=self.settings["weibo_consumer_key"],
                client_secret=self.settings["weibo_consumer_secret"],
                extra_params={"response_type":"code"}
                )
        else:
            self.authorize_redirect(
                redirect_uri=redirect_uri,
                client_id=self.settings["weibo_consumer_key"],
                client_secret=self.settings["weibo_consumer_secret"]
                )

    def _on_auth(self, data):
        # 验证成功执行的回调
        if not data:
            raise tornado.web.HTTPError(500, "Weibo auth failed")
        user = data['data']
        name = user.get('name')
        img = '%s/120' % user.get('head')
        nick = user.get('nick')
        data = tornado.escape.json_encode(dict(name=name, img=img, nick=nick))
        self.set_secure_cookie("user", data)
        self.redirect("/")


class LogoutHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        # 用户退出，删除cookie
        self.clear_cookie("user")
        self.write('You are now logged out. '
                   'Click <a href="/">here</a> to log back in.')

class VoteHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        # 这里没有使用异步装饰器，因为ajax回调是异步的
        vote = int(self.get_argument('vote'))
        user = self.current_user["name"]
        # 获取用户的代理（假如没用代理，或者真实ip）
        proxy = self.request.headers.get("X-Real-Ip", "0.0.0.0") 
        real = self.request.remote_ip #获取用户真实ip
        # 检查用户是否已经投票了
        if self.application.db.voteusers.find_one({'user': user}):
            self.write('本用户已经投票了!')
            return self.finish() 
        # 检查这个ip是否投票了
        elif self.application.db.voteusers.find_one(
            {'real': real, 'proxy':proxy}
            ):
            self.write('本ip已经投票了!')
            return self.finish()
        # 新用户投票相关结果自增长1
        else:
            if vote:
                self.application.db.vote.update({}, {'$inc':{'refuse':1}})
            else:
                self.application.db.vote.update({}, {'$inc':{'approve':1}})
            # 新用户的微博帐号，ip记录下来
            self.application.adb.voteusers.insert(
                {'user': user, 'real':real, 'proxy':proxy}
                )
            # 回调显示投票成功
            self.write('投票已成功!')
        self.finish()

class Application(tornado.web.Application):
    
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/auth/login", WeiboAuthHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/vote", VoteHandler),
        ]
        settings = dict(
            static_path=os.path.join(os.path.dirname(__file__), "public"),
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
            xsrf_cookies=True,
            weibo_consumer_key='100689067',
            weibo_consumer_secret='1f54eff4858b924d090833d537335bd8',
            flash_policy_port = 843,
            flash_policy_file = op.join(ROOT, 'flashpolicy.xml'),
            socket_io_port = 8000,
        )
        VoteRouter = TornadioRouter(VoteConnection,
                            dict(enabled_protocols=['websocket', 'xhr-polling',
                                                    'jsonp-polling', 'htmlfile']))
        tornado.web.Application.__init__(self, VoteRouter.apply_routes(handlers), **settings)
        #self.redis = redis.StrictRedis()
        self.adb = opermongo.asyncdb(database='test')
        self.db = opermongo.db(database='test')

def main():

    SocketServer(Application(), xheaders=True)
    #tornado.options.parse_command_line()
    #http_server = tornado.httpserver.HTTPServer(Application())
    #http_server.listen(8000)
    #tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
