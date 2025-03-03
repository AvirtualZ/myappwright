import asyncio
import os
import random
import typing

from DataRecorder import Recorder
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import BrowserContext, Page, Locator
from sqlalchemy import func

import ai_agent
import config
import repo
import utils
from page_auto import PageAuto, actions
from repo import warpcast
from repo.user import User
from repo.corpora import Corpora
from tasks.warpcast import accountlogin
from utils import logutils


used_contexts = logutils.get_list_from_file(f'./run_logs/used_context.txt')
used_context_data = Recorder(f'./run_logs/used_context.txt')
load_dotenv()
CORPORA_GROUP = os.getenv('CORPORA_GROUP')
'''
farcaster运营方案                    
方案说明：
1    所有账号数据指标
    关注的人    10+ 根据兴趣推送    
        关注的频道 20+ 
                    
        关注PowerBadge身份的用户    根据仪表盘    
        每月发帖    10+    
        每日发帖    1  
    2    发帖内容
        转发    转发首页推荐    
                转发频道推荐    
        原创    发布不带频道    
        发帖频率    每天1-3        
        分层要求    
            10%只做频道转发    具体参考数据仪表盘    素材取自AI语料库
            10%只做首页trending转发        
            40%转发已关注频道    发布个人原创    素材取自AI语料库
            20%通过仪表盘最受欢迎的转发统计，参与发帖    待协商    
            20%通过仪表盘最受欢迎的用户统计，参与发帖    待协商    
        ---- 司辰总回复
            1、发帖总数10条casts+，所以分层指的是单个用户的发帖比例，，首页趋势转发的用户，指的是从技术上设计的转发路径，首页跳转-Trending，随机选择推送的1、3、5、9条进行转发
            2、频道转发在技术上的设计是首页-跳转频道-随机选择频道内的随机发布进行转发
            3、频道内转发首先排除置顶的那条
            4、ai语料库使用的范围比较小，一个是原创不带频道，一个是针对频道去发相关内容，无意义的水贴不合适
            
    3    待协商warpcast功能使用            
            使用Frames    随机添加框架元素，无需使用    需求待协商    
            使用Actions    随机添加内置插件    需求待协商    
    4    钱包交互    需根据Warpcast生态圈活动协商方案        
        &氪金打赏
            
Farcaster常用数据网站汇总
        https://warpcast.com/     Farcaster最常用的客户端之一        
        https://decaster.xyz/     （Farcaster生态工具汇总网站）        
        https://farcaster.network/     （Farcaster数据查询网站）        
        https://dune.com/pixelhack/farcaster     （Farcaster的Dune数据仪表盘）        
        https://www.farcaster.in/     (Farcaster生态代币查询网站)        
        https://fc.hot100.xyz/    （Farcaster热门MEME币统计网站）
'''


async def do_task(context: BrowserContext, browser_id):
    task_vo: User = await warpcast.find_user_by_browser_id(browser_id)
    logger.info(f"开始执行每日任务，环境ID: {browser_id}")
    # TODO: 检查是否登录，如果没有登录，则走登录流程
    warpcast_page: Page = await utils.get_page_by_url(context, 'https://warpcast.com')
    
    await warpcast_page.wait_for_load_state('networkidle')
    await warpcast_page.wait_for_timeout(3000)
    # TODO 校验IP是否有效。
    await login_check(context, task_vo, warpcast_page)
    # 登录
    # 关注频道
    await channels_task(context, task_vo, warpcast_page)
    # 关注用户
    await follow_user(context, task_vo, warpcast_page)
    # 发帖
    await cast_task(context, task_vo, warpcast_page)
    # 转帖
    await recast_task(context, task_vo, warpcast_page)
    # 增加框架
    await add_frames(context, task_vo, warpcast_page)
    # 增加活动
    await add_actions(context, task_vo, warpcast_page)


