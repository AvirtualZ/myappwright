import asyncio
import datetime
import email
import imaplib
import random
from email.header import decode_header

from loguru import logger
from playwright.async_api import BrowserContext, Page
from sqlalchemy import func

import config
import repo
import utils
from page_auto import PageAuto
from repo.browser_data.browser_user import BrowserUser
from repo.corpora import Corpora


async def do_task(context: BrowserContext, browser_id):
    logger.info(f"开始执行outlook初始化，环境ID: {browser_id}")
    user = repo.get_session().query(BrowserUser).filter_by(BrowserUser.browser_id == browser_id).first()
    page: Page = await utils.get_page_by_url(context, 'https://outlook.live.com/')
    # 获取页面是否有“登入”
    if await page.query_selector('[data-bi-ecn="Sign in"]'):
        logger.info(f"用户未登录，开始进行登录操作，环境ID: {browser_id}")
        # 判断登入是bnt还是input，如果未登录过页面有登入按钮，如果已登入过是输入username的input
        sign_in_flag = await PageAuto(page, context, browser_id).locator('a[data-bi-ecn="Sign in"]').click()
        if sign_in_flag:
            logger.info("点击【Sign in】按钮")
            page = await utils.get_page_by_url(context, 'https://login.live.com/')
            # 点击下一步按钮
            login_input = page.locator('input[type="email"]')
            if await login_input.count() > 0:
                logger.info(f"输入邮箱地址：{user.email}，环境ID: {browser_id}")
                # 输入邮箱地址
                await login_input.fill(user.email)
                await asyncio.sleep(1)
                await login_input.press("Enter")

                # 等待页面加载，这里简单等待 2 秒，可以根据实际情况调整
                await asyncio.sleep(2)
                password_input = page.locator('input[type="password"]')
                # 输入密码
                await password_input.fill(user.password)
                await asyncio.sleep(1)
                await password_input.press("Enter")
                await page.wait_for_load_state("networkidle")
            while await page.query_selector('#iProofsContainer'):
                logger.debug("Outlook 绑定辅助邮箱")
                await page.fill('#EmailAddress', user.email_assist)
                await asyncio.sleep(1)
                await page.press("Enter")

                await page.wait_for_load_state("networkidle")
                code = None
                for _ in range(10):
                    code = get_firstmail_code(user.email, user.password)
                    if code:
                        break
                    else:
                        logger.debug(f"等待 Firstmail 邮件，环境ID: {browser_id}")
                        await page.wait_for_timeout(3000)
                if code:
                    await page.fill('input[type="tel"]', code)
                    await asyncio.sleep(1)
                    await page.press("Enter")
                    await page.wait_for_load_state("networkidle")

            # 使用 await 关键字等待协程执行
            if 'https://outlook.live.com/' in page.url:
                logger.info(f"outlook 登录成功，任务ID: {browser_id}")
            else:
                raise Exception("Outlook 登录失败")
    else:
        logger.info("用户已经登录 Outlook")


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
