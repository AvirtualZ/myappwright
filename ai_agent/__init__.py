import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MOONSHOT_API_KEY = os.getenv('MOONSHOT_API_KEY')
client = OpenAI(
    api_key=MOONSHOT_API_KEY,  # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url="https://api.moonshot.cn/v1",
)


def get_ai_corpora(old_corpora):
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "user", "content": f"根据语料：{old_corpora}生成一条类似语料，并加点emoj"}
        ],
        temperature=0.3,
    )

    # 通过 API 我们获得了 Kimi 大模型给予我们的回复消息（role=assistant）
    ai_content = completion.choices[0].message.content
    print("AI:", ai_content[:ai_content.find("\n")])
    return ai_content[:ai_content.find("\n")]
