import asyncio

from loguru import logger
from playwright.async_api import BrowserContext, Page
import datetime
import email
import imaplib
import random
from email.header import decode_header
import utils
from page_auto import PageAuto


async def sign_in(context: BrowserContext, page: Page, browser_id, user):
    if await page.query_selector('input[name="loginfmt"]'):
        logger.info(f"用户未登录，开始进行登录操作，环境ID: {browser_id}")
        login_input = page.locator('input[name="loginfmt"]')
        logger.info(f"输入邮箱地址：{user.email}，环境ID: {browser_id}")
        # 输入邮箱地址
        await login_input.fill(user.email)
        await asyncio.sleep(1)
        await login_input.press("Enter")

        # 等待页面加载，这里简单等待 2 秒，可以根据实际情况调整
        if await page.wait_for_selector("input[type='password']"):
            password_input = page.locator('input[type="password"]')
            # 输入密码
            await password_input.fill(user.password)
            await asyncio.sleep(1)
            await password_input.press("Enter")
            await utils.wait_element_change(page, "input[type='password']")


async def accrue(context: BrowserContext, page: Page, browser_id, user):
    if "https://account.live.com/tou/accrue?" in page.url \
            and await page.query_selector('input[type="submit"]'):
        old_url = page.url
        logger.info(f"{user.email}进入更新服务条款流程，环境ID: {browser_id}")
        await page.locator('input[type="submit"]').click()
        await utils.wait_page_change(page, old_url)


async def privacy(context: BrowserContext, page: Page, browser_id, user):
    if 'https://privacynotice.account.microsoft.com/' in page.url:
        old_url = page.url
        await PageAuto(page, context, browser_id).get_by_role('button').click()
        logger.info(f"{user.email}进入隐私政策流程，环境ID: {browser_id}")
        await utils.wait_page_change(page, old_url)


async def keep_login(context: BrowserContext, page: Page, browser_id, user):
    selector_key = '#checkboxField'
    if await page.query_selector(selector_key):
        logger.info(f"{user.email}进入保持登录流程，环境ID: {browser_id}")
        await page.locator(selector_key).click()
        await page.locator('input[type="submit"]').click()
        await utils.wait_element_change(page, selector_key)


async def add_proofs_email(context: BrowserContext, page: Page, browser_id, user):
    if await page.query_selector('#iProofsContainer'):
        logger.debug("Outlook 绑定辅助邮箱")
        await page.fill('#EmailAddress', user.email_assist)
        await asyncio.sleep(1)
        await page.press("Enter")

        try:
            await page.wait_for_load_state("networkidle")
        except:
            await asyncio.sleep(1)
        code = None
        for _ in range(10):
            code = get_firstmail_code(user.email_assist, user.password_assist)
            logger.info(f'获取辅助邮箱验证码：{code}')
            if code:
                break
            else:
                logger.debug(f"等待 Firstmail 邮件，环境ID: {browser_id}")
                await page.wait_for_timeout(3000)
        if code:
            await page.fill('input[type="tel"]', code)
            await asyncio.sleep(1)
            await page.press("Enter")
            try:
                await page.wait_for_load_state("networkidle")
            except:
                await asyncio.sleep(1)


def get_firstmail_code(username: str, password: str, search_param='(UNSEEN)', timeout=3):
    # 邮箱的域名
    host = 'imap.firstmail.ltd'
    # 创建一个IMAP4_SSL对象，用于SSL加密连接
    mail = imaplib.IMAP4_SSL(host)
    # 登录邮箱
    mail.login(username, password)

    # 搜索收件箱和垃圾邮件文件夹中的最新邮件
    for folder in ["INBOX", "Junk"]:
        mail.select(folder)
        status, messages = mail.search(None, search_param)

        if status != "OK":
            continue

        mail_ids = messages[0].split()
        if not mail_ids:
            continue

        # 从最新邮件开始
        for mail_id in reversed(mail_ids):
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if timeout > 0:
                        date_tuple = email.utils.parsedate_tz(msg["Date"])
                        if date_tuple:
                            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                            if local_date < datetime.now() - datetime.timedelta(minutes=timeout):
                                continue

                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    if "Microsoft account security code" not in subject:
                        continue
                    print("Subject:", subject)

                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if "attachment" not in content_disposition:
                                if content_type == "text/html":
                                    body = part.get_payload(decode=True).decode()

                                    a_list = body.split('color:#2a2a2a;">')
                                    for a in a_list:
                                        if "</span>" in a:
                                            mail.logout()
                                            return a[:a.find('</span>')]
                    else:
                        body = msg.get_payload(decode=True).decode()

                        a_list = body.split('color:#2a2a2a;">')
                        for a in a_list:
                            if "</span>" in a:
                                mail.logout()
                                return a[:a.find('</span>')]

    mail.logout()
    return None
