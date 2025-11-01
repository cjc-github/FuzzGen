import os
import re
from Core.CustomAlgorithm import *
import json
from tqdm import tqdm

def extract_json_from_text(text):
    # 使用正则表达式查找 JSON 格式的字符串
    json_regex = r'\{.*?\}'
    json_strings = re.findall(json_regex, text, re.DOTALL)
    
    # 尝试解析每个找到的 JSON 字符串
    json_objects = []
    for json_str in json_strings:
        try:
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # 如果解析失败，跳过这个字符串
            # print("JSON Decode Failed")
            continue
    
    return json_objects

def get_return_dict(return_str,key_list):
    try:
        result_dict = extract_json_from_text(return_str)[0]
        for key_str in key_list:
            if key_str not in result_dict:
                return None
            if result_dict[key_str] is None:
                return None
        return result_dict
    except:
        # print(f"{return_str} decode error")
        return None
    
    
def load_log_file(file_name):
    with open(file_name,'rb') as f:
        content = f.read()
    content = bytearray2str(content)
    log_list = content.split(" - INFO - ")
    time_str = "2024-10-24 15:57:02"
    spliter= "-<,sp1it.>-"
    log_list = [x for x in log_list if len(x) != len(time_str)]
    all_data_dict = {}
    model_type = None
    for one_str in log_list:
        if "USE-MODEL-TYPE-S" in one_str:
            model_type = one_str.split("USE-MODEL-TYPE-S")[1].split("USE-MODEL-TYPE-E")[0]
            break
    for one_str in log_list:
        if spliter in one_str:
            content = one_str.split("<start>")[1].split("<end>")[0]
            hash_str = content.split(spliter)[0]
            types_str = content.split(spliter)[1]
            content_str = content.split(spliter)[2]
            if hash_str not in all_data_dict:
                all_data_dict[hash_str] = {}
            all_data_dict[hash_str][types_str] = content_str
    return all_data_dict,model_type

def refine_data(data_dict):
    new_dict = {}
    for key in data_dict:
        if "answer" not in data_dict[key]:
            continue
        if "question" not in data_dict[key]:
            continue
        tmp_dict = {}
        tmp_dict["answer"] = data_dict[key]["answer"]
        if "result" in data_dict[key]:
            tmp_dict['result'] = data_dict[key]["result"]
        new_dict[data_dict[key]["question"]] = tmp_dict
    return new_dict

def codeqwen_process(question,need_result):
    from Core.llamacpp import api as api
    # print(f"code qwen running {question}")
    new_question = f"<|im_start|>system\nYou are a helpful assistant<|im_end|>\n<|im_start|>user{question}<|im_end|>\n<|im_start|>assistant\n"
    result = api.run(new_question)
    response_dict = {}
    response_dict["answer"] = result
    # print(f"answer is {result}")
    if not need_result:
        return response_dict
    qustion_keys = extract_question_keys(question)
    return_dict = get_return_dict(result,qustion_keys)
    
    if return_dict:
        if len(qustion_keys) > 2:
            response_dict["result"] = return_dict
        elif len(qustion_keys) == 1:
            if "answer" in return_dict:
                if return_dict["answer"] == "yes":
                    response_dict["result"] = "True"
                elif return_dict["answer"] == "no":
                    response_dict["result"] = "False"
                else:
                    response_dict["result"] = return_dict["answer"] 
            else:
                response_dict['result'] = return_dict[list(return_dict.keys())[0]]
            
        elif len(qustion_keys) == 2:
            if "answer" in return_dict and "reason" in return_dict:
                if return_dict["answer"] == "yes":
                    response_dict["result"] = "True"
                elif return_dict["answer"] == "no":
                    response_dict["result"] = "False"
                else:
                    response_dict["result"] = return_dict["answer"] 
            elif "answer" in return_dict and "reason" not in return_dict:
                response_dict['result'] = return_dict
    # print(response_dict)
    return response_dict
    

