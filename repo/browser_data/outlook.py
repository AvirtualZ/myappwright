from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# 创建基类
Base = declarative_base()


# 定义表结构
class Outlook(Base):
    __tablename__ = 'outlook'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    password = Column(String)
    # 辅助邮箱
    email_assist = Column(String)
    # 辅助密码
    password_assist = Column(String)
    # 浏览器ID
    browser_id = Column(Integer)

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email}, source={self.source})>"
