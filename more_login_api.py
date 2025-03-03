import time
from typing import List

import pandas as pd
import requests
import os
import random

import more_login

BASEURL = more_login.BASEURL  # 基础API地址，从more_login模块导入


def get_request_headers():
    """生成标准请求头
    Returns:
        dict: 包含认证信息的HTTP请求头字典
    """
    return more_login.create_request_headers()


def delete_proxy(proxy_id):
    """删除指定代理配置
    Args:
        proxy_id (int/str): 要删除的代理配置ID

    Returns:
        str: 请求ID（requestId）

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/proxyInfo/delete"
    request_body = [proxy_id]  # 服务端要求数组格式的请求体

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        print(response.json())
        return response.json().get('requestId')
    except requests.exceptions.RequestException as error:
        print("Error deleting proxy:", error)
        raise error


def add_proxy_to_profile(ip, port, username, password, name=''):
    """添加代理配置到配置文件
    Args:
        ip (str): 代理服务器IP地址
        port (int/str): 代理服务器端口
        username (str): 代理认证用户名
        password (str): 代理认证密码
        name (str): 代理配置名称

    Returns:
        dict: 添加成功的代理数据

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/proxyInfo/add"

    request_body = {
        "proxyIp": ip,
        "proxyPort": port,
        "proxyName": name,
        "username": username,
        "password": password,
        "proxyProvider": 2,  # 通过代理类型查询 0：http，1：https，2：socks5，3：ssh
    }

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        return response.json().get('data')
    except requests.exceptions.RequestException as error:
        print("Error adding proxy:", error)
        raise error


def create_browser_profile(proxy_id, name, cookies=None):
    """创建浏览器配置文件（含随机系统类型和UA版本）
    Args:
        proxy_id (int/str): 关联的代理配置ID
        name (str): 浏览器配置名称
        cookies: Cookie
    Returns:
        dict: 创建成功的响应数据

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/env/create/advanced"

    # 操作系统类型：1-Windows，2-macOS
    os_types = [1, 2]
    random_os = random.choice(os_types)

    request_body = {
        "browserTypeId": 1,  # 浏览器类型（1-Chrome）
        "operatorSystemId": random_os,
        "envName": name,
        "cookies": cookies,
        "proxyId": proxy_id,
    }

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print("Error creating profile:", error)
        raise error


def delete_browser(profile_id: List):
    """将浏览器配置移入回收站
    Args:
        profile_id (list): 要删除的浏览器配置ID（支持批量）

    Returns:
        dict: 删除操作返回的数据

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/env/removeToRecycleBin/batch"

    request_body = {
        "envIds": profile_id,  # 支持单个或多个环境ID
    }

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        return response.json().get('data')
    except requests.exceptions.RequestException as error:
        print("Error deleting browser:", error)
        raise error


def get_ua(headers):
    """获取可用的用户代理（UA）版本列表
    Args:
        headers (dict): 包含认证信息的请求头

    Returns:
        list: Chrome浏览器的UA版本列表

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    url = f"{BASEURL}/api/env/advanced/ua/versions"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        chrome_ua = response.json().get('data')[0].get('versions')  # 取第一个浏览器类型的UA列表
        return chrome_ua
    except requests.exceptions.RequestException as error:
        print("Error getting UA:", error)
        raise error


def get_profiles():
    """获取浏览器配置列表（分页查询）
    Returns:
        int: 当前返回的配置数量

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/env/page"

    # 固定查询第一页，每页10条
    request_body = {
        "pageNo": 1,
        "pageSize": 10,
    }

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        print(response.json())
        return len(response.json().get('data').get('dataList'))  # 返回实际数据条数
    except requests.exceptions.RequestException as error:
        print("Error getting profiles:", error)
        raise error


def refresh_fingerprint(profile_id):
    """刷新浏览器指纹信息
    Args:
        profile_id (int/str): 需要刷新指纹的配置ID

    Returns:
        dict: 新的指纹数据

    Raises:
        RequestException: 当HTTP请求失败时抛出异常
    """
    headers = get_request_headers()
    url = f"{BASEURL}/api/env/fingerprint/refresh"

    request_body = {
        "envId": profile_id,
    }

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        print(response.json())
        return response.json().get('data')
    except requests.exceptions.RequestException as error:
        print("Error refreshing fingerprint:", error)
        raise error


if __name__ == '__main__':
    df = pd.read_excel('browser.xlsx', names=['id', 'proxy'])
    proxy_dict = {}
    for row in df.itertuples():
        print(f"行号：{row.id}, 整行数据：{row}")
        if row.proxy in proxy_dict:
            p_id = proxy_dict[row.proxy]
        else:
            proxy_parts = str(row.proxy).split(':')
            # 添加格式检查（在 split 后添加校验）
            if len(proxy_parts) != 4:
                raise ValueError("代理格式错误，应为 ip:port:username:password")
            for i in range(10):
                try:
                    p_id = add_proxy_to_profile(*proxy_parts)  # 要求 proxy_parts 刚好有4个元素
                    break
                except Exception as e:
                    print(f"第 {i+1} 次尝试失败，正在重试...{e}")
                    time.sleep(1)
            proxy_dict[row.proxy] = p_id
        for i in range(10):
            try:
                create_browser_profile(p_id, f"P-{row.id}")
                break
            except Exception as e:
                print(f"第 {i+1} 次尝试失败，正在重试...{e}")
                time.sleep(1)
