                                                          Python3.5协程学习研究



转：https://thief.one/2018/06/21/1/


Python3.5协程学习研究
发表于 2018-06-21   |   分类于 编程之道   |   热度 1216 ℃

　　 之前有研究过python协程相关的知识，但一直没有进行深入探究。平常工作中使用的也还是以python2为主，然而最近的项目需要使用python3协程相关的内容，因此凑出时间学习了一番python3的协程语法。
　　 本篇主要以介绍python3.5的async/await协程语法为主，因为这种语法看上去很别扭，不容易理解。如果对python协程基础不是很了解，建议可以先看此篇：Python协程。

协程函数（异步函数）
　　 我们平常使用最多的函数都是同步函数，即不同函数执行是按顺序执行的。那么什么是异步函数呢？怎么创建异步函数？怎么在异步函数之间来回切换执行？不急，请往下看。

创建协程函数
先来看下普通函数：
def test1():
    print("1")
    print("2")
def test2():
    print("3")
    print("4")
a = test1()
b = test2()
print(a,type(a))
print(b,type(b))

运行以上代码得到结果：
1
2
3
4
None <class 'NoneType'>
None <class 'NoneType'>
说明：程序顺序执行了test1、test2函数，在调用函数的时候就自动进入了函数体，并执行了函数的内容。

然后使用async关键词将普通函数变成协程函数，即异步函数：
async def test1():
    print("1")
    print("2")
async def test2():
    print("3")
    print("4")
print(test1())
print(test2())

运行以上代码得到结果：
<coroutine object test1 at 0x109f4c620>
asyncio_python3_test.py:16: RuntimeWarning: coroutine 'test1' was never awaited
  print(test1())
<coroutine object test2 at 0x109f4c620>
asyncio_python3_test.py:17: RuntimeWarning: coroutine 'test2' was never awaited
  print(test2())
说明：忽略结果中的告警，可以看到调用函数test1、test2的时候，并没有进入函数体且执行函数内容，而是返回了一个coroutine（协程对象）。

除了函数外，类的方法也可以使用async关键词将其变成协程方法：
class test:
    async def run(self):
        print("1")
执行协程函数
　　 前面我们成功创建了协程函数，并且在调用函数的时候返回了一个协程对象，那么怎么进入函数体并执行函数内容呢？类似于生成器，可以使用send方法执行函数，修改下前面的代码：

async def test1():
    print("1")
    print("2")
async def test2():
    print("3")
    print("4")
a = test1()
b = test2()
a.send(None)
b.send(None)

运行以上代码得到以下结果：
1
2
Traceback (most recent call last):
  File "asyncio_python3_test.py", line 19, in <module>
    a.send(None)
StopIteration
sys:1: RuntimeWarning: coroutine 'test2' was never awaited
　　 说明：程序先执行了test1协程函数，当test1执行完时报了StopIteration异常，这是协程函数执行完饭回的一个异常，我们可以用try except捕捉，来用判断协程函数是否执行完毕。

async def test1():
    print("1")
    print("2")
async def test2():
    print("3")
    print("4")
a = test1()
b = test2()
try:
    a.send(None) # 可以通过调用 send 方法，执行协程函数
except StopIteration as e:
    print(e.value)
    # 协程函数执行结束时会抛出一个StopIteration 异常，标志着协程函数执行结束，返回值在value中
    pass
try:
    b.send(None) # 可以通过调用 send 方法，执行协程函数
except StopIteration:
    print(e.value)
    # 协程函数执行结束时会抛出一个StopIteration 异常，标志着协程函数执行结束，返回值在value中
    pass
    
运行以上代码得到以下结果：
1
2
3
4
　　 说明：程序先执行了test1函数，等到test1函数执行完后再执行test2函数。从执行过程上来看目前协程函数与普通函数没有区别，并没有实现异步函数，那么如何交叉运行协程函数呢？

交叉执行协程函数（await）
　　 通过以上例子，我们发现定义协程函数可以使用async关键词，执行函数可以使用send方法，那么如何实现在两个协程函数间来回切换执行呢？这里需要使用await关键词，修改一下代码：

