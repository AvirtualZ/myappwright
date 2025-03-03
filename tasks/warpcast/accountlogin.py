import asyncio
import imaplib

import email
import re
from typing import List

from DataRecorder import Recorder
from loguru import logger
from playwright.async_api import BrowserContext, Page, Frame

from datetime import datetime, timedelta
import repo
from repo import warpcast
import utils
from repo.user import User
from page_auto import PageAuto, actions

from email.header import decode_header

'''
farcaster 邮箱登录 链接确认              
登录流程：
    1、根据user.email_type判断要访问的邮箱域名
    2、获取登录账号密码user.email+password
    3、

'''
ERR_URL = f'./run_logs/error_mail.xlsx'


async def do_task(context: BrowserContext, browser_id) -> bool:
    logger.info(f"开始执行登录任务，环境ID: {browser_id}")
    task_vo: User = await warpcast.find_user_by_browser_id(browser_id)
    return await do_task_handler(context, task_vo)


async def do_task_handler(context: BrowserContext, task_vo, warpcast_login=True) -> bool:
    if task_vo.email_type == 'Gmail':
        return await gmail_login(context, task_vo, warpcast_login)
    elif task_vo.email_type == 'Outlook':
        return await outlook_login(context, task_vo, warpcast_login)
    elif task_vo.email_type == 'NetEase':
        return await netease_login(context, task_vo, warpcast_login)
    elif task_vo.email_type == 'Firstmail':
        if warpcast_login:
            return await firstmail_login(context, task_vo)
    else:
        logger.error(f"不支持的邮箱类型: {task_vo.email_type}")
    return False


async def outlook_login(context: BrowserContext, task_vo: User, warpcast_login=True) -> bool:
    task_id = task_vo.browser_id
    logger.info(f"开始尝试登录 Outlook: {task_id}")
    page: Page = await utils.get_page_by_url(context, 'https://outlook.live.com/')
    try:
        # 获取页面是否有“登入”
        not_log_in = await page.query_selector('[data-bi-ecn="Sign in"]')
        if not_log_in:
            logger.info("用户未登录，开始进行登录操作")
            # 判断登入是bnt还是input，如果未登录过页面有登入按钮，如果已登入过是输入username的input
            sign_in_button = await page.query_selector('[data-bi-ecn="Sign in"]')
            if sign_in_button:
                logger.info("点击【Sign in】按钮")
                await sign_in_button.click()
                # 等待页面跳转
                await asyncio.sleep(2)
            else:
                logger.info("直接登录")
                # 使用 await 关键字等待协程执行
            await login_to_outlook(context, task_vo.email, task_vo.password, page)
        else:
            logger.info("用户已经登录 Outlook")

        # 登录后直接查找并点击链接
        await outlook_find_warpcast_link(page, context, task_vo, warpcast_login)
    except Exception as e:
        record_err_mail(f"Outlook 登录出错: {e}", task_vo)
    return False


async def login_to_outlook(context: BrowserContext, username: str, password: str, page):
    # 输入邮箱地址
    logger.info(f"输入邮箱地址：{username}")
    await page.fill('input[type="email"]', username)
    # 点击下一步按钮
    await page.click('button[type="submit"]')
    # 等待页面加载
    await asyncio.sleep(2)
    # 输入密码
    logger.info(f"输入邮箱密码：{password}")
    await page.fill('input[type="password"]', password)
    # 点击登录按钮
    await page.click('button[type="submit"]')
    # 等待登录完成
    await asyncio.sleep(5)
    # 保持登录
    await page.click('text=Keep me signed in')


