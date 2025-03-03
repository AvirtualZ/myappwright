from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# 创建基类
Base = declarative_base()

'''

'''


# 定义表结构
class Corpora(Base):
    __tablename__ = 'corpora'

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    context = Column(String)
    used = Column(Integer)
    group_id = Column(Integer)

    def __repr__(self):
        return f"<Corpora(tag={self.tag}, context={self.context}, used={self.used}, group_id={self.group_id})>"
