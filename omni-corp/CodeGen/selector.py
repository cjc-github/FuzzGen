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
import networkx as nx
import deepseek

# 选择一个函数并不难，难点在于如何正确拒绝所有的不合适的函数。如何一步步排除那些本就不需要的函数呢？
# 两个函数如果存在相互调用的关系，那么就需要放到一起去作为selector的函数
# 如何将函数的筛选放到整个工程的环境下进行？
# 核心问题是什么？ 各种函数相互之间的逻辑关系，需要用语义来进行聚类。
# 对于C代码来说，如果函数之间互相有调用，那么就应该用selector来筛选。
# 对于C++代码来说，如果类与类之间有调用，那么在generate 的时候就应该放在一起生成。

SelectorInstruction = '''
Which function below is suitable to serve as the target test function for libfuzzer? You can choose multiple functions, output the function in JSON format and output none if no function is suitable. The following is an example of output:
{
    "target":["function name" or "None"]
}
'''
'''
Among the functions listed below, are there any suitable for use as a function in libfuzzer? Please output your response in the following format. The following is an example of output:Exclude the unit test functions and too simple functions. 
{
    "target":["function name" or "None"]
}
'''


# 主要流程：
# 获取各个文件的函数和类
# 根据文件和类的函数进行筛选
# 根据筛选结果生成libfuzzer
Code_suffix = {".cpp",".c",".h",".hpp",".cxx",".cc",".C",".inl",".c++",".h++",".hcc",".hh",".h++",".incl_cpp"}
Spliter = "\"\"\""
prompt1 = '''
下面的类是否适合作为libfuzzer的测试目标，用json格式输出,下面是一个输出示例
{
    "suitable":"yes" or "no",
    "reason" : "reason for the class is or not suitable as a target for libfuzzer"
}
'''
prompt2 = '''
下面几个类/函数应该放到几个libfuzzer中进行测试，用json格式输出，下面是一个输出示例
{
    "libfuzzer1":["class1","class2"],
    "libfuzzer2":["class1","class3","class5"],
    ...
}
'''

'''
A suitable target test function for libfuzzer typically has the following characteristics:

It takes a pointer to the input data and the size of the input data as parameters.
It performs some operations on the input data that could potentially trigger bugs or crashes.
It doesn't return a value but rather crashes or exhibits unexpected behavior if a bug is found.
'''

model_path = "D:/models/codeqwen"
# model_path = "/root/llama/qwen1.5/"
MAX_TOKEN_NUM = 6* 1024
USE_MODEL_TYPE = "mistral"
USE_MODEL_TYPE = "content"
# USE_MODEL_TYPE = "chatglm"

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

def split_list_into_n_parts(lst, n):
    total_sum = sum(lst)
    sorted_lst = sorted(lst)
    avg = total_sum / n
    result = []
    temp = []
    current_sum = 0
    for num in sorted_lst:
        if current_sum + num <= avg:
            temp.append(num)
            current_sum += num
        else:
            result.append(temp)
            temp = [num]
            current_sum = num
    result.append(temp)
    return result

'''
分割函数，同一次识别的函数个数不超过9个，且在一起的函数长度不能超过最大token数量
'''
def split_func_list(tokenizer,func_list):
    return_list = []
    tmp_list = []
    count = 0
    for i,one_func in enumerate(func_list):
        tmp_list.append(one_func)
        tmp_prompt_str = construt_prompt_str(tmp_list)
        count += 1
        if get_str_token_num(tokenizer,tmp_prompt_str) > MAX_TOKEN_NUM:
            if len(tmp_list) ==1:
                return_list.append(tmp_list[:])
                tmp_list = []
                count = 0
            else:
                tmp_list.pop()
                return_list.append(tmp_list[:])
                tmp_list = [one_func]
                count = 1
        elif count > 8:
            return_list.append(tmp_list[:])
            tmp_list = []
            count = 0

    if tmp_list:
        return_list.append(tmp_list)
    return return_list

def get_str_token_num(tokenizer,prompt_str):
    model_inputs = tokenizer(prompt_str)
    return len(model_inputs['input_ids'])


