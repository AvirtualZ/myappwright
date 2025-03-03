import asyncio
import datetime
import email
import imaplib
import random
from email.header import decode_header

import pandas as pd
from loguru import logger
from playwright.async_api import BrowserContext, Page
import utils
from page_auto import PageAuto
from tasks.init_browser.actions import outlook_action
from utils import browserutils

actions = {
    "用户密码登录", outlook_action.sign_in,
    "更新服务条款", outlook_action.accrue,
    "隐私内容汇集", outlook_action.privacy,
    "账号保持登录", outlook_action.keep_login,
    "增加备用邮箱", outlook_action.add_proofs_email,
}


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行outlook初始化，环境ID: {browser_id}")
    user = browserutils.get_data(browser_id)
    page: Page = await utils.get_page_by_url(context, 'https://outlook.live.com/')
    # 获取页面是否有“登入”
    if await page.query_selector('[data-bi-ecn="Sign in"]'):
        logger.info(f"用户未登录，开始进行登录操作，环境ID: {browser_id}")
        page = await utils.get_page_by_url(context, 'https://login.live.com/')
        for i in range(30):
            await asyncio.sleep(5)
            if 'https://outlook.live.com' in page.url:
                logger.info(f"用户登录成功，环境ID: {browser_id}")
                break
            for action in actions:
                await action(context, page, browser_id, user)

    else:
        logger.info("用户已经登录 Outlook")


