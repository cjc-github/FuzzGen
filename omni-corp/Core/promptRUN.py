## 该文件存放分析单个函数的prompt运行和结果返回函数
## 该文件主要存放prompt的运行封装

from Core.promptINS import *
from Core.logger import logger
import networkx as nx
from Core.GenData import *
from Core.CustomAlgorithm import *
from Core.CustomStructure import *
from Core.APIWarp import *
from Core.Utils import *
from Core.api import *
import re
from collections import Counter
from tqdm import tqdm

#################
##辅助函数#######
################

def get_func_parm_struct_list(one_func,project):
    return_list = []
    for one_parm in one_func.parm_list:
        if one_parm.name in project.all_class_dict:
            return_list.append(project.all_class_dict[one_parm.name])
    return return_list
def get_func_contain_target_parm(one_func,parm_list):
    return_list = []
    func_head = bytearray2str(one_func.body).split("{")[0]
    for one_parm in parm_list:
        parm_name = bytearray2str(one_parm.name)
        if parm_name in func_head:
            return_list.append(parm_name)
    return return_list
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
        result_dict = extract_json_from_text(return_str)[-1]
        for key_str in key_list:
            if key_str not in result_dict:
                return None
            if result_dict[key_str] is None:
                return None
        return result_dict
    except:
        # print(f"{return_str} decode error")
        return None

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
 
    
def clear_parm_name(parm_name):
    return_name = parm_name
    return_name = return_name.replace("struct ","")
    return_name = return_name.replace("const ","")
    return_name = return_name.replace("static ","")
    return_name = return_name.replace("*","")
    return_name = return_name.replace("&","")
    return_name = return_name.replace(" ","")
    return return_name



########################
######Prompt运行封装####
########################

def RUN_prompt_is_file_related(readme,file_content,model_type):
    prompt_str = construct_prompt_str(INS_is_related_file(readme),file_content,model_type)
    #log
    log_prompt = construct_prompt_str(INS_is_related_file(readme),file_content,model_type)
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)

    result_dict = None
    while result_dict is None:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer"])
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
    logger.info(log_str)

    if "yes" in result_dict['answer']:
        return True
    return False
def RUN_prompt_get_readme_summary(readme,model_type):
    # 生成摘要，没必要记录log
    prompt_str = construct_prompt_str(INS_generate_readme_summary(),readme,model_type)
    #log
    log_prompt = construct_prompt_str(INS_generate_readme_summary(),readme,model_type)
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)

    result_dict = None
    while result_dict is None:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["final_output"])

    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
    logger.info(log_str)

    

    return result_dict['final_output']

