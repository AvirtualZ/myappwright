import asyncio
import random

from loguru import logger
from playwright.async_api import BrowserContext, Page
from sqlalchemy import func

import config
import repo
import utils
from page_auto import PageAuto
from repo.corpora import Corpora


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行每日X养号任务，环境ID: {browser_id}")
    x_page: Page = await utils.get_page_by_url(context, 'https://x.com')
    await x_page.wait_for_timeout(10000)
    if await PageAuto(x_page, context, browser_id) \
            .get_by_test_id('retweet').click():
        await PageAuto(x_page, context, browser_id) \
            .get_by_test_id('retweetConfirm').click(custom_delay=random.randint(3, 5))
        logger.info(f"每日X养号[转帖]任务执行成功，环境ID: {browser_id}")

    if await PageAuto(x_page, context, browser_id) \
            .get_by_test_id('like').click(custom_delay=random.randint(3, 5)):
        logger.info(f"每日X养号[喜欢]任务执行成功，环境ID: {browser_id}")
    # 发帖
    if random.randint(1, 3) == 3:
        corpora_data = repo.session.query(Corpora).order_by(func.random()).first()
        if corpora_data and corpora_data.context:
            logger.debug(f"获取发帖随机语料发帖: {corpora_data}========================={browser_id}")
            if await PageAuto(x_page, context, browser_id) \
                    .get_by_role('textbox').fill(corpora_data.context):
                if await PageAuto(x_page, context, browser_id) \
                        .get_by_test_id('tweetButtonInline').click(custom_delay=random.randint(1, 5)):
                    logger.info(f"每日X养号[发帖]任务执行成功，环境ID: {browser_id}")

    await utils.human_like_scroll(x_page)
    if not await PageAuto(x_page, context, browser_id) \
            .get_by_role('button', name='Follow').all_click():
        await PageAuto(x_page, context, browser_id) \
            .get_by_role('button', name='关注').all_click(timeout=3000)
    for follow_user in config.tw_follow_list:
        await x_page.goto(follow_user)
        await asyncio.sleep(random.randint(10, 20))
        if await PageAuto(x_page, context, browser_id) \
                .get_by_role('button', name='Follow').click():
            logger.info(f"每日X养号[关注]任务执行成功，环境ID: {browser_id}")
        elif await PageAuto(x_page, context, browser_id) \
                .get_by_role('button', name='关注').click(timeout=3000):
            logger.info(f"每日X养号[关注]任务执行成功，环境ID: {browser_id}")
        else:
            logger.error(f"每日X养号[关注]任务执行失败，环境ID: {browser_id}")
