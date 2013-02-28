=========
vote_for_audition
=========



技术选型
------------

1. `Tornado <http://www.tornadoweb.org>`:因为其异步非阻塞的I/O模型，对大量websocet/Comet长轮询连接的维护
2. `mongodb <http://www.mongodb.org>`:选择数据库，主要就是考虑读写吞吐量、持久化、一致性以及延迟，而它尤其擅长web应用
3. `motor <https://github.com/mongodb/motor>`:`这是基于greenlet，mognodb公司同事写的python的异步驱动 <http://blog.mongodb.org/post/30927719826/motor-asynchronous-driver-for-mongodb-and-python>`, 使用pymongo会放弃异步优势，因为我要实时展示数据
4. `socket.io<http://socket.io>`: 这是一个JavaScript客户端库，类似于WebSocket，其提供了单个的API来连接远程服务器，异步地发送和接收消息。它支持主流浏览器和移动设备，并且可以在客户端不支持websock的时候帮你选择comet长轮询等方式
5. `tornadio2 <https://github.com/mrjoes/tornadio2>`:基于tornado实现的socket.io实时传输库
6. `nginx <http://nginx.org>`:Tornado的web服务器为单线程，一个Request如果阻塞了I/O，那么这个进程将一直挂起，既无法接受新的Request，也无法Finish正在阻塞的其它Request.虽然可以Spawn多个Tornado进程，但是进程这种重量级的东西，Spawn太多会消耗大量的内存资源.Tornado在生产中一般前面都要包一层nginx做反向代理(官网也是用nginx做代理)，用nginx来做静态文件等大数据量的I/O操作等.尤其是2y月19日发布公告，1.3版本已经支持websocket协议

使用方法
------------------

1. 安装依赖
sudo pip install -r requirements.txt 

2. 下载程序
git clone https://github.com/dongweiming/vote_for_audition.git

3. 启动程序
cd vote_for_audition
python server.py


-----------