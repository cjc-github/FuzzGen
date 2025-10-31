from Gen import *
from Core.GenData import *
from Core.CustomAlgorithm import *
from Core.CustomStructure import *
from Core.APIWarp import *
from Core.Utils import *
from Core.api import *
import json
import argparse
from transformers import AutoTokenizer
import networkx as nx
import re
from Core.logger import logger
import random
from promptINS import *
from collections import Counter


model_type = "codeqwen"

def remove_inclusive(G,func_list):
    forbid_list = []
    for one_func in func_list:
        for two_func in func_list:
            if one_func == two_func:
                continue
            if nx.has_path(G,one_func,two_func):
                # print(one_func,two_func)
                forbid_list.append(two_func)

            if nx.has_path(G,two_func,one_func):
                # print(two_func,one_func)
                forbid_list.append(one_func)
    return_list = list(set(func_list) - set(forbid_list))
    return return_list
 
def get_return_dict(return_str,key_list):
    try:
        result_dict = extract_json_from_text(return_str)[0]
        for key_str in key_list:
            if key_str not in result_dict:
                return None
            if not result_dict[key_str]:
                return None
        return result_dict
    except:
        # print(f"\n{return_str}\ndecode error")
        return None
    
def clear_parm_name(parm_name):
    return_name = parm_name
    return_name = return_name.replace("struct ","")
    return_name = return_name.replace("const ","")
    return_name = return_name.replace("static ","")
    return_name = return_name.replace("*","")
    return_name = return_name.replace("&","")
    return_name = return_name.replace(" ","")
    return return_name
def RUN_Prompt_is_func_contain_file_op(one_func,run_count=1):
    # 通过设置多次执行，提升结果准确率
    prompt_str = construct_prompt_str(INS_function_file_op(),bytearray2str(one_func.body),model_type)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False
        
def RUN_Prompt_is_func_contain_memory_load_parameter(one_func,run_count=1):
    prompt_str = construct_prompt_str(INS_function_memory_load(),bytearray2str(one_func.body),model_type)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_is_func_contain_memory_size_parameter(one_func,run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_memory_size(),bytearray2str(one_func.body),model_type)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(f"{prompt_str}\n{result}")
        result_dict = get_return_dict(result,["answer","pointer_name","size_name"])
        if result_dict:
            count += 1
            if "no" in result_dict["answer"]:
                answer_list.append(False)
                continue
            if result_dict["pointer_name"] not in bytearray2str(one_func.body).split("{")[0]:
                answer_list.append(False)
                continue
            if result_dict["size_name"] not in bytearray2str(one_func.body).split("{")[0]:
                answer_list.append(False)
                continue
            answer_list.append(True)

    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False