async def channels_task(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    logger.debug(f'channels_task================================={task_id}')

    try:
        all_channels = await get_user_follow_channels(task_id, warpcast_page, context)
        if len(all_channels) < 20:
            # TODO: 关注频道
            cnt = random.randint(10, 30)
            logger.info(f"开始关注频道，线程ID: {task_id}, 原数量：{len(all_channels)}，关注数量：{cnt}")
            random_channels = random.sample(config.follow_channels, cnt)
            for channel_url in random_channels:
                await utils.page_goto(warpcast_page, channel_url)
                await PageAuto(warpcast_page, context, task_id) \
                    .get_by_role('button', name='Follow').click()
    except Exception as e:
        logger.error(f"执行关注频道异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def cast_task(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    logger.debug(f'cast_task================================={task_id}')
    try:
        logger.debug(f"开始发帖，线程ID: {task_id}")
        corpora_data = warpcast.session.query(Corpora).filter_by(used=0, group_id=CORPORA_GROUP) \
            .order_by(func.random()).first()
        if corpora_data and corpora_data.context:
            if corpora_data.context in used_contexts:
                logger.debug(f"已使用过语料: {corpora_data}========================={task_id}")
                return
            logger.debug(f"获取发帖随机语料发帖: {corpora_data}========================={task_id}")
            tags = corpora_data.tag.split(' ')
            tag0 = random.choice(tags)
            if tag0 != 'home':
                cast_channel = config.get_cast_channel(corpora_data.tag)
                if cast_channel:
                    logger.debug(f"关注频道: {cast_channel}========================={task_id}")
                    await utils.page_goto(warpcast_page, cast_channel)
                    await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('button', name='Follow').click()
                    await PageAuto(warpcast_page, context, task_id) \
                        .get_by_title('Home').click()
            if await PageAuto(warpcast_page, context, task_id) \
                    .get_by_role('button', name='Cast').click():
                corpora_context = corpora_data.context
                ai_flg = random.randint(1, 3) == 3
                logger.debug(f"输入发帖内容: {corpora_context}========================={task_id}")
                if ai_flg:
                    ai_context = ai_agent.get_ai_corpora(corpora_context)
                    logger.debug(f"获取ai内容: {ai_context}========================={task_id}")
                    if ai_context:
                        corpora_context = ai_context
                    else:
                        ai_flg = False
                if await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('combobox').fill(corpora_context):
                    if tag0 != 'home':
                        await asyncio.sleep(actions.delay)  # 等待几秒
                        logger.debug(f"选择频道: {tag0}==============1==========={task_id}")
                        if await PageAuto(warpcast_page, context, task_id) \
                                .locator("#modal-root").get_by_role("img").click():
                            logger.debug(f"选择频道: {tag0}==============2==========={task_id}")
                            if await PageAuto(warpcast_page, context, task_id) \
                                    .get_by_placeholder("Search for channels").fill(tag0):
                                logger.debug(f"点击频道: {tag0}==============3==========={task_id}")
                                await PageAuto(warpcast_page, context, task_id) \
                                    .locator(config.x_map["first_search_channel"]).click()
                    if await PageAuto(warpcast_page, context, task_id) \
                            .get_by_title("Cast").click():
                        logger.info(f"环境ID: {task_id} 发帖成功")
                        if not ai_flg:
                            used_contexts.append(corpora_context)
                            used_context_data.add_data(corpora_context)
                            used_context_data.record()
            else:
                logger.error(f"点击【Cast】按钮失败，环境ID: {task_id} ")
    except Exception as e:
        await utils.page_goto(warpcast_page, '/')
        logger.error(f"执行发帖异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def login_check(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    logger.debug(f'login_check================================={task_id}')
    if await PageAuto(warpcast_page, context, task_id) \
            .get_by_text('Log in with email').is_visible():
        logger.info(f"环境ID: {task_id}登录校验中，等待10秒")
        # 等待 30秒后刷新，warpcast加载特别慢
        for i in range(1, 6):
            logger.info(f"环境ID: {task_id}登录校验中，等待中==========================={i * 2}秒")
            await warpcast_page.wait_for_timeout(2000)
        await warpcast_page.reload(wait_until="networkidle")
        if await PageAuto(warpcast_page, context, task_id) \
                .get_by_text('Log in with email').click():
            logger.info(f"环境ID: {task_id}未登录，执行登录流程")
            await PageAuto(warpcast_page, context, task_id) \
                .get_by_placeholder('satoshin@gmx.com').fill(task_vo.email)
            if await PageAuto(warpcast_page, context, task_id) \
                    .get_by_role('button', name='Send email').click():
                # TODO: 登录流程
                if await accountlogin.do_task(context, task_id):
                    await warpcast_page.reload(wait_until="networkidle")
                elif await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('button', name='Send email').click():
                    # TODO: 二次登录流程
                    if await accountlogin.do_task(context, task_id):
                        await warpcast_page.reload(wait_until="networkidle")
                    
    if await PageAuto(warpcast_page, context, task_id) \
            .get_by_text('Log in with email').is_visible():
        logger.error(f"执行登录异常，环境ID: {task_id} ")
        raise RuntimeError(f"执行登录异常，环境ID: {task_id} ")


async def follow_user(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    logger.debug(f'follow_user================================={task_id}')
    try:
        # 随机1~10 如果大于7则执行
        if random.randint(1, 10) > 7:
            await PageAuto(warpcast_page, context, task_id) \
                .get_by_role('button', name='Follow').all_click()
        fu_cnt = random.randint(0, 3)
        if fu_cnt > 0:
            random_power_users = random.sample(config.power_users, fu_cnt)  # 添加随机取三个用户的代码
            print(random_power_users)  # 打印随机取出的用户
            for a_user in random_power_users:
                await utils.page_goto(warpcast_page, a_user)
                await warpcast_page.wait_for_timeout(3000)
                await PageAuto(warpcast_page, context, task_id) \
                    .get_by_role('button', name='Follow').click()
                await warpcast_page.wait_for_timeout(1000)

    except Exception as e:
        logger.error(f"执行关注用户异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def add_frames(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    try:
        all_frames = await PageAuto(warpcast_page, context, task_id) \
            .locator('div[class="border-hairline relative"]').all()
        if len(all_frames) < 3:
            logger.info(f"环境ID: {task_id} 添加过frames < 3，执行【add_frames】任务")
            if await PageAuto(warpcast_page, context, task_id) \
                    .get_by_title('Frames').click():
                await warpcast_page.wait_for_load_state('networkidle')
                if await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('button', name='Add').click():
                    await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('button', name='Confirm').click()
    except Exception as e:
        logger.error(f"执行添加框架异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def add_actions(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    try:
        if random.randint(1, 3) == 3:
            await utils.page_goto(warpcast_page, 'https://warpcast.com/~/settings/actions')
            if await warpcast_page.locator('div[data-rfd-droppable-id="castActions"]') \
                    .evaluate('el => el.childElementCount == 0'):
                await utils.page_goto(warpcast_page, 'https://warpcast.com/~/discover-actions')
                action_list = await PageAuto(warpcast_page, context, task_id).locator('a[title="Add action"]')\
                    .filter_by_attribute('href', '/~/add-cast-action')
                if len(action_list) > 0:
                    await random.choice(action_list).click()
                    await warpcast_page.wait_for_load_state('networkidle')
                    await PageAuto(warpcast_page, context, task_id) \
                        .get_by_role('button', name='Add').click()
                    await warpcast_page.wait_for_timeout(10000)
    except Exception as e:
        logger.error(f"执行添加Action异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def recast_task(context: BrowserContext, task_vo: User, warpcast_page: Page):
    task_id = task_vo.browser_id
    try:
        '''
        转帖分层要求    
        10%只做频道转发    具体参考数据仪表盘    素材取自AI语料库
        10%只做首页trending转发        
        40%转发已关注频道    发布个人原创    素材取自AI语料库
        20%通过仪表盘最受欢迎的转发统计，参与发帖    待协商    
        20%通过仪表盘最受欢迎的用户统计，参与发帖    待协商    
        '''
        # 随机
        ri = random.randint(1, 100)
        if ri <= 10:
            logger.debug(f"环境ID: {task_id} 10%只做频道转发")
            recast_channel = random.choice(config.follow_channels)
            await utils.page_goto(warpcast_page, recast_channel)
            logger.debug(f"环境ID: {task_id} 向下滚动 模拟人类操作")
            await utils.human_like_scroll(warpcast_page, scroll_steps=random.randint(2, 5))
            await recasts_handler(task_id, warpcast_page)
        elif ri <= 20:
            logger.debug(f"环境ID: {task_id} 10%只做首页trending转发")
            await PageAuto(warpcast_page, context, task_id) \
                .get_by_title('Trending').click()
            await warpcast_page.wait_for_load_state('networkidle')
            await recasts_handler(task_id, warpcast_page)
        elif ri <= 60:
            logger.debug(f"环境ID: {task_id} 40%转发已关注频道")
            all_channels = await get_user_follow_channels(task_id, warpcast_page, context)
            await actions.click(random.choice(all_channels), task_id)
            await warpcast_page.wait_for_load_state('networkidle')
            logger.debug(f"环境ID: {task_id} 向下滚动 模拟人类操作")
            await utils.human_like_scroll(warpcast_page, scroll_steps=random.randint(2, 5))
            await recasts_handler(task_id, warpcast_page)
        elif ri <= 80:
            logger.debug(f"环境ID: {task_id} 20%通过仪表盘最受欢迎的转发统计，参与发帖")
            random_channel = random.choice(config.follow_channels)
            await utils.page_goto(warpcast_page, random_channel)
            await one_recast_handler(task_id, warpcast_page, context)
        else:
            logger.debug(f"环境ID: {task_id} 20%通过仪表盘最受欢迎的用户统计，参与发帖")
            random_power_user = random.choice(config.power_users)
            if random_power_user:
                await utils.page_goto(warpcast_page, random_power_user)
                await PageAuto(warpcast_page, context, task_id) \
                    .get_by_role('button', name='Follow').click()
                await recasts_handler(task_id, warpcast_page)

    except Exception as e:
        logger.error(f"执行转帖异常，环境ID: {task_id} {e}")
    finally:
        await PageAuto(warpcast_page, context, task_id) \
            .get_by_title('Home').click()


async def recasts_handler(task_id, warpcast_page):
    cast_divs = await warpcast_page.locator('div[class="relative w-full min-w-0"]').all()
    cast_len = len(cast_divs)
    if cast_len == 0:
        logger.debug(f"环境ID: {task_id} 随机帖子数为零，跳过")
        return
    logger.debug(f"环境ID: {task_id} 随机帖子{cast_len}")
    cast_list = random.sample(cast_divs, min(3, cast_len - 1))
    logger.info(f"环境ID: {task_id} 转帖列表 {cast_list}")
    for cast_div in cast_list:
        recast_x = config.x_map['recast']
        like_x = config.x_map['like']
        logger.debug(f"环境ID: {task_id} 点击转帖")
        if random.randint(1, 10) > 5:
            await actions.click(cast_div.locator(like_x), task_id)
        if await actions.click(cast_div.locator(recast_x), task_id):
            await actions.click(warpcast_page.get_by_role('button', name='Recast'), task_id)
        else:
            logger.error(f"环境ID: {task_id} 点击转帖失败")


async def one_recast_handler(task_id, warpcast_page, context):
    # //*[@id="root"]/div/div/div/main/div/div/div
    # //*[@id="root"]/div/div/div/main/div/div/div/div[1]/div/div[2]/div/div[2]/div

    logger.debug(f"环境ID: {task_id} 随机帖子")
    if await PageAuto(warpcast_page, context, task_id) \
            .locator('div[class="h-full w-full"]').is_visible():
        recast_x = config.x_map['recast_single']
        like_x = config.x_map['like_single']
        logger.debug(f"环境ID: {task_id} 点击转帖")
        if await PageAuto(warpcast_page, context, task_id) \
                .locator('div[class="h-full w-full"]') \
                .locator('div[class=" fade-in"]').locator(recast_x).click():
            await actions.click(warpcast_page.get_by_role('button', name='Recast'), task_id)
        else:
            logger.error(f"环境ID: {task_id} 点击转帖失败")
        if random.randint(1, 10) > 5:
            await PageAuto(warpcast_page, context, task_id) \
                .locator('div[class="h-full w-full"]') \
                .locator('div[class=" fade-in"]').locator(like_x).click()
    logger.debug(f"环境ID: {task_id} 随机帖子数为零，跳过")
    return


async def get_user_follow_channels(task_id, warpcast_page, context):
    all_channels: typing.List[Locator] = await PageAuto(warpcast_page, context, task_id) \
        .locator('a[class="relative group"]').filter_by_attribute('href', '/~/channel')

    return all_channels