import asyncio
async def test1():
    print("1")
    await asyncio.sleep(1) # asyncio.sleep(1)返回的也是一个协程对象
    print("2")
async def test2():
    print("3")
    print("4")
a = test1()
b = test2()
try:
    a.send(None) # 可以通过调用 send 方法，执行协程函数
except StopIteration:
    # 协程函数执行结束时会抛出一个StopIteration 异常，标志着协程函数执行结束
    pass
try:
    b.send(None) # 可以通过调用 send 方法，执行协程函数
except StopIteration:
    pass

运行以上函数得到以下结果：
1
3
4
　　 说明：程序先执行test1协程函数，在执行到await时，test1函数停止了执行（阻塞）；接着开始执行test2协程函数，直到test2执行完毕。从结果中，我们可以看到，直到程序运行完毕，test1函数也没有执行完（没有执行print(“2”)），那么如何使test1函数执行完毕呢？可以使用asyncio自带的方法循环执行协程函数。

await与阻塞
　　 使用async可以定义协程对象，使用await可以针对耗时的操作进行挂起，就像生成器里的yield一样，函数让出控制权。协程遇到await，事件循环将会挂起该协程，执行别的协程，直到其他的协程也挂起或者执行完毕，再进行下一个协程的执行，协程的目的也是让一些耗时的操作异步化。

注意点：await后面跟的必须是一个Awaitable对象，或者实现了相应协议的对象，查看Awaitable抽象类的代码，表明了只要一个类实现了await方法，那么通过它构造出来的实例就是一个Awaitable，并且Coroutine类也继承了Awaitable。

自动循环执行协程函数
　　 通过前面介绍我们知道执行协程函数需要使用send方法，但一旦协程函数执行过程中切换到其他函数了，那么这个函数就不在被继续运行了，并且使用sned方法不是很高效。那么如何在执行整个程序过程中，自动得执行所有的协程函数呢，就如同多线程、多进程那样，隐式得执行而不是显示的通过send方法去执行函数。

事件循环方法
前面提到的问题就需要用到事件循环方法去解决，即asyncio.get_event_loop方法，修改以上代码如下：

import asyncio
async def test1():
    print("1")
    await test2()
    print("2")
async def test2():
    print("3")
    print("4")
loop = asyncio.get_event_loop()
loop.run_until_complete(test1())

运行以上代码得到以下结果：
1
3
4
2
说明：asyncio.get_event_loop方法可以创建一个事件循环，然后使用run_until_complete将协程注册到事件循环，并启动事件循环。

task任务
　　 由于协程对象不能直接运行，在注册事件循环的时候，其实是run_until_complete方法将协程包装成为了一个任务（task）对象。所谓task对象是Future类的子类，保存了协程运行后的状态，用于未来获取协程的结果。我们也可以手动将协程对象定义成task，修改以上代码如下：

import asyncio
async def test1():
    print("1")
    await test2()
    print("2")
async def test2():
    print("3")
    print("4")
loop = asyncio.get_event_loop()
task = loop.create_task(test1())
loop.run_until_complete(task)
　　 说明：前面说到task对象保存了协程运行的状态，并且可以获取协程函数运行的返回值，那么具体该如何获取呢？这里可以分两种方式，一种需要绑定回调函数，另外一种则直接在运行完task任务后输出。值得一提的是，如果使用send方法执行函数，则返回值可以通过捕捉StopIteration异常，利用StopIteration.value获取。

直接输出task结果
当协程函数运行结束后，我们需要得到其返回值，第一种方式就是等到task状态为finish时，调用task的result方法获取返回值。

import asyncio
async def test1():
    print("1")
    await test2()
    print("2")
    return "stop"
async def test2():
    print("3")
    print("4")
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(test1())
loop.run_until_complete(task)
print(task.result())

运行以上代码得到以下结果：
1
3
4
2
stop
回调函数
　　 获取返回值的第二种方法是可以通过绑定回调函数，在task执行完毕的时候可以获取执行的结果，回调的最后一个参数是future对象，通过该对象可以获取协程返回值。

import asyncio
async def test1():
    print("1")
    await test2()
    print("2")
    return "stop"
