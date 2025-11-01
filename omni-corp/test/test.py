import requests
import json
import random

file_path = "C:/Code/OmniCorp/qadata/909-1.83_Selector_QA.json"
with open(file_path,'r') as f:
    all_list = json.load(f)
index = random.randint(0,len(all_list))
body = all_list[index]["instruction"] + "\n\n" + all_list[index]["input"]

print(all_list[index]["input"])

url = "http://36.103.203.24:5903/v1/chat/completions/"
url = "http://10.17.188.201:5000/v1/chat/completions/"
headers = {
        "Content-Type": "application/json"
            }
data = {
    "stream":False,
    "messages":[
    {"role":"user",
    "content":body}
    ]
}
response = requests.post(url, json=data, headers=headers)
result = response.text
result = json.loads(result)
result = result['choices'][0]['message']['content']
print("LLM output is:")
print(result)
print("Real output is:")
print(all_list[index]["output"])