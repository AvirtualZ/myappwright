import asyncio
import datetime
from DataRecorder import Recorder
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import os
import random
from loguru import logger

import more_login
import repo
import tasks
from thread_manager.exector import Executors
from utils import logutils

load_dotenv()

BROWSER_INDEX = int(os.getenv('BROWSER_INDEX'))
RUN_SIZE = int(os.getenv('RUN_SIZE'))
thread = int(os.getenv('THREAD_CNT'))


async def worker(browser_id: int):
    logger.info(f"do_work================={browser_id}")
    async with async_playwright() as playwright:
        try:
            cdp_url = more_login.process_environment_byid(browser_id)
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            # TODO 接管成功  继续执行任务
            await tasks.do_task(context, browser_id, task_name)
            run_record.add_data(browser_id)
            run_record.record()
        except Exception as error0:
            logger.error(f'{error0}============{browser_id}')
            error_record.add_data((browser_id, error0))
            error_record.record()
        finally:
            try:
                more_login.close_environment(None, browser_id=browser_id)
            except Exception as e2:
                logger.error(f'browser.close()======{e2}======{browser_id}')


async def main():
    task_ids = []
    for i in range(BROWSER_INDEX, BROWSER_INDEX + RUN_SIZE):
        if i in run_list or str(i) in run_list:
            continue
        task_ids.append(i)
    random.shuffle(task_ids)
    for i in task_ids:
        Executors.submit_async(task_name, worker, i)
    logger.info(f"并行任务：{Executors.show_all()}")
    Executors.shutdown_all()


if __name__ == '__main__':
    tasklist = [
        "init_outlook",
        "x"]
    task_name = tasklist[int(input('请输入任务序号：')) or 0]
    logger.add(f"./log/{task_name}-{datetime.date.today()}.log")
    logger.info(f"任务名称:{task_name}")
    run_day_key = '2025-02-26'
    data_path = f'./log/run_logs/{task_name}-{run_day_key}.txt'
    run_list = logutils.get_list_from_file(data_path)
    run_record = Recorder(data_path)
    error_path = f'./log/run_logs/error-{run_day_key}.xlsx'
    error_record = Recorder(error_path)
    asyncio.run(main())
