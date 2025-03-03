import asyncio
import traceback

from playwright.async_api import async_playwright, Playwright

import more_login
import repo
import tasks
from page_auto import PageAuto
from wallets.okx import OKXWallet


async def run(playwright: Playwright):
    try:
        cdp_url = 'http://127.0.0.1:9527'
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]

        okx = OKXWallet(context, password='Aa112211@', task_id=1)
        await okx.unlock()
        page = await context.new_page()
        await page.goto('https://lastodyssey.io/')

        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)
        await page.get_by_role('button', name='Connect').click()
        if await PageAuto(page, context, 1).get_by_text('Connect').click():
            if await PageAuto(page, context, 1).get_by_text('OKX Wallet').click():
                await okx.approve()
            if await PageAuto(page, context, 1).get_by_text('Sign Message').click():
                await okx.sign()
        print('env closed')

    except:
        error_msg = traceback.format_exc()
        print('run-error: ' + error_msg)


async def warpcast_run(playwright: Playwright):
    try:
        repo.init()
        cdp_url = more_login.process_environment_byid(1)
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]

        await tasks.do_task(context, 1, "account_login")
        print('env closed')

    except:
        error_msg = traceback.format_exc()
        print('run-error: ' + error_msg)


async def warpcast_run(playwright: Playwright):
    try:
        repo.init()
        cdp_url = more_login.process_environment_byid(1)
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]

        await tasks.do_task(context, 1, "account_login")
        print('env closed')

    except:
        error_msg = traceback.format_exc()
        print('run-error: ' + error_msg)


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == '__main__':
    asyncio.run(main())
