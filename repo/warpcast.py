import asyncio
import os
from typing import Type

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from repo.user import User

session: Session = None


def init(url="repo/warpcast.db"):
    # 创建 SQLite 数据库连接
    engine = create_engine(f"sqlite:///{url}", echo=True)
    # 创建会话
    session_class = sessionmaker(bind=engine)
    global session
    session = session_class()


async def find_user_by_browser_id(browser_id) -> User:
    print(f"find_user_by_browser_id: {browser_id} 进入加锁区域")
    user_data = session.query(User).filter(User.browser_id == browser_id).first()
    logger.info(f"查询条件：{browser_id} 查询结果：{user_data}")
    print(f"find_user_by_browser_id: {browser_id} 进入 离开加锁区域")
    return user_data


async def session_commit():
    session.commit()
