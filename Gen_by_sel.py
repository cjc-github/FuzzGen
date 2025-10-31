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
from Core.promptRUN import *
from Core.SelGenStructure import *
import random
import subprocess
###########下面几个函数是为了将筛选结果解析到内存的
def get_func_by_name(name,func_list):
    for one_func in func_list:
        if bytearray2str(one_func.name) == name:
            return one_func
    return None
def get_struct_by_name(name,all_class_dict):
    if name.encode('utf-8') in all_class_dict:
        return all_class_dict[name.encode('utf-8')]
    return None
def decode_one_func(func_dict,project):
    one_func = get_func_by_name(func_dict['name'],project.all_funcs)
    if one_func is None:
        return None
    if func_dict['input_parm']:
        one_func.input_parm_set = set()
        for name in func_dict['input_parm']:
            one_func.input_parm_set.add(get_struct_by_name(name,project.all_class_dict))
    else:
        one_func.input_parm_set = set()
    if func_dict['init_parm']:
        one_func.init_parm_set = set()
        for name in func_dict['init_parm']:
            one_func.init_parm_set.add(get_struct_by_name(name,project.all_class_dict))
    else:
        one_func.init_parm_set = set()
    if func_dict['output_parm']:
        one_func.output_parm_set = set()
        for name in func_dict['output_parm']:
            one_func.output_parm_set.add(get_struct_by_name(name,project.all_class_dict))
    else:
        one_func.output_parm_set = set()
    if func_dict['return_init_parm']:
        one_func.init_return_set = set()
        for name in func_dict['return_init_parm']:
            one_func.init_return_set.add(get_struct_by_name(name,project.all_class_dict))
    else:
        one_func.init_return_set = set()
    return one_func
def gen_selector_from_file(file_name,project):
    with open(file_name,"r") as f:
        sel_dict = json.load(f)
    input_func_dict = sel_dict['input']
    input_func = decode_one_func(input_func_dict,project)
    process_dict_list = sel_dict['process']
    process_funcs = []
    for process_dict in process_dict_list:
        process_funcs.append(decode_one_func(process_dict,project))
    init_dict_list = sel_dict['init']
    init_funcs = []
    for init_dict in init_dict_list:
        init_funcs.append(decode_one_func(init_dict,project))
    destory_funcs = []
    for destory_dict in sel_dict['destory']:
        destory_funcs.append(decode_one_func(destory_dict,project))
    one_selector = OneSelectorGroup(input_func)
    one_selector.destory_funcs = destory_funcs[:]
    one_selector.init_funcs = init_funcs[:]
    one_selector.process_funcs = process_funcs[:]
    return one_selector
##################筛选结果解析结束############################


