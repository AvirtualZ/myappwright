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
from utils import logutils

x_token_list = logutils.get_list_from_file('x_token_list.txt')


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行每日X_token_login任务，环境ID: {browser_id}")
    page = await utils.get_page_by_url(context, "https://x.com")
    if await PageAuto(page, context, browser_id).get_by_test_id("loginButton").is_visible():
        logger.info(f"环境ID: {browser_id}未登录，执行登录流程")
        # 设置 Twitter 的 Cookie
        await context.add_cookies([
            {
                "name": "auth_token",
                "value": x_token_list[browser_id],
                "domain": ".twitter.com",
                "path": "/",
            },
            {
                "name": "auth_token",
                "value": x_token_list[browser_id],
                "domain": ".x.com",
                "path": "/",
            }
        ])
        await page.reload()
