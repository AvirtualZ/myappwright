"""
提供 线程全局管理和控制
worker manager service => wms
"""
import asyncio
from typing import Dict, Optional, Tuple
from threading import Thread, Lock as ThreadLock
from datetime import datetime
import ctypes


class Threads:
    """
    线程管理器， 单例模式， 管理全局线程
    """
    __instance: Optional['Threads'] = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Threads, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self._data: Dict[str, Tuple[Thread, dict]] = {}
        self._lock = ThreadLock()

    def _put(self, name: str, thread: Thread, **kwargs) -> int:
        if thread is None:
            return 1  # 无效线程
        if not thread.is_alive():
            return 2  # 线程已经结束
        if name in self._data and self._data[name][0].is_alive():
            return 3  # 已经存在, 且线程还在运行
        with self._lock:
            if kwargs is None:
                kwargs = {'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            elif 'created_at' not in kwargs:
                kwargs['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 添加线程
            self._data[name] = (thread, kwargs)
        return 0  # 增加成功

    @classmethod
    def put(cls, name: str, thread: Thread, /, **kwargs) -> int:
        """
        将一个线程放入全局线程池
        返回：错误码
        0: 成功
        1: 无效线程
        2: 线程已经结束
        3: 已经存在, 且线程还在运行
        """
        return cls.__instance._put(name, thread, **kwargs)

    def _get(self, name: str) -> Tuple[Thread, dict]:
        return self._data.get(name)

    @classmethod
    def get(cls, name: str) -> Tuple[Thread, dict]:
        """
        获取一个线程
        """
        return cls.__instance._get(name)

    def _start(self, name: str, daemon: bool | None, fn, /, *args, **kwargs) -> Tuple[Thread, dict]:
        thread = self.create_thread(daemon, fn, *args, **kwargs)
        thread.start()
        self.put(name, thread)  # 将线程放入全局线程, 以便于管理
        return self.get(name)

    @classmethod
    def start(cls, name: str, daemon: bool | None, fn, /, *args, **kwargs) -> Tuple[Thread, dict]:
        """
        使用线程方式提交线程池任务, 这里不能提供应用的详细信息，需要使用 update 更新
        """
        return cls.__instance._start(name, daemon, fn, *args, **kwargs)

    def _update(self, name: str, overwrite: bool = True, /, **kwargs):
        if name in self._data:
            with self._lock:
                if overwrite:
                    self._data[name][1] = kwargs  # 直接替换
                else:
                    self._data[name][1].update(kwargs)

    @classmethod
    def update(cls, name: str, overwrite: bool = True, /, **kwargs):
        """
        更新线程信息, 附加的信息
        """
        cls.__instance._update(name, overwrite, **kwargs)

    def _pop(self, name: str) -> Tuple[Thread, dict]:
        if name in self._data:
            with self._lock:
                return self._data.pop(name)
        return None

    @classmethod
    def pop(cls, name: str) -> Tuple[Thread, dict]:
        """
        删除一个线程
        """
        return cls.__instance.pop(name)

    def _stop(self, name: str, remove: bool = True) -> bool:
        if name in self._data:
            with self._lock:
                thread = self._data[name]
                if thread[0].is_alive():
                    self._async_raise(thread[0].ident, SystemExit, name + " (stop-one)/ " + thread[0].getName())
                if remove:
                    del self._data[name]  # 删除引用
            return True  # 停止成功
        return False

    @classmethod
    def stop(cls, name: str, remove: bool = True) -> bool:
        """
        停止一个线程
        """
        return cls.__instance._stop(name, remove)

    def _stop_all(self, remove: bool = True):
        with self._lock:
            for name in self._data:
                thread = self._data[name]
                if thread[0].is_alive():
                    self._async_raise(thread[0].ident, SystemExit, name + " (stop-all)/ " + thread[0].getName())
            if remove:
                self._data.clear()  # 清空数据

    @classmethod
    def stop_all(cls, remove: bool = True):
        """
        停止所有线程
        """
        cls.__instance._stop_all(remove)

    def _show_all(self) -> Dict[str, Tuple[bool, dict]]:
        return {name: (thread[0].is_alive(), thread[1]) for name, thread in self._data.items()}

    @classmethod
    def show_all(cls) -> Dict[str, Tuple[bool, dict]]:
        """
        显示所有线程
        """
        return cls.__instance._show_all()

    @classmethod  # @staticmethod & @classmethod
    def _async_raise(cls, tid, exctype, msg):
        """
        Raises an exception in the threads with id tid
        _async_raise 函数使用 ctypes 模块来向指定的线程抛出异常，从而强制终止线程。
        """
        if not isinstance(tid, int):
            raise TypeError("Only integers are allowed for thread_manager id")
        if not issubclass(exctype, BaseException):
            raise TypeError("Only subclasses of BaseException are allowed for exception type")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("Invalid thread_manager id")
        elif res != 1:
            # If it returns a number greater than one, there are issues, so we reset the exception
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        print(f"Thread {tid} has been forcefully stopped: {msg}")

    @classmethod
    def stop_thread(cls, thread: Thread):
        """
        Forcefully stops a thread_manager
        这不是一个好的做法，但是有时候确实需要这么做
        """
        cls._async_raise(thread.ident, SystemExit, thread.getName())  # 强制终止线程
        del thread  # 删除引用

    @classmethod
    def create_thread(cls, daemon: bool | None, fn, /, *args, **kwargs):
        """
        使用线程方式提交线程池任务
        构造方法
            __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None)
            初始化线程对象。
                group: 线程组，通常为 None。
                target: 线程要执行的目标函数。
                name: 线程名称。
                args: 传递给目标函数的位置参数元组。
                kwargs: 传递给目标函数的关键字参数字典。
                daemon: 如果为 True，则表示该线程是守护线程。
        实例方法
            start(self)
                启动线程，调用线程的 run 方法。
            run(self)
                线程的活动方法，默认调用 target 函数并传递 args 和 kwargs。可以在子类中重写此方法。
            join(self, timeout=None)
                阻塞调用线程，直到被调用线程终止或超时。
                timeout: 可选的超时时间（秒）。
            is_alive(self)
                返回线程是否仍然存活。
            getName(self)
                返回线程名称。
            setName(self, name)
                设置线程名称。
                name: 线程名称的属性，可以直接访问或设置。
            ident
                线程的标识符，线程启动后才会被设置。
            daemon
                线程是否为守护线程的属性，可以直接访问或设置。
            isDaemon(self)
                返回线程是否为守护线程。
            setDaemon(self, daemon)
                设置线程是否为守护线程。
        类方法
            current_thread()
                返回当前线程对象。
            main_thread()
                返回主线程对象。
            enumerate()
                返回当前所有存活的线程对象列表。
            active_count()
                返回当前存活的线程数量。
        """
        if asyncio.iscoroutinefunction(fn):
            # 运行的是一个协程，需要创建一个事件循环
            #   loop = asyncio.new_event_loop()
            #   asyncio.set_event_loop(loop)
            #   loop.run_until_complete(fn(*args, **kwargs))
            #   loop.close()
            # 等价于：asyncio.run(fn(*args, **kwargs))
            return Thread(target=lambda: asyncio.run(fn(*args, **kwargs)), daemon=daemon)
        # 如果运行的是同步函数
        return Thread(target=fn, args=args, kwargs=kwargs, daemon=daemon)


# 单例模式声明
Threads()
