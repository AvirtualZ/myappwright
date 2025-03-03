"""
提供 线程池全局管理和控制
worker manager service => wms
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional
from threading import Lock as ThreadLock
from functools import partial
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
thread = int(os.getenv('THREAD_CNT', default=10))


class Executors:
    """
    线程池管理器, 单例模式， 用于管理线程池
    暂时不支持延迟任务提交
    """
    __instance: Optional['Executors'] = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Executors, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self._data: Dict[str, WmsThreadPoolExecutor] = {}
        self._lock = ThreadLock()

    def _executor(self, name: str, max_workers: int = 10, not_create: bool = True) -> ThreadPoolExecutor:
        if name not in self._data:
            if not not_create:
                return None  # 不创建新线程池
            with self._lock:
                if name not in self._data:  # 防止重复创建
                    self._data[name] = WmsThreadPoolExecutor(max_workers=max_workers)
        # 返回线程池
        return self._data[name]

    @classmethod
    def executor(cls, name: str, max_workers: int = 10, not_create: bool = True) -> ThreadPoolExecutor:
        """
        获取一个线程池，如果不存在则创建
        如果 not_create 为 True, 如果不存在线程池，会创建一个新的线程池， 否则返回 None
        """
        if name == "" or name is None:
            name = "__default__"
        return cls.__instance._executor(name, max_workers, not_create)

    def _shutdown(self, name: str):
        if name in self._data:
            with self._lock:
                self._data[name].shutdown()
                del self._data[name]

    @classmethod
    def shutdown(cls, name: str):
        """
        关闭一个线程池
        """
        cls.__instance._shutdown(name)

    def _shutdown_all(self):
        with self._lock:
            for name in self._data:
                self._data[name].shutdown()
            self._data.clear()

    @classmethod
    def shutdown_all(cls):
        """
        关闭所有线程池
        """
        cls.__instance._shutdown_all()

    def _show_all(self) -> Dict[str, dict]:
        data = {}
        for name in self._data:
            data[name] = self._task_stats(name)
        return data

    @classmethod
    def show_all(cls) -> Dict[str, int]:
        """
        显示所有线程池的状态
        """
        return cls.__instance._show_all()

    def _task_stats(self, name: str) -> dict:
        if name not in self._data:
            return None
        pool = self._data[name]
        queue_count = pool._work_queue.qsize()
        thread_max = pool._max_workers
        thread_run = len(pool._threads)
        thread_work = pool._thread_work.get_value()
        thread_idle = thread_run - thread_work
        # 由于信号问题， 这个值不准确，待定
        return {
            "queue_count": queue_count,
            "thread_max": thread_max,
            "thread_run": thread_run,
            "thread_work": thread_work,
            "thread_idle": thread_idle,
        }

    @classmethod
    def task_stats(cls, name: str) -> dict:
        """
        获取线程池的任务数量
        """
        return cls.__instance._task_count(name)

    def _task_count(self, name: str) -> int:
        if name not in self._data:
            return -1  # 线程池不存在
        pool = self._data[name]
        return pool._thread_work.get_value()

    @classmethod
    def task_count(cls, name: str) -> int:
        """
        获取线程池正在运行的任务数量
        -1, 表示线程池不存在
        """
        return cls.__instance._task_count(name)

    def _submit(self, name: str, fn, /, *args, **kwargs) -> Future:
        pool = self.executor(name, max_workers=thread)
        if asyncio.iscoroutinefunction(fn):
            # asyncio.run(async_function())
            # 是一个便捷函数，用于运行顶层的异步函数。它会创建一个新的事件循环，运行指定的异步函数，直到完成，然后关闭事件循环
            #
            # loop.run_until_complete(async_function()) # 多并发场景下，有的线程会出现异常
            # 用于在现有的事件循环中运行一个协程，直到它完成。它通常用于在已有事件循环的上下文中运行异步代码
            #
            # asyncio.run_coroutine_threadsafe(async_function(), loop) # 完全阻塞，无法运行
            # 用于在不同线程中安全地运行协程。它允许你从非事件循环线程中调度协程，并返回一个Future 对象，该对象可以用于等待协程的结果。
            #
            # 实际测试中，只有一种方式能够正常运行，其他两种方式都会报错
            return pool.submit(lambda: asyncio.run(fn(*args, **kwargs)))
        # 同步任务
        return pool.submit(fn, *args, **kwargs)

    @classmethod
    def submit(cls, name: str, fn, /, *args, **kwargs) -> Future:
        """
        提交一个任务到线程池
        参数:
           name (str): 线程池的名称
           fn (Callable): 需要在线程池中执行的函数
           *args: 传递给函数的非关键字参数
           **kwargs: 传递给函数的关键字参数
        返回:
        Future: 表示异步执行的结果对象
        Future 方法和说明:
          - cancel() -> bool: 尝试取消执行该任务
          - cancelled() -> bool: 返回任务是否被取消
          - running() -> bool: 返回任务是否正在运行
          - done() -> bool: 返回任务是否已经完成
          - result(timeout=None) -> Any: 返回任务的结果，如果任务没有完成则等待
          - exception(timeout=None) -> Optional[BaseException]: 返回任务引发的异常，如果有的话
          - add_done_callback(fn) -> None: 当任务完成时，调用指定的回调函数
          - set_running_or_notify_cancel() -> bool: 将任务状态设置为运行中或通知取消
          - set_result(result) -> None: 设置任务的结果
          - set_exception(exception) -> None: 设置任务的异常
        """
        return cls.__instance._submit(name, fn, *args, **kwargs)

    @classmethod
    def submit_once(self, fn, /, *args, **kwargs):
        """
        提交一个任务到线程池，只执行一次就释放线程池, 执行一次后，线程池就会被关闭
        """
        with ThreadPoolExecutor() as pool:
            return pool.submit(fn, *args, **kwargs)

    def _submit_async(self, name: str, fn, *args, loop: str = 'once', **kwargs):
        """
        loop:
            - once: 每次提交任务都会创建一个新的事件循环，执行完毕后关闭， 消耗点资源，是最理想的方式
            - curr: 使用当前运行的事件循环, 如果不存在则会抛出异常， 这种方式存在小概率无法正常结束线程池的问题
            - self: 创建一个持久的事件循环，用于提交任务，执行完毕后不关闭，这种方式会导致线程池不能接收其他类型的任务
        async_loop = asyncio.get_event_loop() or asyncio.get_running_loop()， 默认使用脚本入口的事件循环，即 self._loop
        asyncio.get_event_loop 获取当前线程的事件循环。如果没有事件循环，它会创建一个新的事件循环并返回。
        asyncio.get_running_loop 用于获取当前正在运行的事件循环。如果当前线程没有正在运行的事件循环，它会引发 RuntimeError。
        """
        _pool = self.executor(name, max_workers=thread)
        if not asyncio.iscoroutinefunction(fn):
            # 在异步环境中提交同步任务， 使用 run_in_executor 将同步任务提交到线程池中
            _loop = asyncio.get_running_loop()
            return _loop.run_in_executor(_pool, partial(fn, *args, **kwargs))
        if loop == "once":
            # 可以突破单线程极限，但是由于频繁创建事件循环，会导致系统时间开销, 但是只最理想的方式
            return _pool.submit(lambda: asyncio.run(fn(*args, **kwargs)))
        if loop == "curr":
            # 这种方式，由于loop问题，实际测试无法突破单线程极限, 这种方式存在小概率无法正常结束线程池的问题
            _loop = asyncio.get_running_loop()
            return _pool.submit(lambda: asyncio.run_coroutine_threadsafe(fn(*args, **kwargs), _loop).result())
        if loop == "self":
            # 可以突破单线程极限，但是由于不在关闭事件循环，会导致系统资源开销
            def warpper_fn():
                # 包装一个异步函数，用于提交到线程池, 避免重复创建事件循环导致的系统开销
                _loop = _get_running_loop()
                # 执行异步函数
                return _loop.run_until_complete(fn(*args, **kwargs))

            return _pool.submit(warpper_fn)
        # 其他抛出异常
        raise ValueError(f"loop parameter error: {loop}")

    @classmethod
    def submit_async(cls, name: str, fn, *args, loop: str = 'once', **kwargs):
        """
        在异步环境中提交任务， 这里强调提交者是一个异步环境（协程），无论提交的是异步线程还是同步线程，都将在其他线程中执行
        在同步环境中也可提交任务，可以通过 asyncio.run_until_complete(async_function()) 获取结果

        默认使用当前运行的事件循环，如果当前没有运行的事件循环，则会抛出异常
        参数:
            name (str): 线程池的名称
            fn (Callable): 需要在线程池中执行的函数
            *args: 传递给函数的非关键字参数
            loop: 事件循环的类型
                None: 默认使用当前运行的事件循环, 如果不存在则会抛出异常
                once: 每次提交任务都会创建一个新的事件循环，执行完毕后关闭
                self: 创建一个持久的事件循环，用于提交任务，执行完毕后不关闭，这种方式会导致线程池不能接收其他类型的任务
            **kwargs: 传递给函数的关键字参数
        在默认 loop = "once" 模式下，sumbit_async 和 sumbit 没用区别，仅限异步提交任务
        """
        return cls.__instance._submit_async(name, fn, *args, loop=loop, **kwargs)


# 单例模式声明
Executors()

# ==========================================================================================
__debug = False


def set_debug(debug: bool):
    global __debug
    __debug = debug


def is_debug():
    return __debug


def _get_running_loop():
    _loop = asyncio._get_running_loop()
    if _loop is None:
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def _del_running_loop():
    _loop = asyncio._get_running_loop()
    if _loop is not None:
        asyncio.set_event_loop(None)
        _loop.close()


class TaskItem:
    """
    任务对象，这里不提供内建的 sumbit 方法， 通过 PoolManager 提交任务
    """

    g: Dict[str, 'TaskItem'] = {}  # 任务全局管理

    def __init__(self, name: str, pool: str = "__default__"):
        self.name = name  # 任务名称
        self.pool = pool  # 任务线程池
        self.func = None  # 任务函数
        self.future: Future = None  # Future 对象
        self.state: str = None  # 任务状态, 便于优雅的结束任务
        self.data = {}  # 任务传递数据
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==========================================================================================
# 重新定义 ThreadPoolExecutor -> WmsThreadPoolExecutor
import types
import threading


class _AtomicCounter:
    def __init__(self, initial=0):
        self.__value = initial
        self.__lock = threading.Lock()

    def increment(self, num=1):
        with self.__lock:
            self.__value += num
            return self.__value

    def decrement(self, num=1):
        with self.__lock:
            self.__value -= num
            return self.__value

    def get_value(self):
        return self.__value


class _WorkItem(object):
    def __init__(self, counter, future, fn, args, kwargs):
        self.counter: _AtomicCounter = counter
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        self.counter.increment()
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            if is_debug():
                print(f"_WorkItem Exception: {exc}")
            self.counter.decrement()
            self = None
        else:
            self.future.set_result(result)
            self.counter.decrement()

    __class_getitem__ = classmethod(types.GenericAlias)


from concurrent.futures import _base, thread as _thread


class WmsThreadPoolExecutor(_thread.ThreadPoolExecutor):

    def __init__(self, max_workers: int = 10, thread_name_prefix: str = None, initializer=None, initargs=()):
        super().__init__(max_workers, thread_name_prefix, initializer, initargs)
        self._thread_work = _AtomicCounter(0)  # 工作中的线程的数量

    def submit(self, fn, /, *args, **kwargs):
        with self._shutdown_lock, _thread._global_shutdown_lock:
            if self._broken:
                raise _thread.BrokenThreadPool(self._broken)

            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            if _thread._shutdown:
                raise RuntimeError('cannot schedule new futures after '
                                   'interpreter shutdown')
            o = self._thread_work
            f = _base.Future()
            w = _WorkItem(o, f, fn, args, kwargs)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f

    submit.__doc__ = _base.Executor.submit.__doc__