async def outlook_find_warpcast_link(page, context, user, warpcast_login=True):
    try:
        try:
            # 尝试查找并点击中文的“垃圾邮件”文件夹
            junk_folder_chinese = await page.query_selector('text=垃圾邮件')
            junk_folder_english = await page.query_selector('text=Junk Email')
            if junk_folder_chinese:
                await junk_folder_chinese.click()
                logger.info("成功点击 '垃圾邮件' 文件夹")
            # 若未找到中文文件夹，尝试查找并点击英文的 “Junk Email” 文件夹
            elif junk_folder_english:
                await junk_folder_english.click()
                logger.info("成功点击 'Junk Email' 文件夹")
            else:
                logger.info("未找到 '垃圾邮件' 或 'Junk Email' 文件夹")
        except Exception as e:
            logger.error(f"查找并点击垃圾邮件文件夹出错: {e}")

        # 获取所有邮件元素
        if warpcast_login:
            return await find_warpcast_magic_link(page, context, user)
        else:
            return True
    except Exception as e:
        record_err_mail(f"查找并点击链接出错: {e}", user)
    return False


async def gmail_login(context, user: User, warpcast_login=True):
    logger.info(f"开始登录 Gmail: {user.email}")
    # 打开 Gmail 登录页面
    page: Page = await utils.get_page_by_url(context, 'https://accounts.google.com')
    try:
        sign_in_button = await page.query_selector('[data-bi-ecn="Sign in"]')
        if sign_in_button:
            logger.debug(f'登录gmail按钮html{await sign_in_button.inner_html()}')
            await sign_in_button.click()
            try:
                await page.wait_for_load_state('networkidle')
            except:
                print('gmail_login======================================0')
    except Exception as e:
        record_err_mail(f"Gmail 中间页面出错: {e}", user)
        return False
    try:
        # 获取页面是否有“登入”
        login_input = page.locator('input[type="email"]')
        relogin = False
        if 'https://accounts.google.com' in page.url:
            relogin = await PageAuto(page, context, user.browser_id) \
                .get_by_text(user.email).click(timeout=1000, parent=True)
        if await login_input.count() > 0 or relogin:

            logger.info("用户未登录，开始进行登录操作")
            if not relogin:
                # 输入邮箱地址
                await login_input.fill(user.email)
                await asyncio.sleep(1)
                await login_input.press("Enter")

            # 等待页面加载，这里简单等待 2 秒，可以根据实际情况调整
            await asyncio.sleep(2)
            password_input = page.locator('input[name="Passwd"]')
            # 输入密码
            await password_input.fill(user.password)
            await asyncio.sleep(1)
            await password_input.press("Enter")

            # 等待登录完成，可根据实际加载情况调整等待时间
            await asyncio.sleep(5)
            
            try:
                await page.wait_for_load_state('networkidle')
            except:
                print('gmail_login======================================1')
            try:
                #
                data_challenge = page.locator('div[data-challengeid="5"]')
                if await data_challenge.count() > 0:
                    await data_challenge.click()
                    try:
                        await page.wait_for_load_state('networkidle')
                    except:
                        print('gmail_login======================================2')

                    await PageAuto(page, context, user.browser_id) \
                        .locator('input[type="email"]').fill(user.email_assist)
                    await asyncio.sleep(1)
                    await page.locator('input[type="email"]').press("Enter")
                    try:
                        await page.wait_for_load_state('networkidle')
                    except:
                        print('gmail_login======================================3')
            except Exception as e:
                logger.error(f"Gmail 风控处理出错: {e}")
            if 'https://gds.google.com/' in page.url:
                err_msg = f'Google账号[{user.email}]已被风控'
                record_err_mail(err_msg, user)
                raise RuntimeError(err_msg)
            await asyncio.sleep(10)
        else:
            logger.info("用户已经登录 Gmail")
        try:
            await page.goto("https://mail.google.com/mail/u/0/#inbox")
            await asyncio.sleep(3)
        except Exception as e:
            logger.debug(f"Gmail 加载超时: {e}")
        if 'https://mail.google.com/mail/u/0/#inbox' not in page.url:
            err_msg = f'Gmail账号[{user.email}]登录失败================================={user.browser_id}'
            record_err_mail(err_msg, user)
            raise RuntimeError(err_msg)
        # 调用查找并点击链接的函数
        if warpcast_login:
            reload_flg = False
            # gmail个性化设置
            for i in range(3):
                if await PageAuto(page, context, user.browser_id) \
                        .get_by_role("option").click(timeout=500):
                    if i == 2:
                        await PageAuto(page, context, user.browser_id) \
                            .get_by_role("button",name='Save').click(timeout=1000)
                    else:
                        await PageAuto(page, context, user.browser_id) \
                            .get_by_role("button",name='Next').click(timeout=1000)
                    reload_flg=True
            if reload_flg:
                await PageAuto(page, context, user.browser_id) \
                        .get_by_role("button",name='Reload').click(timeout=1000)
            return await find_warpcast_magic_link(page, context, user)
        else:
            return True
    except Exception as e:
        record_err_mail(f"Gmail 登录出错: {e}", user)
    return False