def RUN_prompt_check_memory_pointer(one_func,pointer_name,run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer(pointer_name),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            # yes表示pointer指向的内存为路径、文件或者结构体等不符合要求的信息
            if "yes" in result_dict["answer"]:
                answer_list.append(False)
            else:
                answer_list.append(True)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False
def RUN_prompt_check_pointer_size(one_func,pointer_name,size,run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_check_pointer_size(pointer_name,size),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result =run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_is_func_contain_memory_pointer(one_func,run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","pointer_name"])
        if result_dict:
            count += 1
            if "yes" in result_dict["answer"]:
                pointer_name = result_dict["pointer_name"]
                if pointer_name in bytearray2str(one_func.body).split("{")[0].split("(")[1]:
                    answer_list.append(True)
                else:
                    answer_list.append(False)
            else:
                answer_list.append(False)
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False
    

def select_memory_pointer_func(one_func,run_count=1):
    # 如果函数能够直接通过两层测试，那么就可以直接说明函数是包含连续内存参数的函数，一次通过则不需要多次测试。否则则进行多次测试。
    count = 0
    prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),bytearray2str(one_func.body),model_type)
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","pointer_name"])
        if result_dict:
            count += 1
            if "yes" not in result_dict["answer"]:
                continue
            pointer_name = result_dict["pointer_name"]
            if pointer_name not in bytearray2str(one_func.body).split("{")[0].split("(")[1]:
                continue
            if RUN_prompt_check_memory_pointer(one_func,pointer_name,1):
                return True
    return False

def select_memory_pointer_size_func(one_func,run_count=1):
    # 如果函数能够直接通过三层测试，那么就可以直接说明函数是包含连续内存参数的函数，一次通过则不需要多次测试。否则则进行多次测试。
    count = 0
    prompt_str = construct_prompt_str(INS_parameter_memory_size(),bytearray2str(one_func.body),model_type)
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","pointer_name","size_name"])
        if result_dict:
            count += 1
            if "yes" not in result_dict["answer"]:
                continue
            pointer_name = result_dict["pointer_name"]
            if pointer_name not in bytearray2str(one_func.body).split("{")[0].split("(")[1]:
                continue
            size = result_dict["size_name"]
            if size not in bytearray2str(one_func.body).split("{")[0].split("(")[1]:
                continue
            if not RUN_prompt_check_memory_pointer(one_func,pointer_name,1):
                continue
            if RUN_prompt_check_pointer_size(one_func,pointer_name,size,1):
                return True
    return False

def select_two_parameter_funcs(target_func_list,run_count=1):
    return_list = []
    for one_func in target_func_list:
        # if RUN_Prompt_is_func_contain_memory_size_parameter(one_func,run_count):
        if select_memory_pointer_size_func(one_func,run_count):
            return_list.append(one_func)
    return return_list

def select_one_paramter_funcs(func_list,run_count=1):
    return_list = []
    for one_func in func_list:
        # if RUN_Prompt_is_func_contain_memory_pointer(one_func,run_count):
        if select_memory_pointer_func(one_func,run_count):
            return_list.append(one_func)
    return return_list
def RUN_Prompt_get_func_classify(one_func):
    prompt_str = construct_prompt_str(INS_function_classify(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    while True:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","reason"])
        if result_dict is not None:
            return result_dict

def RUN_Prompt_get_func_destory(one_func):
    prompt_str = construct_prompt_str(INS_parameter_destory_struct(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    while True:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","destroy_parameter_type"])
        if result_dict is not None:
            return result_dict

def get_func_destory_object(one_func,project,run_count=1):
    count = 0
    answer_list = []
    while count < run_count:
        count += 1
        answer_dict = RUN_Prompt_get_func_destory(one_func)
        if "yes" in answer_dict["answer"]:
            parm_name = answer_dict["destroy_parameter_type"]
            parm_name = clear_parm_name(parm_name)
            byte_parm_name = bytes(parm_name.encode("utf-8"))
            if byte_parm_name in project.all_class_dict:
                # return project.all_class_dict[byte_parm_name]
                answer_list.append(project.all_class_dict[byte_parm_name])
            else:
                answer_list.append("N/A")
        else:
            answer_list.append(None)
            
    element_counts = Counter(answer_list)
    most_common_element = element_counts.most_common(1)
    return most_common_element[0][0]
def is_func_destory(one_func,run_count=1):
    count = 0
    answer_list = []
    while count < run_count:
        classify_dict = RUN_Prompt_get_func_classify(one_func)
        count += 1
        if "C" in classify_dict["answer"]:
            answer_list.append(True)
        else:
            answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_is_func_contain_global_rw(one_func,run_count=1):
    prompt_str = construct_prompt_str(INS_function_global_variable_write(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)
    
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False


def RUN_Prompt_is_func_init_function(one_func,run_count=1):
    prompt_str = construct_prompt_str(INS_function_init(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict is not None:
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False


def RUN_Prompt_is_func_parm_is_init(one_func,parm_name,run_count=1):    
    prompt_str = construct_prompt_str(INS_function_struct_init(parm_name),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict is not None:
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_is_func_parm_struct_init(one_func,parm_name,run_count=1):
    prompt_str = construct_prompt_str(INS_function_parm_struct_init(parm_name),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","reason"])
        if result_dict is not None:
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_is_func_return_struct_init(one_func,parm_name,run_count=1):
    logger.info(f"RUN_Prompt_is_func_return_struct_init({one_func.name},{parm_name},{run_count})")
    prompt_str = construct_prompt_str(INS_function_return_struct_init(parm_name),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","reason"])
        if result_dict is not None:
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        logger.info(f"RUN_Prompt_is_func_return_struct_init({one_func.name},{parm_name},{run_count}) return True")
        return True
    else:
        logger.info(f"RUN_Prompt_is_func_return_struct_init({one_func.name},{parm_name},{run_count}) return False")
        return False
        
def RUN_Prompt_is_func_parm_return(one_func,parm_name,run_count=1):
    logger.info(f"RUN_Prompt_is_func_parm_return {one_func.name} {parm_name}")
    prompt_str = construct_prompt_str(INS_parameter_struct_is_return(parm_name),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,['answer',"variable_name","reason"])
        if result_dict is not None:
            count += 1
            if "yes" in result_dict['answer']:
                func_parameter = bytearray2str(one_func.body).split("{")[0].split("(")[1]
                func_parameter_list = func_parameter.split(",")
                is_contain = False
                for parm_str in func_parameter_list:
                    if result_dict["variable_name"] in parm_str and parm_name in parm_str:
                        is_contain = True
                        break
                if is_contain:
                    answer_list.append(True)
                else:
                    answer_list.append(False)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

def RUN_Prompt_get_func_parm_return(one_func):
    prompt_str = construct_prompt_str(INS_parameter_input_paramter_is_return(),bytearray2str(one_func.body),model_type)
    logger.info(prompt_str)
    while True:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","variable_name","variable_type","reason"])
        if result_dict is not None:
            return result_dict

def get_func_parm_as_return_struct_list(one_func,project,run_count=1):
    # 针对函数的每个输入参数，检测其是否是传引用。
    # 这里判断函数是否对输入参数进行初始化进行判断。因为有些更改输入参数指针的行为也容易被误判为传引用。
    logger.info(f"get_func_parm_as_return_struct_list({one_func.name},{one_func.parm_list},{run_count})")
    return_list = []
    if len(one_func.parm_list) == 0:
        return return_list
    for one_parm in one_func.parm_list:
        if one_parm.name not in project.all_class_dict:
            continue
        if RUN_Prompt_is_func_parm_struct_init(one_func,bytearray2str(one_parm.name),run_count):
            return_list.append(one_parm)
    logger.info(f"get_func_parm_as_return_struct_list({one_func.name},{one_func.parm_list},{run_count}) return {return_list}")
    return return_list

    

def get_func_parm_as_return_struct(one_func,project,run_count=1):
    # return_list = []
    count = 0
    answer_list = []
    while count < run_count:
    # 首先确定是否存在
        count += 1
        answer_dict = RUN_Prompt_get_func_parm_return(one_func)
        if "yes" not in answer_dict['answer']:
            answer_list.append(None)
            continue
        parm_name = clear_parm_name(answer_dict["variable_type"])
        byte_parm_name = bytes(parm_name.encode("utf-8"))
        if byte_parm_name not in project.all_class_dict:
            answer_list.append(None)
            continue
        # 通过具体变量名二次确认，下面函数可以根据情况变成判断参数是否被初始化
        if not RUN_Prompt_is_func_parm_return(one_func,parm_name):
            answer_list.append(None)
            continue
        answer_list.append(project.all_class_dict[byte_parm_name])                                    

            
    # return return_list
    element_counts = Counter(answer_list)
    most_common_element = element_counts.most_common(1)
    return most_common_element[0][0]

def RUN_Prompt_get_func_return(one_func):
    prompt_str = construct_prompt_str(INS_parameter_return_value(),bytearray2str(one_func.body),model_type)
    while True:
        result = run_llm_custom(prompt_str)
        logger.info(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["return_parameter_type"])
        if result_dict is not None:
            return result_dict
def get_func_return_struct(one_func,project,run_count=1):
    logger.info(f"get_func_return_struct({one_func.name},{one_func.return_parm},{run_count})")
    count = 0
    answer_list = []
    while count < run_count:
        count += 1
        answer_dict = RUN_Prompt_get_func_return(one_func)
        parm_name = clear_parm_name(answer_dict["return_parameter_type"])
        logger.info(f"{one_func.name}'s return parm name is {parm_name}")
        byte_parm_name = bytes(parm_name.encode("utf-8"))
        if byte_parm_name in project.all_class_dict:
            logger.info(f"{one_func.name}'s return struct is {project.all_class_dict[byte_parm_name]}")
            answer_list.append(project.all_class_dict[byte_parm_name])
        else:
            logger.info(f"{one_func.name} cannot find struct {byte_parm_name}")
            answer_list.append(None)
    element_counts = Counter(answer_list)
    most_common_element = element_counts.most_common(1)
    logger.info(f"get_func_return_struct({one_func.name},{one_func.return_parm},{run_count}) return {most_common_element[0][0]}")
    return most_common_element[0][0]


def get_func_contain_target_parm(one_func,parm_list):
    return_list = []
    func_head = bytearray2str(one_func.body).split("{")[0]
    for one_parm in parm_list:
        parm_name = bytearray2str(one_parm.name)
        if parm_name in func_head:
            return_list.append(parm_name)
    return return_list

def filter_file_op_funcs(func_list,run_count=1):
    return_list = []
    for one_func in func_list:
        if not RUN_Prompt_is_func_contain_file_op(one_func,run_count):
            return_list.append(one_func)
    return return_list


def get_func_parm_struct_list(one_func,project):
    return_list = []
    for one_parm in one_func.parm_list:
        if one_parm.name in project.all_class_dict:
            return_list.append(project.all_class_dict[one_parm.name])
    return return_list
def analyze_funcs_parm(func_list,project,run_count=1):
    # 先将所有函数分析一遍参数,主要是输入和返回参数，以及这些参数是否涉及到初始化。
    for one_func in func_list:
        if one_func.is_func_analyzed():
            continue
        # 函数输入参数是否被函数初始化（为output_parm以及init parm)
        parm_struct_list = get_func_parm_as_return_struct_list(one_func,project,run_count)
        one_func.output_parm_set = set()
        one_func.init_parm_set = set()
        if parm_struct_list:
            for tmp_struct in parm_struct_list:
                if tmp_struct.name in project.all_class_dict:
                    one_func.output_parm_set.add(project.all_class_dict[tmp_struct.name])
                    one_func.init_parm_set.add(project.all_class_dict[tmp_struct.name])
        one_func.input_parm_set = set()
        for one_parm in one_func.parm_list:
            if one_parm.name in project.all_class_dict:
                tmp_struct = project.all_class_dict[one_parm.name]
                if tmp_struct not in one_func.output_parm_set:
                    one_func.input_parm_set.add(tmp_struct)
        # 查看函数返回值
        one_func.init_return_set = set()
        return_parm = get_func_return_struct(one_func,project,run_count)
        if not return_parm:
            # print(f"{one_func.name} input parm set {one_func.input_parm_set}")
            # print(f"{one_func.name} output parm set {one_func.output_parm_set}")
            # print(f"{one_func.name} init parm set {one_func.init_parm_set}")
            # print(f"{one_func.name} init return set {one_func.init_return_set}")
            # print("="*120)
            continue
        one_func.output_parm_set.add(return_parm)
        if RUN_Prompt_is_func_return_struct_init(one_func,bytearray2str(return_parm.name),run_count):
            if return_parm.name in project.all_class_dict:
                one_func.init_return_set.add(project.all_class_dict[return_parm.name])
        # print(f"{one_func.name} input parm set {one_func.input_parm_set}")
        # print(f"{one_func.name} output parm set {one_func.output_parm_set}")
        # print(f"{one_func.name} init parm set {one_func.init_parm_set}")
        # print(f"{one_func.name} init return set {one_func.init_return_set}")
        # print("="*120)
        


            
# 针对单个函数
def STATE_find_func_init(one_func,project,all_func_list,run_count=1):
    print(f"STATE INIT analyzing {one_func.name}")
    logger.info(f"STATE_find_func_init processing {one_func.name}")
    one_func.type = "input"
    one_func.input_parm_set = set()
    return_list = [one_func]
    tmp_list = []
    # struct_list = []
    analyze_funcs_parm([one_func],project,run_count)
    need_init_struct_list = list(one_func.input_parm_set)
    # parm_list = one_func.parm_list
    # for one_parm in parm_list:
    #     if one_parm.name in project.all_class_dict:
    #         struct_list.append(project.all_class_dict[one_parm.name])
    # need_init_struct_list = []
    # for one_struct in struct_list:
    #     # TODO下一步增加多重校验功能
    #     # 查看目标函数的参数是否有作为返回值的情况，根据一般开发规律，函数输入参数结构体作为返回值，在存在输入为连续内存的情况下，这个函数参数只有被初始化的情况下才会被返回
    #     logger.info(f"STATE_find_func_init RUN_Prompt_is_func_parm_struct_init {one_func.name} {one_struct.name}")
    #     if not RUN_Prompt_is_func_parm_struct_init(one_func,bytearray2str(one_struct.name),run_count=5):
    #         logger.info(f"STATE_find_func_init RUN_Prompt_is_func_parm_struct_init {one_func.name} {one_struct.name} is not return")
    #         one_func.input_parm_set.add(one_struct)
    #         need_init_struct_list.append(one_struct)
    #     else:
    #         if one_func.output_parm_set is None:
    #             one_func.output_parm_set = set()
    #             one_func.output_parm_set.add(one_struct)
    
    if not need_init_struct_list:
        logger.info(f"STATE_find_func_init {one_func.name} no init struct")
        return return_list
    analyze_funcs_parm(all_func_list,project,run_count)
    for tmp_func in all_func_list:
        for need_struct in need_init_struct_list:
            if need_struct in tmp_func.init_parm_set:
                return_list.append(tmp_func)
                break
            if need_struct in tmp_func.init_return_set:
                return_list.append(tmp_func)
                break
            
    return return_list
            
    for tmp_func in all_func_list:
        contain_parm_list = get_func_contain_target_parm(tmp_func,need_init_struct_list)
        logger.info(f"STATE_find_func_init analyzing {tmp_func.name} with {need_init_struct_list} and contain parm is {contain_parm_list}")
        if not contain_parm_list:
            continue
        if tmp_func.output_parm_set is None:
            logger.info(f"STATE_find_func_init running get_func_return_struct {tmp_func.name}")
            return_struct = get_func_return_struct(tmp_func,project,run_count)
            logger.info(f"STATE_find_func_init after get_func_return_struct {tmp_func.name} return {return_struct}")
            tmp_func.output_parm_set = set()
            if return_struct:
                tmp_func.output_parm_set.add(return_struct)
            else:
                # parm_struct= get_func_parm_as_return_struct(tmp_func,project,run_count)
                logger.info(f"STATE_find_func_init running get_func_parm_as_return_struct_list {tmp_func.name}")
                parm_struct_list = get_func_parm_as_return_struct_list(tmp_func,project,run_count=5)
                logger.info(f"STATE_find_func_init after get_func_parm_as_return_struct_list {tmp_func.name} return {parm_struct_list}")
                if parm_struct_list:
                    for tmp_struct in parm_struct_list:
                        tmp_func.output_parm_set.add(tmp_struct)

        logger.info(f"STATE_find_func_init {tmp_func.name} output set is {tmp_func.output_parm_set}")
        for one_struct in tmp_func.output_parm_set:
            if one_struct in need_init_struct_list:
                tmp_func.type = "init"
                tmp_list.append(tmp_func)
                break
    print(f"STATE_find_func_init tmp list {tmp_list}")
    for tmp_func in tmp_list:
        for one_struct in tmp_func.output_parm_set:
            # 先判断结构体是输入参数还是返回参数
            func_body = bytearray2str(tmp_func.body).split("{")[0]
            # 如果是输入参数，那么前面已经判断过，不需要再次判断了。
            if bytearray2str(one_struct.name) in func_body.split("(")[1]:
                logger.info(f"\nnSTATE_find_func_init {tmp_func.name}'s input parameter {one_struct.name} is init")
                return_list.append(tmp_func)
            else:
                logger.info(f"\nSTATE_find_func_init running RUN_Prompt_is_func_return_struct_init {tmp_func.name} {one_struct.name}")
                if RUN_Prompt_is_func_return_struct_init(tmp_func,bytearray2str(one_struct.name),run_count=5):
                    logger.info(f"\nSTATE_find_func_init after RUN_Prompt_is_func_return_struct_init {tmp_func.name} {one_struct.name} is True")
                    return_list.append(tmp_func)
        # if RUN_Prompt_is_func_init_function(tmp_func,run_count):
        #     return_list.append(tmp_func)
    return return_list
# 针对多个函数
def STATE_find_input(func_list,G,run_count=1):
    return_list = []
    target_func_list = []
    # 首先通过判断函数参数个数筛选一遍函数
    for one_func in func_list:
        func_head = bytearray2str(one_func.body).split("{")[0]
        if len(one_func.parm_list) == 0:
            logger.info(f"STATE_find_input {func_head} out")
            continue
        struct_num = 0
        for one_parm in one_func.parm_list:
            if len(one_parm.name) > 0:
                struct_num += 1
        if struct_num == len(one_func.parm_list):
            logger.info(f"STATE_find_input {func_head} out")
            continue
        target_func_list.append(one_func)
    return_list = select_one_paramter_funcs(target_func_list,run_count)
    print(f"pointer list {return_list}")
    for one_func in return_list:
        one_func.type = "input"
    logger.info(f"\nSTATE_find_input get all {return_list}")
    two_parm_func_list = select_two_parameter_funcs(return_list,run_count)
    print(f"two parameter list {two_parm_func_list}")
    return_list = remove_inclusive(G,return_list)
    two_parm_func_list = remove_inclusive(G,two_parm_func_list)
    for one_func in two_parm_func_list:
        one_func.type = "input"
    # return_list = select_two_parameter_funcs(func_list,run_count)
    # logger.info(f"\nSTATE_find_input get two parm {return_list}")
    # another_list = []
    # for one_func in func_list:
    #     if one_func not in return_list:
    #         another_list.append(one_func)
    # return_list += select_one_paramter_funcs(another_list,run_count)
    # logger.info(f"\nSTATE_find_input get all {return_list}")
    return_list = list(set(return_list + two_parm_func_list))
    return return_list
# 针对单个函数
def STATE_find_process_func(one_func,project,all_func_list,run_count=1):
    print(f"STATE PROCESS analyzing {one_func.name}")
    logger.info(f"STATE_find_process_func analyzing {one_func.name}")
    
    analyze_funcs_parm([one_func],project)
    analyze_funcs_parm(all_func_list,project)
        
    return_list = [one_func]
    analyze_list = [one_func]
    analyzed_set = set()
    while analyze_list:
        test_func = analyze_list.pop()
        output_struct_list = list(test_func.output_parm_set)
        if output_struct_list:
            for tmp_func in all_func_list:
                if tmp_func in analyzed_set:
                    continue
                for one_struct in output_struct_list:
                    if one_struct in tmp_func.input_parm_set:
                        analyze_list.append(tmp_func)
                        analyzed_set.add(tmp_func)
                        return_list.append(tmp_func)
    return list(set(return_list))
    while analyze_list:
        test_func = analyze_list.pop()
        if test_func.output_parm_set is None:
            test_func.output_parm_set = set()
            parm_struct_list = []
            # parm_struct = get_func_parm_as_return_struct(test_func,project,run_count)
            logger.info(f"STATE_find_process_func running get_func_parm_as_return_struct_list {test_func.name}")
            parm_struct_list = get_func_parm_as_return_struct_list(test_func,project,run_count)
            if test_func.init_parm_set is None:
                test_func.init_parm_set = set()
            if parm_struct_list:
                for tmp_parm in parm_struct_list:
                    test_func.init_parm_set.add(tmp_parm)
            logger.info(f"STATE_find_process_func after get_func_parm_as_return_struct_list {test_func.name} with {parm_struct_list}")
            logger.info(f"STATE_find_process_func running get_func_return_struct {test_func.name}")
            return_parm = get_func_return_struct(test_func,project,run_count)
            logger.info(f"STATE_find_process_func after get_func_return_struct {test_func.name} with {return_parm}")
            # if parm_struct:
            #     parm_struct_list.append(parm_struct)
            if return_parm:
                parm_struct_list.append(return_parm)
            for one_struct in parm_struct_list:
                test_func.output_parm_set.add(one_struct)
        else:
            parm_struct_list = list(test_func.output_parm_set)
        print(f"STATE_find_process_func {test_func.name} output parm is {test_func.output_parm_set}")
        logger.info(f"STATE_find_process_func {test_func.name} output parm is {test_func.output_parm_set}")
        logger.info(f"STATE_find_process_func parm_struct_list is {parm_struct_list}")
        if parm_struct_list:
            #轮询每个函数的输入参数。
            for tmp_func in all_func_list:
                if tmp_func == one_func:
                    continue
                if tmp_func in analyzed_set:
                    continue
                struct_name_set = set()
                for tmp_struct in parm_struct_list:
                    struct_name_set.add(tmp_struct.name)
                logger.info(f"STATE_find_process_func {tmp_func.name} {tmp_func.parm_list}")
                if tmp_func.init_parm_set is not None:
                    pass
                else:
                    for parm in tmp_func.parm_list:
                        if parm.name in struct_name_set:
                            logger.info(f"STATE_find_process_func running RUN_Prompt_is_func_parm_struct_init {tmp_func.name} {parm.name}")
                            if not RUN_Prompt_is_func_parm_struct_init(tmp_func,bytearray2str(parm.name),run_count):
                                logger.info(f"STATE_find_process_func after RUN_Prompt_is_func_parm_struct_init {tmp_func.name} {parm.name} is False")
                                if tmp_func not in analyzed_set:
                                    analyze_list.append(tmp_func)
                                    return_list.append(tmp_func)
                                    analyzed_set.add(tmp_func)
                                break
    return return_list
# 针对函数列表
def STATE_find_destory_func(func_list,project,run_count=1):
    logger.info("STATE_find_destory_func")
    return_list = []
    tmp_list = []
    for one_func in func_list:
        logger.info(f"\nSTATE_find_destory_func running is_func_destory {one_func.name}")
        if is_func_destory(one_func,run_count):
            tmp_list.append(one_func)
            logger.info(f"\nSTATE_find_destory_func after is_func_destory {one_func.name} is True")
    for one_func in tmp_list:
        logger.info(f"\nSTATE_find_destory_func running get_func_destory_object {one_func.name}")
        return_obj = get_func_destory_object(one_func,project,run_count)
        logger.info(f"\nSTATE_find_destory_func after get_func_destory_object {one_func.name} is {return_obj}")
        if return_obj:
            if one_func.input_parm_set is None:
                one_func.input_parm_set = set()
            if return_obj != "N/A":
                one_func.input_parm_set.add(return_obj)
            one_func.type = "destory"
            return_list.append(one_func)
    return return_list
    

if __name__ == '__main__':

    # 感觉整体上需要有一个网进行链接，需要再设计一个结构体，专门用来管理函数。不断的聚类，分类。

    target_floder_path = "D:/work/selector-test/j40-main"
    target_floder_path = "/root/test/test/j40-main"
    # target_floder_path = "/root/test/test/qoi-master"
    target_floder_path = "/root/test/test/PDFGen-master"
    target_floder_path = "/root/test/test/cgif-main"
    target_floder_path = "/root/test/test/jebp-main"
    target_floder_path = "/root/test/test/olc-master"
    target_floder_path = "/root/test/test/quickjs-master"
    target_floder_path = "D:/work/selector-test/test/quickjs-master"
    
    target_project = CXXProject(target_floder_path)
    target_project.process()
    logger.info(f"\nfind all structs \n{target_project.all_class_dict}")
    G = nx.DiGraph()
    target_funcs = []
    for func in target_project.all_funcs:
        if bytearray2str(func.name) in {"main","LLVMFuzzerTestOneInput"}:
            continue
        target_funcs.append(func)
        # print(func)
    G = construct_graph(target_funcs)
    for one_func in target_funcs:
        count = 0
        for tmp_func in target_funcs:
            if one_func.body != tmp_func.body:
                if nx.has_path(G,one_func,tmp_func):
                    count += 1
        print(one_func,count,"/",len(target_funcs))
    os._exit(0)
    ##############TEST##################################

    ####################################################
    destory_func_list = STATE_find_destory_func(target_funcs,target_project,run_count=1)
    print(f"destory list {destory_func_list}")
    for one_func in destory_func_list:
        print(f"{one_func.name} destory {one_func.input_parm_set}")
    input_target_funcs = []
    for one_func in target_funcs:
        if one_func in destory_func_list:
            continue
        input_target_funcs.append(one_func)

    input_func_list = STATE_find_input(input_target_funcs,G,run_count=7)
    input_func_list = filter_file_op_funcs(input_func_list)
    print(f"init input func list {input_func_list}")
    init_funcs_group = []
    init_target_funcs = []
    for one_func in target_funcs:
        if one_func.type == "input":
            continue
        if one_func in destory_func_list:
            continue
        init_target_funcs.append(one_func)

    for one_func in input_func_list:
        tmp_init_target_funcs = []
        for tmp_func in init_target_funcs:
            if nx.has_path(G,one_func,tmp_func):
                continue
            tmp_init_target_funcs.append(tmp_func)
        tmp_list = STATE_find_func_init(one_func,target_project,tmp_init_target_funcs)
        print(f"{one_func.name} init func init list is {tmp_list}")
        init_funcs_group.append(remove_inclusive(G,tmp_list))

    for func_list in init_funcs_group:
        print(f"init funcs {func_list}")    
    init_funcs_set = set([item for sublist in init_funcs_group for item in sublist])
    process_target_funcs = []
    for one_func in init_target_funcs:
        if one_func in init_funcs_set:
            continue
        if one_func in destory_func_list:
            continue
        if one_func in input_func_list:
            continue
        process_target_funcs.append(one_func)

    process_funcs_group = []
    for func_list in init_funcs_group:
        target_func = None
        # 找到Input func
        for one_func in func_list:
            if one_func.type == "input":
                target_func = one_func
                break
        tmp_process_target_funcs = []
        for tmp_func in process_target_funcs:
            if nx.has_path(G,target_func,tmp_func):
                continue
            tmp_process_target_funcs.append(tmp_func)
        if target_func:
            tmp_list = STATE_find_process_func(target_func,target_project,tmp_process_target_funcs)
            process_funcs_group.append(list(set(tmp_list + func_list)))

    for func_list in process_funcs_group:
        print(f"process funcs {func_list}")
        # 添加销毁函数
        tmp_destory_list = []
        output_parm_set = set()
        for one_func in func_list:
            output_parm_set |= one_func.output_parm_set
        print(f"{func_list} output parm is {output_parm_set}")
        for one_parm in output_parm_set:
            for destory_func in destory_func_list:
                if one_parm in destory_func.input_parm_set:
                    print(f"{func_list} find destory func {destory_func}")
                    tmp_destory_list.append(destory_func)
        print(f"destory list is {tmp_destory_list}")
        func_list += tmp_destory_list
    
            
    for func_list in process_funcs_group:
        print(f"final group {func_list}")
        logger.info(f"final group {func_list}")

    os._exit(0)


 


