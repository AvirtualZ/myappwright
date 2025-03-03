import pandas as pd
from typing import Dict, Any

# 读取 Excel 文件（建议使用绝对路径）
try:
    df = pd.read_excel('browser.xlsx')
except FileNotFoundError:
    raise Exception("browser.xlsx 文件未找到，请确认文件路径是否正确")
except Exception as e:
    raise Exception(f"读取 Excel 文件失败：{str(e)}")

# 浏览器配置数据缓存字典
data_map: Dict[int, pd.Series] = {}


def get_data_map() -> None:
    """初始化数据映射
    将 Excel 中的 browser_id 列作为键，整行数据作为值存入字典
    """
    global data_map
    try:
        # 检查必要列是否存在
        if 'id' not in df.columns:
            raise KeyError("Excel 中缺少必要列：id")

        data_map = {row.id: row for _, row in df.iterrows()}
    except KeyError as ke:
        raise KeyError(f"数据列缺失：{str(ke)}")
    except Exception as e:
        raise Exception(f"初始化数据映射失败：{str(e)}")


def get_data(browser_id: int) -> Any:
    """获取浏览器配置数据
    Args:
        browser_id: 浏览器配置ID

    Returns:
        pd.Series: 对应的配置数据

    Raises:
        ValueError: 当ID不存在时抛出
    """
    # 仅当字典为空时初始化（修正原逻辑错误）
    if not data_map:
        get_data_map()

    try:
        return data_map[browser_id]
    except KeyError:
        available_ids = list(data_map.keys())
        raise ValueError(
            f"无效的 browser_id：{browser_id}，"
            f"可用ID范围：{min(available_ids)}-{max(available_ids)}"
        )
