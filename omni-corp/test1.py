import requests

# 替换为你的 DeepSeek API 密钥
API_KEY = 'sk-f606c156208842f391806c4213bb8344'

# DeepSeek API 的端点
API_URL = 'https://api.deepseek.com/v1/chat/completions'

def ask_deepseek(question):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'deepseek-chat',  # 替换为你想使用的模型
        'messages': [
            {'role': 'user', 'content': question}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"

if __name__ == "__main__":
    question = input("请输入你的问题: ")
    answer = ask_deepseek(question)
    print("DeepSeek 的回答: ", answer)