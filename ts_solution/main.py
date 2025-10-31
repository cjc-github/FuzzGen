import os
import argparse
from Analysis import *
# import sys
import Data
import json





cpp_lib_path = "C:/Code/tree-sitter-cpp/build/my-cpp-language.dll"
# lib_path = "C:/Code/tree-sitter-cpp/build/cpp.dll"
cpp_lang = "cpp"


c_lib_path = "C:/Code/tree-sitter-c/build/my-c-language.dll"
# lib_path = "C:/Code/tree-sitter-cpp/build/cpp.dll"
c_lang = "c"

log_path = "run.log"
''' lang config dict sample
{
    "cpp":"C:/Code/tree-sitter-cpp/build/my-cpp-language.dll",
    "c":"C:/Code/tree-sitter-c/build/my-c-language.dll"
}
'''

# C:\Code\OmniCorp\data_10G\4171-master
#C:\Code\OmniCorp\data_10G\492-v2.9.3
# C:\Code\OmniCorp\data_10G\952-wireshark-3.6.6
# C:\Code\OmniCorp\data_10G\492-v2.9.3
# D:\BaiduNetdiskDownload\libfuzz\4278601953788064455-v3.8.0
# D:\BaiduNetdiskDownload\libfuzz\4278601953788064455-v3.8.0
# D:\BaiduNetdiskDownload\libfuzz\4984410955850285214-386.45958
# D:\BaiduNetdiskDownload\libfuzz\5216044857212535033-v27.9.19
# /root/libfuzzer_data/41567-20220405
# /root/libfuzzer_data/1191054-0.9.1
# /root/libfuzzer_data/fuzz_test3/423-v4.3.4
# /root/libfuzzer_data/41567-20220405
# /root/libfuzzer_data/4984410955850285214-386.45958

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')

    parser.add_argument('-i',"--input" ,type=str, help='包含所有工程文件夹的文件夹')
    parser.add_argument("-o","--output",type=str,help='输出数据库的文件夹')
    parser.add_argument("-lc","--lang_config",type=str,help="tree-sitter语言配置文件")
    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output
    lang_config = args.lang_config

    with open(lang_config,'r') as f:
        config_dict = json.load(f)

    # config_dict = {}
    # config_dict[c_lang] = c_lib_path
    # config_dict[cpp_lang] = cpp_lib_path

    path_list = []
    if os.path.exists(log_path):
        with open(log_path,'r') as f:
            content = f.read()
        path_list = content.split("\n")
        path_list = set(path_list)

    for dir in os.listdir(input_dir):
        project_dir = os.path.join(input_dir,dir)
        if not os.path.isdir(project_dir):
            continue
        print(f"processing {project_dir} ...")
        if project_dir in path_list:
            continue

        project = Data.CXXProject(project_dir,config_dict)
        if len(project.fuzz_file_list) == 0:
            with open(log_path,"a") as f:
                f.write(project_dir+'\n')
            continue
        # project.save_to_files(output_dir)
        project.analyze_all_libfuzzer()
        project.save_as_fuzzer(output_dir)
        with open(log_path,"a") as f:
            f.write(project_dir+'\n')
    print("Run Over. Have a nice day!!")
    
   


