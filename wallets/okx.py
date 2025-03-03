import traceback
from abc import ABC
from typing import Optional, Dict, Any

from page_auto import PageAuto
from wallets import Wallet, close_popup, get_wallets_page  # 从 wallet.py 导入 Wallet 抽象类
from playwright.async_api import Page, BrowserContext
from loguru import logger


async def okx_confirm(page: Page, context: BrowserContext, task_id: int):
    # 点击确认按钮 0 取消 1 确认
    try:
        pa = PageAuto(page, context, task_id)
        await pa.get_by_test_id('okd-button').click(nth=1)
    except:
        logger.error(f'okx-confirm-error: {traceback.print_exc()}')


class OKXWallet(Wallet, ABC):
    def __init__(self, context: BrowserContext, password: str, task_id: int):
        self.context = context
        self.password = password
        self.task_id = task_id

    async def open(self, extension_id='mcohilncbfahbmgdjkbpemcciiolgcge') -> Page:
        logger.info(f'{self.task_id} 等待钱包弹出')
        popup: Page = await self.context.new_page()
        await popup.goto(f'chrome-extension://{extension_id}/home.html')
        # 等待弹窗加载完成
        await popup.wait_for_load_state()

        await popup.wait_for_timeout(3000)
        # 将弹窗带到最前面
        await popup.bring_to_front()
        return popup

    async def unlock(self, extension_id='mcohilncbfahbmgdjkbpemcciiolgcge') -> None:
        logger.info(f'{self.task_id} 钱包解锁...')
        popup: Page = await self.open(extension_id)
        passwd = PageAuto(popup, self.context, self.task_id)
        passwd.get_by_test_id('okd-input')
        if await passwd.fill(self.password):
            unlock = PageAuto(popup, self.context, self.task_id)
            await unlock.get_by_test_id('okd-button').click(custom_delay=3000)

        await popup.close()

    async def approve(self) -> None:
        logger.info(f'{self.task_id} 确认授权...')
        await okx_confirm(await self.get_wallet_page(), self.context, self.task_id)

    async def get_wallet_page(self) -> Page:
        try:
            popup: Page = await self.context.wait_for_event('page', timeout=5000)
        except:
            logger.error(f'{self.task_id} 获取钱包页面失败')
            popup: Page = get_wallets_page(self.context)
        # 等待弹窗加载完成
        await popup.wait_for_load_state()

        await popup.wait_for_timeout(3000)
        # 将弹窗带到最前面
        await popup.bring_to_front()
        return popup

    async def sign(self) -> None:
        logger.info(f'{self.task_id} 签名确认...')
        await okx_confirm(await self.get_wallet_page(), self.context, self.task_id)

    async def signin(self) -> None:
        logger.info(f'{self.task_id} 登录确认...')
        await okx_confirm(await self.get_wallet_page(), self.context, self.task_id)

    async def confirm_transaction(self, options: Optional[Dict[str, Any]] = None) -> None:
        logger.info(f'{self.task_id} 确认交易...')
        popup = await self.get_wallet_page()
        # 判断是否需要选择网略-测试网选择rpc节点
        check_rpc = PageAuto(popup, self.context, self.task_id).get_by_test_id('okd-checkbox-circle')
        if await check_rpc.click():
            await okx_confirm(popup, self.context, self.task_id, close_flg=False)
        # 判断是否需要批准
        approve_btn = PageAuto(popup, self.context, self.task_id).get_by_text('Approve')
        if await approve_btn.is_visible():
            await okx_confirm(popup, self.context, self.task_id, close_flg=False)
        await okx_confirm(popup, self.context, self.task_id)

    async def import_pk(self, pk: str) -> None:
        pass

    async def lock(self) -> None:
        pass

    async def reject(self) -> None:
        pass

    async def switch_account(self, account_number: int) -> None:
        pass

    async def switch_network(self, network: str) -> None:
        pass

    async def count_accounts(self) -> int:
        pass

    async def delete_account(self, account_number: int) -> None:
        pass

    async def delete_network(self, name: str) -> None:
        pass

    async def get_token_balance(self, token_symbol: str) -> float:
        pass

    async def has_network(self, name: str) -> bool:
        pass

    async def confirm_network_switch(self) -> None:
        pass

    @staticmethod
    def download(options: Dict[str, Any]) -> str:
        pass

    async def add_network(self, options: Dict[str, Any]) -> None:
        pass

    async def add_token(self, options: Dict[str, Any]) -> None:
        pass

    async def create_account(self) -> None:
        pass
