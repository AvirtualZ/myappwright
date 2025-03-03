from loguru import logger
from sqlalchemy.orm import Session

from repo import warpcast, browser

func_list = {
    "warpcast": warpcast,
    "browser": browser,
}


def init(name="browser", url="repo/warpcast.db"):
    cls = func_list[f'{name}']
    if cls:
        cls.init(url)
    else:
        logger.debug(f"数据库：{name} 未找到")


async def session_commit(name="browser"):
    cls = func_list[f'{name}']
    if cls:
        await cls.session_commit()


def close(name="browser"):
    cls = func_list[f'{name}']
    if cls:
        cls.session.close()


def get_session(name="browser") -> Session:
    cls = func_list[f'{name}']
    if cls:
        return cls.session
