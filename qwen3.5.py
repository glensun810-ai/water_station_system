import os
from openai import OpenAI

try:
    client = OpenAI(
        # 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-5261a4dfdf964a5c9a6364128cc4c653",
        # api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 各地域配置不同，请根据实际地域修改
        base_url="https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1",
    )

    response = client.responses.create(
        model="qwen3.5-plus",
        input="简要介绍下你能做什么？"
    )

    print(response)
except Exception as e:
    print(f"错误信息：{e}")
    print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")