async def test2():
    print("3")
    print("4")
def callback(future):
    print('Callback:',future.result()) # 通过future对象的result方法可以获取协程函数的返回值
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(test1()) # 创建task，test1()是一个协程对象
task.add_done_callback(callback) # 绑定回调函数
loop.run_until_complete(task)

运行以上代码得到以下结果：
1
3
4
2
Callback: stop

如果回调函数需要接受多个参数，可以通过偏函数导入，修改代码如下：
import asyncio
import functools
async def test1():
    print("1")
    await test2()
    print("2")
    return "stop"
async def test2():
    print("3")
    print("4")
def callback(param1,param2,future):
    print(param1,param2)
    print('Callback:',future.result())
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(test1())
task.add_done_callback(functools.partial(callback,"param1","param2"))
loop.run_until_complete(task)
说明：回调函数中的future对象就是创建的task对象。

future对象
　　 future对象有几个状态：Pending、Running、Done、Cancelled。创建future的时候，task为pending，事件循环调用执行的时候当然就是running，调用完毕自然就是done，如果需要停止事件循环，就需要先把task取消，可以使用asyncio.Task获取事件循环的task。

协程停止
　　 前面介绍了使用事件循环执行协程函数，那么怎么停止执行呢？在停止执行协程前，需要先取消task，然后再停止loop事件循环。

import asyncio
async def test1():
    print("1")
    await asyncio.sleep(3)
    print("2")
    return "stop"
tasks = [
    asyncio.ensure_future(test1()),
    asyncio.ensure_future(test1()),
    asyncio.ensure_future(test1()),
]
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.wait(tasks))
except KeyboardInterrupt as e:
    for task in asyncio.Task.all_tasks():
        task.cancel()
    loop.stop()
    loop.run_forever()
finally:
    loop.close()
运行以上代码，按ctrl+c可以结束执行。

本文中用到的一些概念及方法
event_loop事件循环：程序开启一个无限的循环，当把一些函数注册到事件循环上时，满足事件发生条件即调用相应的函数。
coroutine协程对象：指一个使用async关键字定义的函数，它的调用不会立即执行函数，而是会返回一个协程对象，协程对象需要注册到事件循环，由事件循环调用。
task任务：一个协程对象就是一个原生可以挂起的函数，任务则是对协程进一步封装，其中包含任务的各种状态。
future：代表将来执行或没有执行的任务的结果，它和task上没有本质的区别
async/await关键字：python3.5用于定义协程的关键字，async定义一个协程，await用于挂起阻塞的异步调用接口。
并发与并行
　　 并发通常指有多个任务需要同时进行，并行则是同一时刻有多个任务执行。用多线程、多进程、协程来说，协程实现并发，多线程与多进程实现并行。

asyncio协程如何实现并发
　　 asyncio想要实现并发，就需要多个协程来完成任务，每当有任务阻塞的时候就await，然后其他协程继续工作，这需要创建多个协程的列表，然后将这些协程注册到事件循环中。这里指的多个协程，可以是多个协程函数，也可以是一个协程函数的多个协程对象。

import asyncio
async def test1():
    print("1")
    await asyncio.sleep(1)
    print("2")
    return "stop"

a = test1()
b = test1()
c = test1()

tasks = [
    asyncio.ensure_future(a),
    asyncio.ensure_future(b),
    asyncio.ensure_future(c),
]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks)) # 注意asyncio.wait方法
for task in tasks:
    print("task result is ",task.result())

运行以上代码得到以下结果：
1
1
1
2
2
2
task result is  stop
task result is  stop
task result is  stop
说明：代码先是定义了三个协程对象，然后通过asyncio.ensure_future方法创建了三个task，并且将所有的task加入到了task列表，最终使用loop.run_until_complete将task列表添加到事件循环中。

协程爬虫
　　 前面介绍了如何使用async与await创建协程函数，使用asyncio.get_event_loop创建事件循环并执行协程函数。例子很好地展示了协程并发的高效，但在实际应用场景中该如何开发协程程序？比如说异步爬虫。我尝试用requests模块、urllib模块写异步爬虫，但实际操作发现并不支持asyncio异步，因此可以使用aiohttp模块编写异步爬虫。

