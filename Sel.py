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






if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='目标工程文件夹')
    parser.add_argument('-o','--output',type=str,help="输出代码路径")
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

    logger.info(f"USE-MODEL-TYPE-S{USE_MODEL_TYPE}USE-MODEL-TYPE-E") #记录模型的日志
    input_dir = args.input  
    output_dir = args.output
    # tokenizer = AutoTokenizer.from_pretrained(model_path)

    initial_target_funcs_list = []
    target_class_list = []

    if not os.path.exists(input_dir):
        print(f"{input_dir} path not exist")
        os._exit(0)
    logger.info(f"processing {input_dir}")
    target_project = CXXProject(input_dir)
    
    # target_project.parse_readme_file(USE_MODEL_TYPE)
    target_project.filter_file_by_llm(USE_MODEL_TYPE)#保留与项目相关的文件
    target_project.process()#提取文件中的函数、类、命名空间等信息
    G = construct_graph(target_project.all_funcs) #将所有的函数都作为节点放到图中
    target_lang = ""
    # 构造有向图
    # G = construct_graph(target_project.all_funcs)
    # 初步筛选
    initial_target_funcs_list = []
    for file_name in target_project.all_file_obj_dict:
        if target_project.all_file_obj_dict[file_name].config == "cpp":
            target_lang = "cpp"
        elif target_project.all_file_obj_dict[file_name].config == "c":
            target_lang = 'c'
        break
    
    # if target_lang == "c":
    candi_list = [] 
    for one_func in target_project.all_funcs:
        if bytearray2str(one_func.name) in {"main","LLVMFuzzerTestOneInput"}:
            continue
        candi_list.append(one_func)
    Selector = CSelector(candi_list,target_project,USE_MODEL_TYPE,1)#分类
    selector_list = Selector.run()
    for one_selector in selector_list:
        dump_path = os.path.join(output_dir,bytearray2str(one_selector.input_func.name)+".sel")
        with open(dump_path,'w') as f:
            json.dump(one_selector.todict(),f)
        print(f"dump {dump_path} over")
    
            
    for one_selector in selector_list:
        print(one_selector.show())
        logger.info(one_selector.show())
    # for selector in selector_list:
    #     output_path = os.path.join(output_dir,bytearray2str(selector.input_func.name)+"-output")
    #     generator = CGenerator(selector,target_project,USE_MODEL_TYPE)
    #     generator.filter_func()
    #     sel_funcs = selector.get_all_funcs()
    #     header_file_set = set()
    #     for one_func in sel_funcs:
    #         if not one_func.include_file_path:
    #             continue  
    #         for file_name in target_project.all_files:
    #             if one_func.include_file_path in file_name:
    #                 header_file_set.add(file_name)
    #     predefine_content = ""
    #     header_content = ""
    #     if header_file_set:
    #         for ffile_name in header_file_set:
    #             file_content = get_file_front_line_content(ffile_name,300)
    #             prompt_str = construct_prompt_str(INS_generate_header(),file_content,USE_MODEL_TYPE)
    #             result_dict = None
    #             while result_dict is None:
    #                 result = run_llm_custom(prompt_str)
    #                 result_dict = get_return_dict(result,["predefine","header"])
    #             predefine_content += result_dict['predefine'] + "\n"
    #             header_content += result_dict['header'] + "\n"

    #     #改用状态机生成，保证生成一个可用harness
    #     state = ["api","parm","robo","opt","harness","regen","exit"]
    #     cur_state = "api"
    #     cyc_state = "harness"
    #     cyc_time = 0
    #     while True:
    #         if cur_state == "api":
    #             print("[STATE] GEN API")
    #             generator.gen_api_doc()
    #             cur_state = "parm"
    #         elif cur_state == "parm":
    #             print("[STATE] GEN PARM CODE")
    #             generator.gen_code_by_parm()
    #             cur_state = "robo"
    #         elif cur_state == "robo":
    #             print("[STATE] GEN ROBO CODE")
    #             generator.gen_robo_code()
    #             cur_state = "opt"
    #         elif cur_state == "opt":
    #             print("[STATE] GEN OPT CODE")
    #             generator.gen_opt_code()
    #             cur_state= "harness"
    #         elif cur_state == "harness":
    #             # TODO 重新定义run
    #             # 最少生成4次
    #             print("[STATE] GEN HARNESS CODE")
    #             generator.gen_harness_code()
    #             content = generator.harness_code
    #             code_content = get_code_from_content(content)
    #             fuzzer_code = f"{predefine_content}{header_content}{code_content}"
    #             # 保存代码
    #             with open(gen_file_path, "w") as f:
    #                 f.write(fuzzer_code)
    #             # 编译代码
    #             process = subprocess.Popen(gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    #             stdout, error_message = process.communicate()
    #             if isinstance(error_message, bytes):
    #                 error_message = error_message.decode('utf-8',errors='ignore')
    #             # 假设存在编译错误，预先构造prompt
    #             ins = INS_regenerate_compile(fuzzer_code,error_message)
    #             prompt_str = construct_prompt_str(ins,"",USE_MODEL_TYPE)
    #             logger.info(construct_prompt_str(ins,"","content"))

    #             for _ in range(4):
    #                 # 如果编译成功，则直接退出
    #                 if len(error_message) == 0:
    #                     # 生成成功，保存文件
    #                     output_file_name = output_path + "-0.c"
    #                     with open(output_file_name, "w") as f:
    #                         f.write(fuzzer_code)

    #                     print("generate success")
    #                     cur_state = "regen"
    #                     break
    #                 # 编译失败，重新构造构造编译错误代码
    #                 print("[STATE] GEN HARNESS CODE - recompile")
    #                 result = run_llm_custom(prompt_str)
    #                 logger.info(result)
    #                 # 提取代码
    #                 content_list = result.split("```c")
    #                 fuzzer_code = ""
    #                 for one_code in content_list[::-1]:
    #                     if "LLVMFuzzerTestOneInput(" in one_code:
    #                         fuzzer_code = one_code.split("```")[0]
    #                         break
    #                 logger.info(fuzzer_code)
    #                 with open(gen_file_path, "w") as f:
    #                     f.write(fuzzer_code)
    #                 process = subprocess.Popen(gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    #                 stdout, error_message = process.communicate()
    #                 if isinstance(error_message, bytes):
    #                     error_message = error_message.decode('utf-8',errors='ignore')

    #             # 如果cur_state说明4次编译尝试失败，则回退重新生成
    #             if cur_state != "regen":
    #                 if cyc_time < 3:
    #                     cur_state = cyc_state
    #                     cyc_time += 1
    #                 else:
    #                     if cyc_state == "api":
    #                         cur_state = "exit"
    #                         print("generate failure")
    #                     else:
    #                         cyc_time = 1
    #                         cyc_state = state[max(state.index(cyc_state)-1,0)]
    #                         cur_state = cyc_state
    #         elif cur_state == "regen":
    #             # TODO 编写regen
    #             # 进入到此状态，说明已经生成了一个能够编译的libfuzzer代码了，因此不到万不得已，不会轻易回退。
    #             print("[STATE] RUN AND REGEN HARNESS CODE")
    #             process = subprocess.Popen(run_gen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    #             stdout, error_message = process.communicate()
    #             if isinstance(error_message, bytes):
    #                 error_message = error_message.decode('utf-8',errors='ignore')

    #         elif cur_state == "exit":
    #             print("exit")
    #             break
    
