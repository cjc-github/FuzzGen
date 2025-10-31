from Core.APIWarp import *
import json

with open("Core/api_config.json", "r") as f:
    api_config = json.load(f)

'''
{
    "url":"10.17.188.201",
    "port":7070
}
'''
url = api_config["url"]
port = api_config["port"]
api = llamacpp(url,port)