from sqlalchemy import func

import random  # 添加random模块

import repo
from repo import warpcast
from repo.user import User
from repo.corpora import Corpora

# 创建 SQLite 数据库连接
warpcast.init(url="D:/web3/dappwright/repo/warpcast.db")


def test_qry_corpora():
    c = warpcast.session.query(Corpora).filter_by(used=0, group_id=0) \
        .order_by(func.random()).first()
    print(c)


def test_qry_user():
    ud = warpcast.session.query(User).filter_by(email="q1xmth91@distan.vip").first()
    print(ud)


def test_update_user():
    users = repo.get_session.query(User).all()
    for user in users:
        if '@distan.vip' in user.email or '@gmail.com' in user.email:
            # 谷歌
            user.email_type = 'Gmail'
        elif '@outlook.com' in user.email:
            # 微软
            user.email_type = 'Outlook'
        elif '@163.com' in user.email or '@126.com' in user.email:
            # 网易
            user.email_type = 'NetEase'
        elif '@atorymail.com' in user.email \
                or '@bolivianomail.com' in user.email \
                or '@aceomail.com' in user.email \
                or '@chromomail.com' in user.email:
            '''
            @atorymail.com
            @bolivianomail.com
            @aceomail.com
            @chromomail.com
            '''
            # Firstmail
            user.email_type = 'Firstmail'
        else:
            user.email_type = 'Other'
        print(user)
    warpcast.session.commit()


def test_source_user():
    users = warpcast.session.query(User).all()
    # 通过source分析
    sc_users = []
    chad_users = []
    perry_users = []
    dahua_users = []
    for user in users:
        if '司辰' in user.source:
            sc_users.append(user)
        elif 'Perry' in user.source:
            perry_users.append(user)
        elif '大华' in user.source:
            dahua_users.append(user)
        elif 'chad' in user.source:
            chad_users.append(user)
    # 随机取三个用户
    random_users = random.sample(users, 3)  # 添加随机取三个用户的代码
    print(random_users)  # 打印随机取出的用户


def test_update_user2():
    users = warpcast.session.query(User).filter(User.browser_id < 1501, User.email.like('%@outlook.com')).all()
    for user in users:
        print(user)
        outlook = user.email
        outlook_password = user.password
        user.email = user.email_assist
        user.password = user.password_assist
        user.email_assist = outlook
        user.password_assist = outlook_password
        user.email_type = 'Firstmail'
    warpcast.session.commit()
# test_qry_user()
# test_qry_corpora()
# test_update_user()
# test_source_user()
test_update_user2()