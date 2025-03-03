import asyncio

from loguru import logger
from playwright.async_api import Locator

delay = 2


async def cnt_locator(locator: Locator, task_id, logs, func_name=None, timeout=3000) -> int:
    logger.info(f'任务ID：{task_id}=============={func_name}:{logs}')
    ele_cnt = 0
    for i in range(3):
        ele_cnt = await locator.count()
        if ele_cnt > 0:

            break
        else:
            await asyncio.sleep(2)  # 等待几秒
    if ele_cnt == 0:
        logger.debug(f'任务ID：{task_id}=============={func_name}：加载失败 {logs} ')
    return ele_cnt


async def click(locator: Locator, task_id, logs=None, custom_delay=1, nth=0, timeout=3000, parent=False) -> bool:
    try:
        ele_cnt = await cnt_locator(locator, task_id, logs, "点击元素【click】")
        if ele_cnt == 0:
            return False
        if ele_cnt > 1:
            locator = locator.nth(nth)
        click_res = await click_handler(locator, timeout, task_id)
        if not click_res and parent:
            p = locator.locator("xpath=..")
            # 往上找10层
            l_cnt = 1
            while not await click_handler(p, timeout/10, task_id):
                if l_cnt > 10:
                    logger.error(f'点击元素【click】失败：{locator}=============={task_id}')
                    return False
                p = p.locator("xpath=..")
                l_cnt += 1
        await asyncio.sleep(delay + custom_delay)  # 等待几秒
        return True
    except Exception as error:
        logger.error(f'点击元素【click】失败：{error}=============={task_id}')
        return False


async def click_handler(locator: Locator, timeout, task_id):
    try:
        await locator.click(timeout=timeout)
        await asyncio.sleep(delay)  # 等待几秒
        return True
    except Exception as error:
        logger.debug(f'点击元素【click】失败：{locator}=============={task_id}')
        return False


async def all_click(locator, task_id, logs=None, custom_delay=1, timeout: float = None) -> bool:
    try:
        ele_cnt = await cnt_locator(locator, task_id, logs, "批量点击元素【all_click】")
        if ele_cnt == 0:
            return False
        locators = await locator.all()
        for li in locators:
            await li.click(timeout=timeout)
        await asyncio.sleep(delay + custom_delay)  # 等待几秒
        return True
    except Exception as error:
        logger.error(f'点击元素【click】失败：{error}=============={task_id}')
        return False


async def fill(locator, value, task_id, logs=None, custom_delay=0, nth=0) -> bool:
    try:
        ele_cnt = await cnt_locator(locator, task_id, logs, "输入元素【click】")
        if ele_cnt == 0:
            return False
        if ele_cnt > 1:
            locator = locator.nth(nth)
        await locator.fill(value)
        await asyncio.sleep(delay + custom_delay)  # 等待几秒
        return True
    except Exception as error:
        logger.error(f'输入元素【fill】失败：{error}=============={task_id}')
        return False