aiohttp实现

import asyncio
import aiohttp
async def run(url):
    print("start spider ",url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(resp.url)
url_list = ["https://thief.one","https://home.nmask.cn","https://movie.nmask.cn","https://tool.nmask.cn"]
tasks = [asyncio.ensure_future(run(url)) for url in url_list]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
运行以上代码得到以下结果：

start spider  https://thief.one
start spider  https://home.nmask.cn
start spider  https://movie.nmask.cn
start spider  https://tool.nmask.cn
https://movie.nmask.cn
https://home.nmask.cn
https://tool.nmask.cn
https://thief.one
说明：aiohttp基于asyncio实现，既可以用来写webserver，也可以当爬虫使用。

requests实现
　　 由于requests模块阻塞了客户代码与asycio事件循环的唯一线程，因此在执行调用时，整个应用程序都会冻结，但如果一定要用requests模块，可以使用事件循环对象的run_in_executor方法，通过run_in_executor方法来新建一个线程来执行耗时函数，因此可以这样修改代码实现：

import asyncio
import requests
async def run(url):
    print("start ",url)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)
    print(response.url)
    
url_list = ["https://thief.one","https://home.nmask.cn","https://movie.nmask.cn","https://tool.nmask.cn"]
tasks = [asyncio.ensure_future(run(url)) for url in url_list]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
如果要给requests带上参数，可以使用functools：


import asyncio
import requests
import functools
async def run(url):
    print("start ",url)
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None,functools.partial(requests.get,url=url,params="",timeout=1))
    except Exception as e:
        print(e)
    else:
        print(response.url)
url_list = ["https://thief.one","https://home.nmask.cn","https://movie.nmask.cn","https://tool.nmask.cn"]
tasks = [asyncio.ensure_future(run(url)) for url in url_list]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
asyncio中使用阻塞函数
　　 如同前面介绍如何在asyncio中使用requests模块一样，如果想在asyncio中使用其他阻塞函数，该怎么实现呢？虽然目前有异步函数支持asyncio，但实际问题是大部分IO模块还不支持asyncio。

阻塞函数在asyncio中使用的问题
　　 阻塞函数(例如io读写，requests网络请求)阻塞了客户代码与asycio事件循环的唯一线程，因此在执行调用时，整个应用程序都会冻结。

解决方案
　　 这个问题的解决方法是使用事件循环对象的run_in_executor方法。asyncio的事件循环在背后维护着一个ThreadPoolExecutor对象，我们可以调用run_in_executor方法，把可调用对象发给它执行，即可以通过run_in_executor方法来新建一个线程来执行耗时函数。

run_in_executor方法

AbstractEventLoop.run_in_executor(executor, func, *args)
executor 参数应该是一个 Executor 实例。如果为 None，则使用默认 executor。
func 就是要执行的函数
args 就是传递给 func 的参数

实际例子（使用time.sleep()）：
import asyncio
import time
async def run(url):
    print("start ",url)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None,time.sleep,1)
    except Exception as e:
        print(e)
    print("stop ",url)
url_list = ["https://thief.one","https://home.nmask.cn","https://movie.nmask.cn","https://tool.nmask.cn"]
tasks = [asyncio.ensure_future(run(url)) for url in url_list]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
运行以上代码得到以下函数：


start  https://thief.one
start  https://home.nmask.cn
start  https://movie.nmask.cn
start  https://tool.nmask.cn
stop  https://thief.one
stop  https://movie.nmask.cn
stop  https://home.nmask.cn
stop  https://tool.nmask.cn
说明：有了run_in_executor方法，我们就可以使用之前熟悉的模块创建协程并发了，而不需要使用特定的模块进行IO异步开发。

参考
https://www.oschina.net/translate/playing-around-with-await-async-in-python-3-5
https://www.jianshu.com/p/b5e347b3a17c
https://zhuanlan.zhihu.com/p/27258289
https://juejin.im/entry/5aabb949f265da23a04951df


在此特别感谢作者，请大家给与支持。




