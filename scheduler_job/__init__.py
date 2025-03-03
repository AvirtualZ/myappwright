import random
from datetime import datetime, timedelta


class Scheduler:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def add_tomorrow_job(self, func, hour=random.randint(2, 8), minute=random.randint(1, 59)):
        # 计算明天的时间
        tomorrow = datetime.now() + timedelta(days=1)
        run_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # 添加一次性任务
        self.scheduler.add_job(func, 'date', run_date=run_time)
        # 启动调度器
        print(f"任务已安排，将在 {run_time} 执行...")