# log 形式：{question-hash}--{qusetion/answer/result}-<start>{prompt/answer/result}<end>
def RUN_prompt_is_func_common(one_func,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_common(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_common(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            count += 1
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
def RUN_Prompt_is_func_contain_file_op(one_func,model_type="codeqwen",run_count=1):
    # 通过设置多次执行，提升结果准确率
    prompt_str = construct_prompt_str(INS_function_file_op(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_file_op(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
    
# def RUN_Prompt_is_func_contain_memory_load_parameter(one_func,model_type="codeqwen",run_count=1):
#     prompt_str = construct_prompt_str(INS_function_memory_load(),bytearray2str(one_func.body),model_type)
#     count = 0
#     answer_list = []
#     while count < run_count:
#         result = run_llm_custom(prompt_str)
#         logger.info(prompt_str)
#         logger.info(result)
#         result_dict = get_return_dict(result,["answer"])
#         if result_dict:
#             count += 1
#             if "yes" in result_dict['answer']:
#                 answer_list.append(True)
#             else:
#                 answer_list.append(False)

#     if answer_list.count(True) > answer_list.count(False):
#         return True
#     else:
#         return False
    

def RUN_prompt_check_memory_pointer_char(one_func,pointer_name,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer_2(pointer_name),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_check_memory_pointer_2(pointer_name),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    result1 = run_llm_custom(prompt_str)
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result1}<end>"
    logger.info(log_str)
    
    func_head = bytearray2str(one_func.body).split("{")[0]
    count = 0
    answer_list = []
    prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer_3(pointer_name),func_head + "\n" + result1,model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_check_memory_pointer_3(pointer_name),func_head + "\n" + result1,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)

    answer_list = []
    count = 0
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            count += 1
            answer_list.append(result_dict['answer'])
    element_counts = Counter(answer_list)
    most_common_element = element_counts.most_common(1)
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{most_common_element[0][0]}<end>"
    logger.info(log_str)
    
    if most_common_element[0][0] == "E":
        return True
    else:
        return False
def RUN_prompt_check_memory_pointer_struct(one_func,pointer_name,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer_2(pointer_name),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_check_memory_pointer_2(pointer_name),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)

    result1 = run_llm_custom(prompt_str)
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result1}<end>"
    logger.info(log_str)
    
    func_head = bytearray2str(one_func.body).split("{")[0]
    count = 0
    answer_list = []
    prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer_1(pointer_name),func_head + "\n" + result1,model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_check_memory_pointer_1(pointer_name),func_head + "\n" + result1,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            count += 1
            answer_list.append(result_dict['answer'])
            
    element_counts = Counter(answer_list)
    most_common_element = element_counts.most_common(1)
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{most_common_element[0][0]}<end>"
    logger.info(log_str)
    # 确定为二进制数据
    if most_common_element[0][0] == "A":
        return True
    # 确定是字符串
    elif most_common_element[0][0] == "B":
        prompt_str = construct_prompt_str(INS_parameter_check_memory_pointer_3(pointer_name),func_head + "\n" + result1,model_type)
        #log
        log_prompt =construct_prompt_str(INS_parameter_check_memory_pointer_3(pointer_name),func_head + "\n" + result1,"content")
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
        logger.info(log_str)
        
        answer_list = []
        count = 0
        while count < run_count:
            result = run_llm_custom(prompt_str)
            logger.info(result)
            result_dict = get_return_dict(result,["answer"])
            if result_dict:
                #log
                log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
                logger.info(log_str)
                count += 1
                answer_list.append(result_dict['answer'])
        element_counts = Counter(answer_list)
        most_common_element = element_counts.most_common(1)
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{most_common_element[0][0]}<end>"
        logger.info(log_str)
        
        if most_common_element[0][0] == "E":
            return True
        else:
            return False
    return False
    
    
def RUN_prompt_check_pointer_size(one_func,pointer_name,size,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_parameter_check_pointer_size(pointer_name,size),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_check_pointer_size(pointer_name,size),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result =run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)
    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
    

def RUN_Prompt_is_func_contain_memory_pointer(one_func,model_type="codeqwen",run_count=1):
    if one_func.sign is None:
        # 如果还没有得到函数签名，那就运行一次得到函数签名
        RUN_prompt_get_func_sign(one_func,model_type)
    # prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),bytearray2str(one_func.body),model_type)
    prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),one_func.sign,model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_memory_pointer(),one_func.sign,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)

    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer","pointer_name"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
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
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False

def RUN_prompt_is_func_benchmark(one_func,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_benchmark(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_benchmark(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False   
    
def RUN_prompt_is_func_test(one_func,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_test(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_test(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)

    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False   

def RUN_Prompt_get_func_classify(one_func,model_type="codeqwen"):
    prompt_str = construct_prompt_str(INS_function_classify(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_classify(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    while True:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","reason"])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{result_dict['answer']}<end>"
            logger.info(log_str)
            return result_dict

            
def RUN_Prompt_get_func_destory(one_func,model_type="codeqwen"):
    prompt_str = construct_prompt_str(INS_parameter_destory_struct(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_destory_struct(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    while True:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer","destroy_parameter_type"])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{result_dict}<end>"
            logger.info(log_str)
            return result_dict

def RUN_Prompt_is_func_contain_global_rw(one_func,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_global_variable_write(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_global_variable_write(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            count += 1
            if "yes" in result_dict["answer"]:
                answer_list.append(True)
            else:
                answer_list.append(False)
    
    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
    

# def RUN_Prompt_is_func_init_function(one_func,model_type="codeqwen",run_count=1):
#     prompt_str = construct_prompt_str(INS_function_init(),bytearray2str(one_func.body),model_type)
#     logger.info(prompt_str)
#     count = 0
#     answer_list = []
#     while count < run_count:
#         result = run_llm_custom(prompt_str)
#         logger.info(result)
#         result_dict = get_return_dict(result,["answer"])
#         if result_dict is not None:
#             count += 1
#             if "yes" in result_dict["answer"]:
#                 answer_list.append(True)
#             else:
#                 answer_list.append(False)
                
#     if answer_list.count(True) > answer_list.count(False):
#         return True
#     else:
#         return False

# def RUN_Prompt_is_func_parm_is_init(one_func,parm_name,model_type="codeqwen",run_count=1):    
#     prompt_str = construct_prompt_str(INS_function_struct_init(parm_name),bytearray2str(one_func.body),model_type)
#     logger.info(prompt_str)
#     count = 0
#     answer_list = []
#     while count < run_count:
#         result = run_llm_custom(prompt_str)
#         logger.info(result)
#         result_dict = get_return_dict(result,["answer"])
#         if result_dict is not None:
#             count += 1
#             if "yes" in result_dict['answer']:
#                 answer_list.append(True)
#             else:
#                 answer_list.append(False)
                
#     if answer_list.count(True) > answer_list.count(False):
#         return True
#     else:
#         return False

def RUN_Prompt_is_func_parm_struct_init(func_str,parm_name,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_parm_struct_init(parm_name),func_str,model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_parm_struct_init(parm_name),func_str,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer"])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
def RUN_Prompt_is_func_return_struct_init(one_func,parm_name,model_type="codeqwen",run_count=1):
    prompt_str = construct_prompt_str(INS_function_return_struct_init(parm_name),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_return_struct_init(parm_name),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer","reason"])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            count += 1
            if "yes" in result_dict['answer']:
                answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False
        
# def RUN_Prompt_is_func_parm_return(one_func,parm_name,model_type="codeqwen",run_count=1):
#     logger.info(f"RUN_Prompt_is_func_parm_return {one_func.name} {parm_name}")
#     prompt_str = construct_prompt_str(INS_parameter_struct_is_return(parm_name),bytearray2str(one_func.body),model_type)
#     logger.info(prompt_str)
#     count = 0
#     answer_list = []
#     while count < run_count:
#         result = run_llm_custom(prompt_str)
#         logger.info(result)
#         result_dict = get_return_dict(result,['answer',"variable_name","reason"])
#         if result_dict is not None:
#             count += 1
#             if "yes" in result_dict['answer']:
#                 func_parameter = bytearray2str(one_func.body).split("{")[0].split("(")[1]
#                 func_parameter_list = func_parameter.split(",")
#                 is_contain = False
#                 for parm_str in func_parameter_list:
#                     if result_dict["variable_name"] in parm_str and parm_name in parm_str:
#                         is_contain = True
#                         break
#                 if is_contain:
#                     answer_list.append(True)
#                 else:
#                     answer_list.append(False)
#             else:
#                 answer_list.append(False)
                
#     if answer_list.count(True) > answer_list.count(False):
#         return True
#     else:
#         return False

# def RUN_Prompt_get_func_parm_return(one_func,model_type="codeqwen"):
#     prompt_str = construct_prompt_str(INS_parameter_input_paramter_is_return(),bytearray2str(one_func.body),model_type)
#     logger.info(prompt_str)
#     while True:
#         result = run_llm_custom(prompt_str)
#         logger.info(result)
#         result_dict = get_return_dict(result,["answer","variable_name","variable_type","reason"])
#         if result_dict is not None:
#             return result_dict


def RUN_Prompt_get_func_return(one_func,model_type="codeqwen"):
    prompt_str = construct_prompt_str(INS_parameter_return_value(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_return_value(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    while True:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["return_parameter_type"])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{result_dict['return_parameter_type']}<end>"
            logger.info(log_str)
            return result_dict


def RUN_prompt_get_func_sign(one_func,model_type="codeqwen"):
    prompt_str = construct_prompt_str(INS_function_sign(),bytearray2str(one_func.body),model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_sign(),bytearray2str(one_func.body),"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    function_sign = run_llm_custom(prompt_str)
    #log
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{function_sign}<end>"
    logger.info(log_str)
    one_func.sign = function_sign
    return function_sign

def RUN_prompt_is_pointer_return(one_func,pointer_name,model_type="codeqwen",run_count=1):
    if one_func.sign is None:
        # 如果还没有得到函数签名，那就运行一次得到函数签名
        RUN_prompt_get_func_sign(one_func,model_type)
    prompt_str1 = construct_prompt_str(INS_function_parameter_sign_output(pointer_name),one_func.sign,model_type)
    #log
    log_prompt = construct_prompt_str(INS_function_parameter_sign_output(pointer_name),one_func.sign,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    count = 0
    answer_list = []
    while count < run_count:
        result = run_llm_custom(prompt_str1)
        result_dict = get_return_dict(result,['answer'])
        if result_dict is not None:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            count += 1
            if "yes" in result_dict['answer']:
                    answer_list.append(True)
            else:
                answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-True<end>"
        logger.info(log_str)
        return True
    else:
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-False<end>"
        logger.info(log_str)
        return False


########################
######Prompt二次封装####
########################

def select_one_paramter_funcs(func_list,model_type="codeqwen",run_count=1):
    return_list = []
    for one_func in tqdm(func_list,desc="select memory pointer"):
        # if RUN_Prompt_is_func_contain_memory_pointer(one_func,run_count):
        if select_memory_pointer_func(one_func,model_type,run_count):
            return_list.append(one_func)
    return return_list

def select_two_parameter_funcs(target_func_list,model_type="codeqwen",run_count=1):
    return_list = []
    for one_func in tqdm(target_func_list,desc="select memory size pointer"):
        # if RUN_Prompt_is_func_contain_memory_size_parameter(one_func,run_count):
        if select_memory_pointer_size_func(one_func,model_type,run_count):
            return_list.append(one_func)
    return return_list

def get_func_return_struct(one_func,project,model_type="codeqwen",run_count=1):
    logger.info(f"get_func_return_struct({one_func.name},{one_func.return_parm},{run_count})")
    count = 0
    answer_list = []
    while count < run_count:
        count += 1
        answer_dict = RUN_Prompt_get_func_return(one_func,model_type)
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



# def get_func_parm_as_return_struct(one_func,project,model_type="codeqwen",run_count=1):
#     # return_list = []
#     count = 0
#     answer_list = []
#     while count < run_count:
#     # 首先确定是否存在
#         count += 1
#         answer_dict = RUN_Prompt_get_func_parm_return(one_func,model_type)
#         if "yes" not in answer_dict['answer']:
#             answer_list.append(None)
#             continue
#         parm_name = clear_parm_name(answer_dict["variable_type"])
#         byte_parm_name = bytes(parm_name.encode("utf-8"))
#         if byte_parm_name not in project.all_class_dict:
#             answer_list.append(None)
#             continue
#         # 通过具体变量名二次确认，下面函数可以根据情况变成判断参数是否被初始化
#         if not RUN_Prompt_is_func_parm_return(one_func,parm_name,model_type):
#             answer_list.append(None)
#             continue
#         answer_list.append(project.all_class_dict[byte_parm_name])                                    
#     # return return_list
#     element_counts = Counter(answer_list)
#     most_common_element = element_counts.most_common(1)
#     return most_common_element[0][0]

def is_func_destory(one_func,model_type="codeqwen",run_count=1):
    count = 0
    answer_list = []
    while count < run_count:
        classify_dict = RUN_Prompt_get_func_classify(one_func,model_type)
        count += 1
        if "C" in classify_dict["answer"]:
            answer_list.append(True)
        else:
            answer_list.append(False)
                
    if answer_list.count(True) > answer_list.count(False):
        return True
    else:
        return False

    
# def get_func_classify(one_func,model_type="codeqwen",run_count=1):
#     count = 0
#     answer_list = []
#     while count < run_count:
#         classify_dict = RUN_Prompt_get_func_classify(one_func,model_type)
#         if classify_dict["answer"] not in ['A','B','C','D','E']:
#             continue
#         count += 1
#         answer_list.append(classify_dict["answer"])

#     element_counts = Counter(answer_list)
#     most_common_element = element_counts.most_common(1)
#     return most_common_element[0][0]

def get_func_destory_object(one_func,project,model_type="codeqwen",run_count=1):
    count = 0
    answer_list = []
    while count < run_count:
        count += 1
        answer_dict = RUN_Prompt_get_func_destory(one_func,model_type)
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

def select_memory_pointer_func(one_func,model_type="codeqwen",run_count=1):
    # 如果函数能够直接通过两层测试，那么就可以直接说明函数是包含连续内存参数的函数，一次通过则不需要多次测试。否则则进行多次测试。
    count = 0
    if one_func.sign is None:
        # 如果还没有得到函数签名，那就运行一次得到函数签名
        RUN_prompt_get_func_sign(one_func,model_type)
    # prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),bytearray2str(one_func.body),model_type)
    prompt_str = construct_prompt_str(INS_parameter_memory_pointer(),one_func.sign ,model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_memory_pointer(),one_func.sign ,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    
    while count < run_count:
        result = run_llm_custom(prompt_str)
        logger.info(result)
        result_dict = get_return_dict(result,["answer","pointer_name"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{result_dict}<end>"
            logger.info(log_str)

            count += 1
            if "yes" not in result_dict["answer"]:
                continue
            pointer_name = result_dict["pointer_name"]
            # 原则上要确定输入参数仅仅有一个是指向连续内存的
            if type(pointer_name) != type("abc"):
                continue
            check_result = TS_check_memroy_pointer(one_func,pointer_name)
            if check_result is False:
                return False
            if check_result is True:
                if TS_check_pointer_const(one_func,pointer_name):
                    return True
                else:
                    if RUN_prompt_is_pointer_return(one_func,pointer_name,model_type,1):
                        return True
            if check_result == "char":
                if RUN_prompt_check_memory_pointer_char(one_func,pointer_name,model_type,1):
                    if TS_check_pointer_const(one_func,pointer_name):
                        return True
                    else:
                        if RUN_prompt_is_pointer_return(one_func,pointer_name,model_type,1):
                            return True
            elif check_result == "struct":
                if RUN_prompt_check_memory_pointer_struct(one_func,pointer_name,model_type,1):
                    if TS_check_pointer_const(one_func,pointer_name):
                        return True
                    else:
                        if RUN_prompt_is_pointer_return(one_func,pointer_name,model_type,1):
                            return True
    return False

def select_memory_pointer_size_func(one_func,model_type="codeqwen",run_count=1):
    # 如果函数能够直接通过三层测试，那么就可以直接说明函数是包含连续内存参数的函数，一次通过则不需要多次测试。否则则进行多次测试。
    count = 0
    if one_func.sign is None:
        # 如果还没有得到函数签名，那就运行一次得到函数签名
        RUN_prompt_get_func_sign(one_func,model_type)
    # prompt_str = construct_prompt_str(INS_parameter_memory_size(),bytearray2str(one_func.body),model_type)
    prompt_str = construct_prompt_str(INS_parameter_memory_size(),one_func.sign,model_type)
    #log
    log_prompt = construct_prompt_str(INS_parameter_memory_size(),one_func.sign,"content")
    log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
    logger.info(log_str)
    while count < run_count:
        result = run_llm_custom(prompt_str)
        result_dict = get_return_dict(result,["answer","pointer_name","size_name"])
        if result_dict:
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{result}<end>"
            logger.info(log_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-result-<,sp1it.>-{result_dict}<end>"
            logger.info(log_str)
            count += 1
            if "yes" not in result_dict["answer"]:
                continue
            pointer_name = result_dict["pointer_name"]
            # 原则上pointer_name 和size 只有一个
            if type(pointer_name) != type("123"):
                continue
            size = result_dict["size_name"]
            if type(size) != type("123"):
                continue
            if size not in bytearray2str(one_func.body).split("{")[0].split("(")[1]:
                continue
            check_result = TS_check_memroy_pointer(one_func,pointer_name)
            if check_result is False:
                continue
            elif check_result == "char":
                if not RUN_prompt_check_memory_pointer_char(one_func,pointer_name,model_type,1):
                    continue
            elif check_result == "struct":
                if not RUN_prompt_check_memory_pointer_struct(one_func,pointer_name,model_type,1):
                    continue
            if not TS_check_pointer_const(one_func,pointer_name):
                if not RUN_prompt_is_pointer_return(one_func,pointer_name,model_type,1):
                    continue
            if RUN_prompt_check_pointer_size(one_func,pointer_name,size,model_type,1):
                return True
    return False