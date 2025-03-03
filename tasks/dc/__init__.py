import asyncio
import imaplib

import email
import re
from typing import List

from loguru import logger
from playwright.async_api import BrowserContext, Page, Frame

from datetime import datetime, timedelta

from sqlalchemy import func

import repo
from repo import warpcast
import utils
from repo.corpora import Corpora
from repo.user import User
from page_auto import PageAuto, actions

from email.header import decode_header

'''
dc活跃

'''

DC_INVITE_URL = "https://discord.com/invite/m9GypwYj"  # dc邀请链接按情况更改
DC_CHANNEL_URL = "https://discord.com/channels/1343759892716064880/1343759893659779136"  # dc邀请链接按情况更改


async def do_invite(context: BrowserContext, browser_id):
    logger.info(f"开始执行每日dc_invite任务，环境ID: {browser_id}")
    page = await utils.get_page_by_url(context, DC_INVITE_URL)
    if await PageAuto(page, context, browser_id).get_by_role('button', name='Accept Invite').click():
        await page.goto(DC_CHANNEL_URL)
        await asyncio.sleep(5)


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行每日dc养号任务，环境ID: {browser_id}")
    page = await utils.get_page_by_url(context, DC_CHANNEL_URL)
    for i in range(60):
        textbox = await page.get_by_role('textbox')
        corpora_data = warpcast.session.query(Corpora).filter_by(used=0) \
            .order_by(func.random()).first()
        if await actions.fill(textbox, corpora_data.context, browser_id):
            await asyncio.sleep(3)
            await textbox.press('Enter')

        await asyncio.sleep(5)
