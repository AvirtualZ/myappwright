import os
import queue


def get_list_from_file(data_path, target=[]):
    datas = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='UTF-8') as f:
            for line in f.readlines():
                line = line.strip()
                if len(line) != 0:
                    if line in target:
                        continue
                    datas.append(line)
    return datas


def get_queue_from_file(data_path, target=[]):
    queues = queue.Queue()

    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='UTF-8') as f:
            for line in f.readlines():
                line = line.strip()
                if len(line) != 0:
                    if line in target:
                        continue
                    queues.put(line)
    return queues


def save_list_to_file(data_path, data_list, mode='w'):
    """
    将列表数据写入文件
    :param data_path: 文件路径
    :param data_list: 要写入的列表数据
    :param mode: 写入模式，默认覆盖写入（'w'），可改为追加写入（'a'）
    """
    # 自动创建不存在的目录
    dir_path = os.path.dirname(data_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(data_path, mode, encoding='UTF-8') as f:
        for item in data_list:
            line = str(item).strip()
            if len(line) > 0:
                f.write(line + '\n')
