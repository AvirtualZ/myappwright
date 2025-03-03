import asyncio
import os
from typing import Type

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from repo.browser_data.browser_user import BrowserUser
from repo.user import User

session: Session = None


def init(url="repo/browser.db"):
    # 创建 SQLite 数据库连接
    engine = create_engine(f"sqlite:///{url}", echo=True)
    # 创建会话
    session_class = sessionmaker(bind=engine)
    global session
    session = session_class()


async def session_commit():
    session.commit()
