from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# 创建基类
Base = declarative_base()


# 定义表结构
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    # 辅助邮箱
    email_assist = Column(String)
    # 辅助密码
    password_assist = Column(String)
    # 助记词
    warpcast_mnemonic = Column(String)
    # 分层类型
    layer_type = Column(String)
    # 账号来源
    source = Column(String)
    # 浏览器ID
    browser_id = Column(String)
    # 邮箱类型
    email_type = Column(String)

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email}, source={self.source})>"