def content_process(question,need_result):
    import Core.deepseek as api
    # print(f"content running {question}")
    result = api.run(question)
    response_dict = {}
    response_dict["answer"] = result
    # print(f"answer is {result}")
    if not need_result:
        return response_dict
    qustion_keys = extract_question_keys(question)
    return_dict = get_return_dict(result,qustion_keys)
    if return_dict:
        if len(qustion_keys) > 2:
            response_dict["result"] = return_dict
        elif len(qustion_keys) == 1:
            if "answer" in return_dict:
                if return_dict["answer"] == "yes":
                    response_dict["result"] = "True"
                elif return_dict["answer"] == "no":
                    response_dict["result"] = "False"
                else:
                    response_dict["result"] = return_dict["answer"] 
            else:
                response_dict['result'] = return_dict[list(return_dict.keys())[0]]
            
        elif len(qustion_keys) == 2:
            if "answer" in return_dict and "reason" in return_dict:
                if return_dict["answer"] == "yes":
                    response_dict["result"] = "True"
                elif return_dict["answer"] == "no":
                    response_dict["result"] = "False"
                else:
                    response_dict["result"] = return_dict["answer"] 
            elif "answer" in return_dict and "reason" not in return_dict:
                response_dict['result'] = return_dict
    # print(response_dict)
    return response_dict

def extract_question_keys(question):
    return_list = []
    if "{" not in question or "}" not in question:
        return None
    pattern = r'\{([^{}]+)\}'
    matches = re.findall(pattern, question)
    match = matches[0]
    all_list = match.split("\n")
    try:
        for one_str in all_list:
            if ":" in one_str and "\"" in one_str:
                return_list.append(one_str.split(":")[0].split("\"")[1])
    except:
        return []
    return return_list

'''
输出字典样式
key | value 
question | data_dict

data_dict:
key | value
model_type | response_dict

response_dict:
key | value
answer | answer_str
result(可选) | result_str

整体字典情况：

question -> model_type -> answer
                       -> result

一个例子

question -> codeqwen -> answer
                     -> result
         -> content  -> answer
                     -> result

'''
if __name__ == "__main__":
    target_floder = "log/"
    
    origin_data_path = "origin_data1.log"
    output_path = "origin_data1.log"
    if not origin_data_path:
        origin_data = {}
    else:
        with open(origin_data_path,'r') as f:
            origin_data = json.load(f)
    if not origin_data:
        # 加载数据
        for file_name in os.listdir(target_floder):
            all_data_dict,model_type = load_log_file(os.path.join(target_floder,file_name))
            if not model_type:
                continue
            # 由于不同进程用的种子不一样，计算得到的hash也不一样，因此每次加载数据，需要重新整理dict，用question作为key
            all_data_dict = refine_data(all_data_dict)
            for question in all_data_dict:
                if question in origin_data:
                    if model_type in origin_data[question]:
                        origin_data[question][model_type]["answer"] = all_data_dict[question]['answer']
                        if "result" in all_data_dict[question]:
                            origin_data[question][model_type]["result"] = all_data_dict[question]['result']
                    else:
                        response_dict = {}
                        response_dict["answer"] = all_data_dict[question]['answer']
                        if "result" in all_data_dict[question]:
                            response_dict["result"] = all_data_dict[question]['result']
                        origin_data[question][model_type] = response_dict
                else:
                    tmp_data_dict = {}
                    response_dict = {}
                    response_dict["answer"] = all_data_dict[question]['answer']
                    if "result" in all_data_dict[question]:
                        response_dict["result"] = all_data_dict[question]['result']
                    tmp_data_dict[model_type] = response_dict
                    origin_data[question] = tmp_data_dict

    # tmp_dict = {}
    # for question in origin_data:
    #     if len(origin_data[question].keys()) == 2:
    #         tmp_dict[question] = origin_data[question]
    # with open(output_path,'w') as f:
    #     json.dump(tmp_dict,f)
    # os._exit(0)

    # 梳理数据
    codeqwen_process_list = []
    content_process_list = []
    for question in tqdm(origin_data):
        if len(origin_data[question].keys()) < 2:
            if "codeqwen" not in origin_data[question]:
                if "result" in origin_data[question]["content"]:
                    need_result = True
                else:
                    need_result = False
                response_dict = codeqwen_process(question,need_result)
                origin_data[question]['codeqwen'] = response_dict
                with open(output_path,'w') as f:
                    json.dump(origin_data,f)
            # else:
            #     if "result" in origin_data[question]["codeqwen"]:
            #         need_result = True
            #     else:
            #         need_result = False
            #     response_dict = content_process(question,need_result)
            #     origin_data[question]['content'] = response_dict
            #     with open(output_path,'w') as f:
            #         json.dump(origin_data,f)


            # if "result" in origin_data[question]["codeqwen"]:
            #     if origin_data[question]["codeqwen"]['result'] != origin_data[question]["content"]['result']:
            #         print(question)
        
    # save the data
    with open(output_path,'w') as f:
        json.dump(origin_data,f)
    
    
    