def record_err_mail(err_msg, user):
    logger.error(err_msg)
    ERR_RECORDER = Recorder(ERR_URL)
    ERR_RECORDER.add_data((user.browser_id, user.email, user.password, user.email_type, user.email_assist, err_msg))
    ERR_RECORDER.record()


async def find_warpcast_magic_link(page: Page, context, user) -> bool:
    # Confirm Warpcast login
    # await PageAuto(page, context, user.browser_id) \
    #         .get_by_text('Confirm Warpcast login').click(timeout=1000, parent=True)
    main_mail_url = page.url
    for i in range(5):
        logger.info(f"正在查找 Confirm Warpcast 链接，尝试次数：{i + 1}")
        await page.wait_for_timeout(3000)
        if main_mail_url == page.url:
            if not await PageAuto(page, context, user.browser_id) \
                    .get_by_text('Confirm Warpcast login') \
                    .click(timeout=1000, parent=True):
                await PageAuto(page, context, user.browser_id) \
                    .locator('div[class="y6"]') \
                    .get_by_text('Confirm Warpcast login') \
                    .click(timeout=1000, parent=True)

        await asyncio.sleep(3)

        # 查找邮件中的链接
        links = await page.query_selector_all('a')
        for link in links:
            href = await link.get_attribute('href')
            print(href)
            if href and 'https://warpcast.com/magic-link?' in href:
                # 点击链接
                await page.goto(href)
                await page.wait_for_load_state('networkidle')
                # An error has occurred. Please try again.
                if await PageAuto(page, context, user.browser_id) \
                        .get_by_text('An error has occurred. Please try again.').is_visible():
                    logger.debug("An error has occurred. Please try again.")
                else:
                    return True
        frames: List[Frame] = page.frames
        for frame in frames:
            # frame查找邮件中的链接
            f_links = await frame.query_selector_all('a')
            for f_link in f_links:
                href = await f_link.get_attribute('href')
                print(href)
                if href and 'https://warpcast.com/magic-link?' in href:
                    # 点击链接
                    await page.goto(href)
                    await page.wait_for_load_state('networkidle')
                    # An error has occurred. Please try again.
                    if await PageAuto(page, context, user.browser_id) \
                            .get_by_text('An error has occurred. Please try again.').is_visible():
                        logger.debug("An error has occurred. Please try again.")
                    else:
                        return True
        logger.info("未找到 Confirm Warpcast 链接，继续等待")
        try:
            await page.reload(wait_until='networkidle')
        except Exception:
            logger.debug('刷新页面')
    record_err_mail("未找到 Confirm Warpcast 链接，请手动处理", user)
    return False