def check_run_message(message):
    content_list = message.splitlines()
    cov_set = set()
    ft_set = set()
    exec_set = set()
    if len(content_list) < 300:
        return False
    for one_line in content_list:
        if "cov: " not in one_line:
            continue
        if " ft: " not in one_line:
            continue
        if " exec/s: " not in one_line:
            continue
        cov_str = one_line.split("cov: ")[1].split(" ")[0]
        cov_set.add(int(cov_str))
        ft_str = one_line.split(" ft: ")[1].split(" ")[0]
        ft_set.add(int(ft_str))
        exec_str = one_line.split(" exec/s: ")[1].split(" ")[0]
        exec_set.add(int(exec_str))
    if len(cov_set) > 30 and len(ft_set) > 30 and len(exec_set) > 10:
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='目标工程文件夹')
    parser.add_argument('-o','--output',type=str,help="输出代码路径")
    parser.add_argument('-s','--sel',type=str,help="sel文件的位置")
    args = parser.parse_args()
    ''' gen_config.json 在相同目录下建立gen_config.json文件，并将下面内容写入
    {
    "model_path":"D:/models/codeqwen/",
    "prompt_type":"codeqwen",
    "max_token_num":16384,
    "gen_file_path":"D:/work/selector-test/qoi/test.c",
    "target_floder":"D:/work/selector-test/qoi",
    "gen_command":"clang -fsanitize=fuzzer,address -g -O2 test.c",
    "run_command":"./a.out"
}
    '''
    if not os.path.exists("gen_config.json"):
        print("[FATAL] no gen_config.json")
        os._exit(0)
    with open("gen_config.json",'r') as f:
        config_dict = json.load(f)
    model_path = config_dict['model_path']
    USE_MODEL_TYPE = config_dict['prompt_type']
    
    ## 下面都是生成临时测试代码的地方
    gen_file_path = config_dict['gen_file_path']
    gen_floder = config_dict['target_floder']
    gen_command = config_dict['gen_command']
    run_gen_command = config_dict['run_command']

    logger.info(f"USE-MODEL-TYPE-S{USE_MODEL_TYPE}USE-MODEL-TYPE-E")
    input_dir = args.input  
    output_dir = args.output
    sel_dict_path = args.sel


    initial_target_funcs_list = []
    target_class_list = []

    if not os.path.exists(input_dir):
        print(f"{input_dir} path not exist")
        os._exit(0)
    logger.info(f"processing {input_dir}")
    # 分析输入工程
    target_project = CXXProject(input_dir)
    # 只需要获取函数信息即可，没必要用llm筛选文件。
    # target_project.filter_file_by_llm(USE_MODEL_TYPE)
    target_project.process()
    G = construct_graph(target_project.all_funcs)

    selector = gen_selector_from_file(sel_dict_path,target_project)
    output_path = os.path.join(output_dir,bytearray2str(selector.input_func.name)+"-output")
    generator = CGenerator(selector,target_project,USE_MODEL_TYPE)
    generator.filter_func()
    sel_funcs = selector.get_all_funcs()
    header_file_set = set()
    for one_func in sel_funcs:
        if not one_func.include_file_path:
            continue  
        for file_name in target_project.all_files:
            if one_func.include_file_path in file_name:
                header_file_set.add(file_name)
    predefine_content = ""
    header_content = ""
    if header_file_set:
        for ffile_name in header_file_set:
            file_content = get_file_front_line_content(ffile_name,300)
            prompt_str = construct_prompt_str(INS_generate_header(),file_content,USE_MODEL_TYPE)
            result_dict = None
            while result_dict is None:
                result = run_llm_custom(prompt_str)
                result_dict = get_return_dict(result,["predefine","header"])
            predefine_content += result_dict['predefine'] + "\n"
            header_content += result_dict['header'] + "\n"

    #改用状态机生成，保证生成一个可用harness
    state = ["api","parm","robo","opt","harness","regen","exit"]
    cur_state = "api"
    cyc_state = "harness"
    cyc_time = 0
    fuzzer_code = ""
    while True:
        if cur_state == "api":
            print("[STATE] GEN API")
            generator.gen_api_doc()
            cur_state = "parm"
        elif cur_state == "parm":
            print("[STATE] GEN PARM CODE")
            generator.gen_code_by_parm()
            cur_state = "robo"
        elif cur_state == "robo":
            print("[STATE] GEN ROBO CODE")
            generator.gen_robo_code()
            cur_state = "opt"
        elif cur_state == "opt":
            print("[STATE] GEN OPT CODE")
            generator.gen_opt_code()
            cur_state= "harness"
        elif cur_state == "harness":
            # TODO 重新定义run
            # 最少生成4次
            print("[STATE] GEN HARNESS CODE")
            generator.gen_harness_code()
            content = generator.harness_code
            code_content = get_code_from_content(content)
            fuzzer_code = f"{predefine_content}{header_content}{code_content}"
            # 保存代码
            with open(gen_file_path, "w") as f:
                f.write(fuzzer_code)
            # 编译代码
            process = subprocess.Popen(gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            stdout, error_message = process.communicate()
            if isinstance(error_message, bytes):
                error_message = error_message.decode('utf-8',errors='ignore')
            # 假设存在编译错误，预先构造prompt
            ins = INS_regenerate_compile(fuzzer_code,error_message)
            prompt_str = construct_prompt_str(ins,"",USE_MODEL_TYPE)
            logger.info(construct_prompt_str(ins,"","content"))

            for _ in range(4):
                # 如果编译成功，则直接退出
                if len(error_message) == 0:
                    # 生成成功，保存文件

                    print("generate success")
                    cur_state = "regen"
                    break
                # 编译失败，重新构造构造编译错误代码
                print("[STATE] GEN HARNESS CODE - recompile")
                result = run_llm_custom(prompt_str)
                logger.info(result)
                # 提取代码
                content_list = result.split("```c")
                fuzzer_code = ""
                for one_code in content_list[::-1]:
                    if "LLVMFuzzerTestOneInput(" in one_code:
                        fuzzer_code = one_code.split("```")[0]
                        break
                logger.info(fuzzer_code)
                with open(gen_file_path, "w") as f:
                    f.write(fuzzer_code)
                process = subprocess.Popen(gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
                stdout, error_message = process.communicate()
                if isinstance(error_message, bytes):
                    error_message = error_message.decode('utf-8',errors='ignore')

            # 如果cur_state说明4次编译尝试失败，则回退重新生成
            if cur_state != "regen":
                if cyc_time < 3:
                    cur_state = cyc_state
                    cyc_time += 1
                else:
                    if cyc_state == "api":
                        cur_state = "exit"
                        print("generate failure")
                    else:
                        cyc_time = 1
                        cyc_state = state[max(state.index(cyc_state)-1,0)]
                        cur_state = cyc_state
        elif cur_state == "regen":
            # TODO 编写regen
            # 进入到此状态，说明已经生成了一个能够编译的libfuzzer代码了，因此不到万不得已，不会轻易回退。
            cur_state = "exit"
            regen_code = fuzzer_code
            print("[STATE] RUN AND REGEN HARNESS CODE")
            process = subprocess.Popen(run_gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            stdout, error_message = process.communicate()
            if isinstance(error_message, bytes):
                error_message = error_message.decode('utf-8',errors='ignore')
            if check_run_message(error_message):
                print("run harness and result is good")
                cur_state = "exit"
            else:
                prompt_str = construct_prompt_str(INS_regenerate_run(regen_code,error_message),"","codeqwen")
                # 尝试生成10次
                for _ in range(10):
                    result = run_llm_custom(prompt_str)
                    content_list = result.split("```c")
                    for one_code in content_list[::-1]:
                        if "LLVMFuzzerTestOneInput(" in one_code:
                            regen_code = one_code.split("```")[0]
                            break
                    logger.info(f"regen code: \n{regen_code}")
                    with open(gen_file_path, 'w') as f:
                        f.write(regen_code)
                    process = subprocess.Popen(gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
                    stdout, error_message = process.communicate()
                    if len(error_message) > 10:
                        print("re compile error")
                        continue
                    print("re compile success, re run harness")
                    process = subprocess.Popen(run_gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
                    stdout, error_message = process.communicate()
                    if check_run_message(error_message):
                        print("run harness and result is good")
                        fuzzer_code = regen_code
                        cur_state = "exit"
                        break
        elif cur_state == "exit":
            print("exit")
            output_file_name = output_path + "-0.c"
            with open(output_file_name, "w") as f:
                f.write(fuzzer_code)
            with open(gen_file_path, 'w') as f:
                f.write(fuzzer_code)
            break