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

dc_token_list = logutils.get_list_from_file('dc_token_list.txt')


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行每日dc_token_login任务，环境ID: {browser_id}")
    page = await utils.get_page_by_url(context, "https://discord.com/login")
    if await PageAuto(page, context, browser_id).locator('button[type="submit"]').is_visible():
        logger.info(f"环境ID: {browser_id}未登录，执行登录流程")
        # 注入 JavaScript 代码
        script = """
        function login(token) {
            setInterval(() => {
                document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"${token}"`
            }, 50);
            setTimeout(() => {
                location.reload();
            }, 2500);
        }
        """
        await page.evaluate(script + f'\nlogin("{dc_token_list[browser_id]}")')
        logger.info(f"环境ID: {browser_id}开始执行dc登录流程")