async def netease_login(context, user, warpcast_login=True):
    logger.info(f"开始登录 NetEase: {user.email}")
    # https://mail.163.com
    page: Page = await utils.get_page_by_url(context, 'https://mail.163.com')
    try:

        # 切换到登录的 iframe
        if await page.get_by_role("heading", name="账号登录").is_visible():
            frame = page.frame_locator('iframe[id^="x-URS-iframe"]').first
            await asyncio.sleep(3)
            try:
                # id="switchAccountLogin"
                await frame.locator('a[id="switchAccountLogin"]').click(timeout=1000)
            except Exception as e:
                logger.debug(f"NetEase 尝试切换密码登录: {e}")
            try:
                # id="switchAccountLogin"
                await frame.get_by_role('link', name="密码登录").click(timeout=2000)
            except Exception as e:
                logger.debug(f"NetEase 尝试切换密码登录: {e}")
            # 在 iframe 中输入邮箱地址
            await frame.locator('input[name="email"]').fill(user.email)
            await asyncio.sleep(2)
            # 在 iframe 中输入密码
            await frame.locator('input[name="password"]').fill(user.password)
            await asyncio.sleep(2)
            await frame.locator('input[id="un-login"]').click()
            await asyncio.sleep(2)
            # 在 iframe 中点击登录按钮
            await frame.locator('a[data-action="dologin"]').click()

            # 等待登录完成
            await asyncio.sleep(5)
        else:
            logger.info("用户已经登录 NetEase")
        await page.wait_for_load_state('networkidle')
        logger.info(f"环境ID: {user.browser_id}网易登录校验中，等待30秒")
        # 等待 30秒后刷新，warpcast加载特别慢
        for i in range(1, 10):
            logger.info(f"环境ID: {user.browser_id}登录校验中，等待中==========================={i * 3}秒")
            try:
                await asyncio.sleep(3)
            except Exception:
                print(11111111111111111111111)
            if 'https://mail.163.com' not in page.url:
                try:
                    await page.wait_for_load_state('networkidle')
                except Exception:
                    print(11111111111111111111111)
                break
        unread = await PageAuto(page, context, user.browser_id) \
            .get_by_role("img", name="未读邮件").click()

        # 调用查找并点击链接的函数
        if warpcast_login:
            return await find_warpcast_magic_link(page, context, user)
        else:
            return unread
    except Exception as e:
        record_err_mail(f"NetEase 登录出错: {e}", user)
    return False


async def firstmail_login(context, user):
    logger.info(f"开始登录 Firstmail: {user.email}")
    page = await context.new_page()
    try:
        # 假设的 Firstmail 登录页面，需要根据实际修改
        magic_link = None
        for _ in range(10):
            magic_link = get_firstmail_code(user.email, user.password)
            if magic_link:
                break
            else:
                await page.wait_for_timeout(3000)
        if magic_link:
            await page.goto(magic_link)
            await page.wait_for_load_state('networkidle')
            # An error has occurred. Please try again.
            if await PageAuto(page, context, user.browser_id) \
                    .get_by_text('An error has occurred. Please try again.').is_visible():
                record_err_mail("Firstmail未找到 Confirm Warpcast 链接，请手动处理", user)
                return False
            else:
                return True
        else:
            record_err_mail("Firstmail未找到 Confirm Warpcast 链接，请手动处理", user)
    except Exception as e:
        record_err_mail(f"Firstmail 登录出错: {e}", user)
    return False


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
                            if local_date < datetime.now() - timedelta(minutes=timeout):
                                continue

                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    if "Confirm Warpcast login" not in subject:
                        continue
                    print("Subject:", subject)

                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if "attachment" not in content_disposition:
                                if content_type == "text/html":
                                    body = part.get_payload(decode=True).decode()

                                    a_list = body.split('<a href="')
                                    for a in a_list:
                                        if "https://warpcast.com/magic-link?" in a:
                                            mail.logout()
                                            return a[:a.find('">')]
                    else:
                        body = msg.get_payload(decode=True).decode()

                        a_list = body.split('<a href="')
                        for a in a_list:
                            if "https://warpcast.com/magic-link?" in a:
                                mail.logout()
                                return a[:a.find('">')]
    mail.logout()
    return None