def bytearray2str(target_str):
    if type(target_str) == type('123'):
        return target_str
    else:
        return target_str.decode('utf-8',errors='ignore')
    

def construt_prompt_str(func_list):
    question = {}
    question['Instruction'] = SelectorInstruction
    # print(SelectorInstruction)
    content = ""
    for one_func in func_list:
        content += '\n\'\'\'\n' + bytearray2str(one_func.body)+ '\n\'\'\'\n' 
    question['Input'] = content
    selection_prompt = Prompt(USE_MODEL_TYPE)
    prompt_str = selection_prompt.gen_prompt(question)
    return prompt_str


def get_func_by_name(func_name,func_list):
    for one_func in func_list:
        tmp_body  = bytearray2str(one_func.body)
        tmp_func_name = tmp_body.split("{")[0].split('(')[0]
        if func_name in tmp_func_name:
            return one_func
        # if one_func.name.decode('utf-8',errors='ignore') == func_name:
        #     return one_func
    return None

def get_class_by_name(class_name,class_list):
    for one_class in class_list:
        if class_name == one_class.name.decode('utf-8',errors='ignore'):
            return one_class
    return None

def run_prompt(prompt_str):
    func_list_dict = {}
    result = api.run(prompt_str)
    # result = deepseek.run(prompt_str)
    result_dict_list = extract_json_from_text(result)
    func_list = []
    
    if result_dict_list:
        for result_dict in result_dict_list:
            if "target" in result_dict:
                func_list += result_dict['target']

    if str(func_list) in func_list_dict:
        func_list_dict[str(func_list)] += 1
    else:
        func_list_dict[str(func_list)] = 1


def run_llm_get_result(prompt_str,all_funcs):
    max_run_times = 16
    count = 0
    target_func_list = []
    logger.info(prompt_str)
    while not target_func_list:
        if count > max_run_times:
            return []
        func_list = []
        result = api.run(prompt_str)
        # result = deepseek.run(prompt_str)
        logger.info(f"[run_llm_get_result] [Response] : {result}")
        result_dict_list = extract_json_from_text(result)
        logger.info(f"[run_llm_get_result] [result list] : {result_dict_list}")
        if result_dict_list:
            for result_dict in result_dict_list:
                if "target" in result_dict:
                    func_list += result_dict['target']
        for func_name in func_list:
            if "None" == func_name:
                return []
            one_func = get_func_by_name(func_name,all_funcs)
            if one_func:
                logger.info(f"[run_llm_get_result] get one func {one_func.name}")
                target_func_list.append(one_func)
        count += 1

    return target_func_list

def find_func_by_call(func_list:list,one_call:caller):
    for one_func in func_list:
        if one_func.type == "function":
            if one_call.func_name == one_func.name:
                if not one_func.class_list and not one_call.name_space_list:
                    return one_func
                elif one_func.class_list and one_call.name_space_list:
                    if one_func.class_list[0] == one_call.name_space_list[0]:
                        return one_func
    return None

def func_get_class(one_func:func,class_dict:dict):
    if not one_func.class_list:
        return None
    for class_name in one_func.class_list[::-1]:
        if class_name in class_dict:
            return class_dict[class_name]
    return None
