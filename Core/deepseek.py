# from openai import OpenAI
#
#
# def run(prompt_str):
#     client = OpenAI(api_key="sk-f606c156208842f391806c4213bb8344", base_url="https://api.deepseek.com/v1",timeout=10.0)
#
#     response = client.chat.completions.create(
#         model="deepseek-coder",
#         messages=[
#             {"role": "system", "content": "You are a code assistant, you can answer any question about coding."},
#             {"role": "user", "content": prompt_str},
#         ],
#         stream=False
#     )
#     return response.choices[0].message.content



import requests
import json
from typing import Dict, Any

def run(prompt_str: str) -> str:
    """
    调用 DeepSeek API 并返回生成的文本。

    :param prompt_str: 用户输入的提示文本
    :return: 生成的文本内容
    """
    # API 配置
    api_key = "sk-f606c156208842f391806c4213bb8344"
    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 请求体
    data = {
        "model": "deepseek-coder",
        "messages": [
            {"role": "system", "content": "You are a code assistant, you can answer any question about coding."},
            {"role": "user", "content": prompt_str}
        ],
        "stream": False
    }

    try:
        # 发送 POST 请求
        response = requests.post(api_url, headers=headers, json=data, timeout=90.0)
        response.raise_for_status()  # 检查请求是否成功

        # 解析响应内容
        result = response.json()
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("响应中缺少 'choices' 字段或内容为空")
        return result["choices"][0]["message"]["content"]  # 返回生成的文本
    except requests.exceptions.RequestException as e:
        # 处理请求异常
        raise RuntimeError(f"请求失败: {e}")
    except json.JSONDecodeError as e:
        # 处理 JSON 解析错误
        raise ValueError(f"响应内容不是有效的 JSON: {e}")
    except KeyError as e:
        # 处理字段缺失错误
        raise ValueError(f"响应内容缺少必要字段: {e}")
