import asyncio
import random

from loguru import logger
from playwright.async_api import BrowserContext, Page


async def get_page_by_url(context: BrowserContext, url) -> Page:
    for page in context.pages:
        if url in page.url:
            try:
                await page.wait_for_load_state('networkidle', timeout=60000)
            except Exception:
                logger.debug("等待页面加载")
            return page
    try:
        new_page = await context.new_page()
        await new_page.goto(url, wait_until='networkidle', timeout=60000)
    except Exception as error:
        logger.error(f'{error}')
        if url not in page.url:
            raise error
    await new_page.wait_for_timeout(3000)
    return new_page


async def page_goto(page: Page, href, timeout=3000):
    # href = href.replace('https://warpcast.com', '')
    await page.evaluate(f'window.location.href = "{href}"')
    await page.wait_for_timeout(timeout)


async def human_like_scroll(page: Page, scroll_steps=10):
    # 使用鼠标滚轮模拟更真实的滚动
    mouse = page.mouse

    for _ in range(scroll_steps):
        # 随机滚动距离（100-300像素）
        scroll_amount = random.randint(100, 300)

        # 随机滚动方向（5%概率向上滚动）
        if random.random() < 0.05:
            scroll_amount *= -1

        # 执行滚动
        await mouse.wheel(0, scroll_amount)

        # 随机等待时间（0.1-1.5秒）
        await asyncio.sleep(random.uniform(0.1, 1.5))

        # 随机暂停（10%概率中等暂停）
        if random.random() < 0.1:
            await asyncio.sleep(random.uniform(1.5, 3))

        # 检查是否到达页面底部
        current_position = await page.evaluate("window.scrollY + window.innerHeight")
        page_height = await page.evaluate("document.body.scrollHeight")
        if current_position >= page_height:
            break
