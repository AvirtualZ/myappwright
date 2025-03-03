import hashlib
import os
import random
import string
import time
from loguru import logger
import requests
from dotenv import load_dotenv
import pandas as pd

# 加载 .env 文件
load_dotenv()

APPID = os.getenv('APPID')
SECRETKEY = os.getenv('SECRETKEY')
BASEURL = os.getenv('BASEURL')


def generate_random_string(length=6):
    """生成指定长度的随机字符串，由字母和数字组成。"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_nonce_id():
    """生成唯一的 nonceId，包含当前时间戳和随机字符串。"""
    return str(int(time.time() * 1000)) + generate_random_string()


def generate_md5_signature(nonce_id):
    """根据 APPID、nonceId 和 SECRETKEY 生成 MD5 哈希值。"""
    md5 = hashlib.md5()
    md5.update((APPID + nonce_id + SECRETKEY).encode('utf-8'))
    return md5.hexdigest()


def create_request_headers():
    """生成 API 请求的头部，包括身份验证信息。"""
    nonce_id = generate_nonce_id()
    md5_str = generate_md5_signature(nonce_id)
    return {
        'X-Api-Id': APPID,
        'Authorization': md5_str,
        'X-Nonce-Id': nonce_id
    }


def start_environment(env_id, browser_id=None):
    """启动指定的 MoreLogin 环境，并返回调试端口。"""
    headers = create_request_headers()
    if browser_id:
        payload = {
            "uniqueId": browser_id
        }
    else:
        payload = {
            "envId": env_id,
        }
    try:
        logger.info(f'[{payload}] 正在启动环境')
        res = requests.post(f"{BASEURL}/api/env/start", json=payload, headers=headers)
        res.raise_for_status()  # 检查请求是否成功
        data = res.json()
        logger.info(f'启动环境：{data}')
        return data['data']['debugPort']
    except requests.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None


def close_environment(env_id, browser_id=None):
    """关闭指定的 MoreLogin 环境。"""
    headers = create_request_headers()
    if browser_id:
        payload = {
            "uniqueId": browser_id
        }
    else:
        payload = {
            "envId": env_id,
        }
    try:
        logger.info(f'[{payload}] 正在关闭环境')
        res = requests.post(f"{BASEURL}/api/env/close", json=payload, headers=headers)
        logger.info(f'关闭环境：{res}')
    except requests.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None


def parse_range(range_string):
    """解析用户输入的范围字符串"""
    result = set()
    parts = range_string.split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    return sorted(list(result))


def get_ids_from_excel(filename='more_login_ids.xlsx', indices=None):
    """从Excel文件中读取指定索引的id和env_id"""
    df = pd.read_excel(filename, names=['id', 'env_id'], dtype={'env_id': str})
    if indices:
        return df['env_id'].iloc[[i - 1 for i in indices]].tolist()  # 转换为0-based索引
    return df['env_id'].tolist()


def process_environment(count0, total0, env_id):
    logger.info(f'[{count0}/{total0}] 等待打开环境ID：{env_id}')
    debug_port = start_environment(env_id)
    if debug_port is None:
        logger.error(f"无法获取调试端口，请检查网络连接和MoreLogin服务是否正常。")
        return None
    logger.info(f'[{count0}/{total0}] 环境ID：{env_id} 已打开，正在启动浏览器...')
    return f'http://127.0.0.1:{debug_port}'


def process_environment_byid(browser_id):
    logger.info(f'等待打开环境ID：{browser_id}')
    debug_port = start_environment(None, browser_id=browser_id)
    if debug_port is None:
        logger.error(f"无法获取调试端口，请检查网络连接和MoreLogin服务是否正常。")
        return None
    logger.info(f'环境ID：{browser_id} 已打开，正在启动浏览器...')
    return f'http://127.0.0.1:{debug_port}'