def generate_list(target_func_list,G,tokenizer):
    return_list = []
    for one_func in target_func_list:
        if one_func.type == 'function':
            logger.info(f"last process {one_func.name}")
            tmp_list = [one_func]
            ancestors = list(nx.ancestors(G,one_func))
            logger.info(f"ancestors is {ancestors}")
            if ancestors:
                all_list = split_func_list(tokenizer,ancestors)
                for one_list in all_list:
                    tmp_list = one_list + [one_func]
                    return_list.append(tmp_list[:])

            if list(G.successors(one_func)):
                all_list = split_func_list(tokenizer,list(G.successors(one_func)))
                for one_list in all_list:
                    tmp_list = one_list + [one_func]
                    return_list.append(tmp_list[:])
    return return_list




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='目标工程文件夹')
    parser.add_argument('-o','--output',type=str,help="输出json文件路径")
    args = parser.parse_args()
    if not os.path.exists("config.json"):
        print("[FATAL] no config.json")
        os._exit(0)
    with open("config.json",'r') as f:
        config_dict = json.load(f)
    model_path = config_dict['modelpath']
    USE_MODEL_TYPE = config_dict['prompttype']

    logger.info("Selector Start")
    input_dir = args.input  
    output_json_path = args.output
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    api = llamacpp(host="10.17.188.201",port=7070)

    initial_target_funcs_list = []
    target_class_list = []
    G = nx.DiGraph()
    if os.path.exists(input_dir):
        logger.info(f"processing {input_dir}")
        target_project = CXXProject(input_dir)
        target_project.parse_readme_file()
        target_project.process()
        for one_func in target_project.all_funcs:
            if bytearray2str(one_func.name) in {"main","LLVMFuzzerTestOneInput"}:
                continue
            if one_func.call_list:
                for one_call in one_func.call_list:
                    tmp_func = find_func_by_call(target_project.all_funcs,one_call)
                    if tmp_func:
                        G.add_edge(one_func,tmp_func)
        
        logger.info(f"readme is  {target_project.readme}")
        if target_project.readme:
            SelectorInstruction = f"根据下面的总体要求 {target_project.readme}\n 请按照以上要求，" + SelectorInstruction
        all_funcs = target_project.all_funcs

        for file_name in target_project.all_file_obj_dict:
            # 先剔除不符合要求的函数
            candi_list = []
            for of in target_project.all_file_obj_dict[file_name].func_list:
                if bytearray2str(of.name) in {"main","LLVMFuzzerTestOneInput"}:
                    continue
                if of not in G.nodes():
                    continue
                candi_list.append(of)
            tmp_func_group_list = split_func_list(tokenizer,candi_list)
            for func_group in tmp_func_group_list:
                prompt_str = construt_prompt_str(func_group)
                print(f"初步筛选 {func_group}")
                target_func_list = run_llm_get_result(prompt_str,func_group)
                target_func_list = list(set(target_func_list))
                print(f"初步筛选得到 {target_func_list}\n\n")
                for one_func in target_func_list:
                    initial_target_funcs_list.append(one_func)
                    if one_func.class_list:
                        one_class = func_get_class(one_func,target_project.all_class_dict)
                        if one_class:
                            target_class_list.append(one_class)


        # prompt_list = []
        # prompt_func_list = []
        # for file_name in target_project.all_file_obj_dict:
        #     # logger.info(f"processing {file_name}")
        #     tmp_class_dict = {}
        #     for one_func in target_project.all_file_obj_dict[file_name].func_list:
        #         # 那些孤岛的函数不分析
        #         if one_func not in G.nodes():
        #             continue
        #         if bytearray2str(one_func.name) in {"main","LLVMFuzzerTestOneInput"}:
        #             continue
        #         str_class_list = str(one_func.class_list)
        #         if str_class_list in tmp_class_dict:
        #             tmp_class_dict[str_class_list].append(one_func)
        #         else:
        #             tmp_class_dict[str_class_list] = [one_func]
        #     for str_class_list in tmp_class_dict:
        #         all_func_list = tmp_class_dict[str_class_list][:]
        #         tmp_prompt_str = construt_prompt_str(all_func_list)
        #         if get_str_token_num(tokenizer,tmp_prompt_str) < MAX_TOKEN_NUM:
        #             prompt_list.append(tmp_prompt_str)
        #             prompt_func_list.append(all_func_list)
        #         else:
        #             len_list = []
        #             len_dict = {}
        #             for i,one_func in enumerate(all_func_list):
        #                 if one_func.name == b'main':
        #                     continue
        #                 tmp_len = get_str_token_num(tokenizer,bytearray2str(one_func.body))
        #                 if tmp_len > MAX_TOKEN_NUM:
        #                     continue
        #                 len_list.append(tmp_len)
        #                 len_dict.setdefault(tmp_len, []).append(i)
        #             if len(all_func_list) > 2:
        #                 len_dict_str = json.dumps(len_dict)
        #                 for n in range(2,len(all_func_list)):
        #                     tmp_len_dict = json.loads(len_dict_str)
        #                     tmp_len_list = len_list[:]
        #                     tmp_prompt_str_list = []
        #                     is_valid_partition = True
        #                     parted_list = split_list_into_n_parts(tmp_len_list, n)
        #                     for one_list in parted_list:
        #                         tmp_func_list = []
        #                         for one_len in one_list:
        #                             index = tmp_len_dict[str(one_len)].pop()
        #                             tmp_func_list.append(all_func_list[index])
        #                         tmp_prompt_str = construt_prompt_str(tmp_func_list)
        #                         if get_str_token_num(tokenizer,tmp_prompt_str) < MAX_TOKEN_NUM:
        #                             tmp_prompt_str_list.append(tmp_prompt_str)
        #                             prompt_func_list.append(tmp_func_list)
        #                         else:
        #                             is_valid_partition = False
        #                             break
        #                     if is_valid_partition:
        #                         prompt_list += tmp_prompt_str_list
        #                         break

        # for i,prompt_str in enumerate(prompt_list):
        #     # 用LLM生成结果
        #     # print(prompt_str)
        #     print(f"初步筛选函数{prompt_func_list[i]}")
        #     target_func_list = run_llm_get_result(prompt_str,prompt_func_list[i])
        #     print(f"筛选得到{target_func_list}\n\n")
        #     for one_func in target_func_list:
        #         # initial_target_funcs_list.append(one_func.gen_func_dict())
        #         initial_target_funcs_list.append(one_func)
        #         if one_func.class_list:
        #             one_class = func_get_class(one_func,target_project.all_class_dict)
        #             if one_class:
        #                 # initial_target_funcs_list.append(one_class)
        #                 target_class_list.append(one_class)

        for one_func in initial_target_funcs_list:
            logger.info(f"Initially, chosse function name {one_func.name} {one_func.class_list}")
            print(f"初筛得到函数{one_func.name}, 属于{one_func.class_list}类")
        for one_class in target_class_list:
            logger.info(f"choose target class name is {one_class.name}")
                # print(func_dict['name'])
            # print(target_funcs_list)
        final_func_list = []
        tmp_final_func_list = []
        discard_func_list = []
        if initial_target_funcs_list:
            related_list = generate_list(initial_target_funcs_list,G,tokenizer)
            for func_list in related_list:
                print(f"最后参与筛选的函数{func_list}")
                prompt_str = construt_prompt_str(func_list)
                tmp_list = run_llm_get_result(prompt_str,func_list)
                print(f"筛选得到{tmp_list}")
                discard_func_list += list(set(func_list) - set(tmp_list))
                print(f"被淘汰的函数有{list(set(func_list) - set(tmp_list))}\n\n")
                tmp_final_func_list += tmp_list

            discard_func_list = list(set(discard_func_list))
            print(f"总共被淘汰的函数有{discard_func_list}")
            for one_func in list(set(initial_target_funcs_list) - set(discard_func_list)):
                print(f"最终得到 {bytearray2str(one_func.name)}")
                logger.info(f"finnal get {one_func.name} {one_func.class_list}")
                final_func_list.append(one_func)

        if not final_func_list:
            print("Failed please rerun this script")
        # final_func_list = list(set(final_func_list))
        # del_list = []
        # for one_func in final_func_list:
        #     tmp_body = bytearray2str(one_func.body)
        #     if len(tmp_body.split("\n")) < 7:
        #         logger.info(f"deleting {one_func.name} {one_func.class_list}")
        #         del_list.append(one_func)
        # for one_func in del_list:
        #     final_func_list.remove(one_func)

        final_func_dict_list = []
        for one_func in final_func_list:
            final_func_dict_list.append(one_func.gen_func_dict())
        with open(output_json_path,'w') as f:
            json.dump(final_func_dict_list,f)

    else:
        print(f"[FATAL] {input_dir} not exists")



    
 
        
            
        
        
    

    