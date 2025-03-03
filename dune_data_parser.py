import json

# 将你的 JSON 数据存储为一个字符串
json_data = {}

# 提取数据中的 channel_name
channel_data = json_data['execution_succeeded']['data']

for channel in channel_data:
    name = channel['username']
    name = name.replace('<a href="', "'")
    name = name.replace('" target="_blank">', "',   ")
    print(name)
