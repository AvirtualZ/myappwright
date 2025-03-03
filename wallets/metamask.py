from abc import ABC
from typing import List, Optional, Dict, Any
from wallets import Wallet, close_popup  # 从 wallet.py 导入 Wallet 抽象类
from playwright.async_api import Browser, Page


class MetaMask(Wallet, ABC):

    def __init__(self, browser: Browser, password: str):
        self.browser = browser
        self.password = password

    async def unlock(self, extension_id='nkbihfbeogaeaoehlefnkodbefgpgknn') -> None:
        unlock_p: Page = await self.browser.new_page()
        await unlock_p.goto(f'chrome-extension://{extension_id}/home.html')

        await unlock_p.get_by_test_id('unlock-password').fill(self.password)
        await unlock_p.get_by_test_id('unlock-submit').click();

        await close_popup()

    async def approve(self) -> None:
        popup: Page = await self.context.wait_for_event('page')
        # 等待弹窗加载完成
        await popup.wait_for_load_state()

        # 将弹窗带到最前面
        await popup.bring_to_front()

        # 选择第一个账户
        await popup.locator('.choose-account-list__account').first.locator('input[type="checkbox"]').first.check()
        await popup.get_by_test_id('page-container-footer-next').click()

        # 完成提示
        await popup.get_by_test_id('page-container-footer-next').click()

        await close_popup()

    async def sign(self) -> None:
        pass

    async def signin(self) -> None:
        pass

    async def confirm_transaction(self, options: Optional[Dict[str, Any]] = None) -> None:
        pass

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
