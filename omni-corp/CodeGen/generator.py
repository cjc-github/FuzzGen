import os
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
from transformers import AutoTokenizer
import argparse
from Data import *
from APIWarp import *
import json
import re
from logger_config import logger



GeneratorInstruction = "Based on the functions or class listed below and their descriptions, write a libfuzzer to test as many of the following codes as possible."

ClassInstruction = '''
下面几个类/函数应该放到几个libfuzzer中进行测试，只分析定义的函数，而不管调用的函数，用json格式输出，下面是一个输出示例
{
    "libfuzzer1":["function1","function2"],
    "libfuzzer2":["function1","function3","function5"],
    ...
}
'''
SummaryInstruction = '''
用生成libfuzzer的标准，用尽可能短的文字总结下面的函数，要求能够根据函数总结就能准确的生成一个libfuzzer
'''
USE_MODEL_TYPE = "mistral"
URL = "10.17.188.201"
PORT =7070

def print_red(text):
    print(f"\033[91m{text}\033[0m")

def print_green(text):
    print(f"\033[92m{text}\033[92m")

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
            print("JSON Decode Failed")
            continue
    
    return json_objects

def classFunctions(func_body_list):
    question = {}
    question['Instruction'] = ClassInstruction
    content = ""
    for func_body in func_body_list:
        content +=  "\"\"\"\n"+func_body + '\n\"\"\"\n'
    question['Input'] = content
    class_prompt = Prompt(USE_MODEL_TYPE)
    prompt_str = class_prompt.gen_prompt(question)
    logger.info(prompt_str)

    api = llamacpp(host=URL,port=PORT)
    result = api.run(prompt_str)
    logger.info(result)
    return result

def get_func_summary(func_body):
    question = {}
    question['Instruction'] = SummaryInstruction
    question['Input'] = func_body
    summary_prompt = Prompt(USE_MODEL_TYPE)
    prompt_str = summary_prompt.gen_prompt(question)
    api = llamacpp(host=URL,port=PORT)
    result = api.run(prompt_str)
    logger.info(result)
    return result

def get_func_by_name(func_name,func_dict_list):
    for func_dict in func_dict_list:
        if func_dict['name'] == func_name:
            return func_dict
    return None


def gen_libfuzzer(func_name_list,func_dict_list):
    question = {}
    question['Instruction'] = GeneratorInstruction

    content = ""
    tmp_func_dict_list = []
    for func_name in func_name_list:
        tmp_dict = get_func_by_name(func_name,func_dict_list)
        if tmp_dict:
            tmp_func_dict_list.append(tmp_dict)

    parm_set = set()
    if tmp_func_dict_list:
        for func_dict in tmp_func_dict_list:
            content += "//" + func_dict['contain'] + "\n" +func_dict['body'] + "\n"
            for one_parm in func_dict['parm']:
                parm_set.add(one_parm)
            if len(func_dict['return']) > 1:
                parm_set.add(func_dict['return'])
        for parm_str in parm_set:
            content += parm_str + "\n"
        question['Input'] = content
        generation_prompt = Prompt(USE_MODEL_TYPE)
        prompt_str = generation_prompt.gen_prompt(question)
        logger.info(prompt_str)
        api = llamacpp(host=URL,port=PORT)
        for _ in range(4):
            result = api.run(prompt_str)
            logger.info(result)
            print_green(result)
            print("\n\n")
        return result
    else:
        print(f"cannot find the function {func_name_list}")



    






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='目标函数文件')
    args = parser.parse_args()
    logger.info("Generator Starts")
    func_dict_file = args.input
    with open(func_dict_file,'r') as f:
        target_func_list = json.load(f)
    func_list = []
    for func_dict in target_func_list:
        if func_dict['type'] == 'function':
            logger.info(func_dict['name'])
            tmp_summary = get_func_summary(func_dict['body'])
            func_body = func_dict['body']
            func_head = func_body.split('{')[0]
            func_body = func_head + "{\n\\\\" + tmp_summary + "}\n" 
            func_dict['body'] = func_body
            func_list.append(func_body)
    result = classFunctions(func_list)
    func_list = extract_json_from_text(result)
    target_func_name_list = []
    for one_dict in func_list:
        logger.info(one_dict)
        tmp_dict_list = []
        for key in one_dict:
            if one_dict[key]:
                target_func_name_list.append(one_dict[key])
    for one_list in target_func_name_list:
        gen_libfuzzer(one_list,target_func_list)
    
    
    





