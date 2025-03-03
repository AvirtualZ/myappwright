from playwright.async_api import BrowserContext

from tasks import x
from tasks.init_browser import init_outlook
from tasks.warpcast import dailytasks, accountlogin

task_list = {
    "warpcast": [dailytasks.do_task],
    "account_login": [accountlogin.do_task],
    "x": [x.do_task],
    "init_outlook": [init_outlook.do_task],
}


async def do_task(context: BrowserContext, browser_id, task_name) -> int:
    task_funcs = task_list[task_name]
    for task_func in task_funcs:
        await task_func(context, browser_id)
