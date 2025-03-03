import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from loguru import logger
from playwright.async_api import Page, BrowserContext


async def close_popup(popup: Page):
    if not popup.is_closed():
        await popup.wait_for_event('close')


async def get_wallets_page(context: BrowserContext, wallet_name='OKX Wallet') -> Page:
    idx: int = 0
    while True:
        nwp = await has_title(context, wallet_name)
        if nwp is not None or idx > 10:
            break
        else:
            logger.info(f"等待插件{wallet_name}...............{idx}")
            await asyncio.sleep(1)
        idx += 1
    return nwp


async def has_title(context: BrowserContext, title) -> Page:
    for p in context.pages:
        if p.title() == title:
            return p
    return None


class Wallet(ABC):

    # Extension downloader
    @staticmethod
    @abstractmethod
    async def download(options: Dict[str, Any]) -> str:
        pass

    # Wallet actions
    @abstractmethod
    async def add_network(self, options: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def add_token(self, options: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def open(self) -> None:
        pass

    # Action 批准
    @abstractmethod
    async def approve(self) -> None:
        pass

    @abstractmethod
    async def create_account(self) -> None:
        pass

    @abstractmethod
    async def confirm_network_switch(self) -> None:
        pass

    @abstractmethod
    async def confirm_transaction(self, options: Optional[Dict[str, Any]] = None) -> None:
        pass

    @abstractmethod
    async def count_accounts(self) -> int:
        pass

    @abstractmethod
    async def delete_account(self, account_number: int) -> None:
        pass

    @abstractmethod
    async def delete_network(self, name: str) -> None:
        pass

    @abstractmethod
    async def get_token_balance(self, token_symbol: str) -> float:
        pass

    @abstractmethod
    async def has_network(self, name: str) -> bool:
        pass

    @abstractmethod
    async def import_pk(self, pk: str) -> None:
        pass

    @abstractmethod
    async def lock(self) -> None:
        pass

    @abstractmethod
    async def reject(self) -> None:
        pass

    # Action 连接网站并签名
    @abstractmethod
    async def sign(self) -> None:
        pass

    @abstractmethod
    async def signin(self) -> None:
        pass

    @abstractmethod
    async def switch_account(self, account_number: int) -> None:
        pass

    @abstractmethod
    async def switch_network(self, network: str) -> None:
        pass

    @abstractmethod
    async def unlock(self, extension_id='') -> None:
        pass
