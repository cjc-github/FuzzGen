import os
from Analysis import *
from APIWarp import *
import Data
import json
import tree_sitter
from pygments.lexers import guess_lexer
from pygments.lexers import get_lexer_for_filename
def detect_language(file_path):
    with open(file_path, 'r') as file:
        source_code = file.read()
        # source_code = source_code.decode('utf-8',errors='ignore')
        lexer = guess_lexer(source_code)
        language = lexer.name
        return language

def path_to_list(path):
    parts = []
    while True:
        path, part = os.path.split(path)
        if part != "":
            parts.append(part)
        else:
            if path != "":
                parts.append(path)
            break
    parts.reverse()
    return parts

cpp_lib_path = "C:/Code/tree-sitter-cpp/build/my-cpp-language.dll"
cpp_lib_path = "C:/Code/tree-sitter-cpp/build/cpp.dll"
cpp_lang = "cpp"


c_lib_path = "C:/Code/tree-sitter-c/build/my-c-language.dll"
c_lib_path = "C:/Code/tree-sitter-c/build/c.dll"
c_lang = "c"

source_file = "C:/Code/exiv2/src/image.cpp"
source_file = "C:/Code/exiv2/src/exif.cpp"
source_file = "C:/Code/exiv2/src/value.cpp"
source_file = "C:/Code/OmniCorp/data_10G/1165-v3.0.1/benchmark/partial_tweets/tweet.h"
source_file1 = "C:/Code/exiv2/include/exiv2/image.hpp" 
source_file1 = "C:/Code/exiv2/include/exiv2/exif.hpp" 
source_file1 = "C:/Code/OmniCorp/data_10G/1127-6.0.0/test/fuzzing/hb-shape-fuzzer.cc"
# source_file = "C:/Code/exiv2/fuzz/fuzz-read-print-write.cpp" 
source_file = "../test.cpp" 
source_file = "C:/Code/OmniCorp/data_10G/37933-master/capstone/suite/fuzz/fuzz_harness.c"
source_file1 = "C:/Code/OmniCorp/data_10G/37933-master/capstone/cs.c"

source_file1 = "C:/Code/exiv2/include/exiv2/image.hpp"
source_file1 = "C:/Code/OmniCorp/data_10G/42744-0.9.2-rc1.post2/llvm\keystone/ks.cpp"
source_file1 = "C:/Code/exiv2/src/pngimage.cpp"
source_file1 = "C:/Code/exiv2/fuzz/fuzz-read-print-write.cpp"


source_file = "C:/Code/OmniCorp/data_10G/42744-0.9.2-rc1.post2/suite/fuzz/fuzz_asm_arm_thumbv8.c"
source_file = "C:/Code/fuzz_test/967-0.9.0/fuzzing/elf_fuzzer.cpp"

project_dir = "C:/Code/exiv2"
project_dir = "C:/Code/OmniCorp/data_10G/3663-v4.4.LTS"
project_dir = "C:/Code/OmniCorp/data_10G/37933-master"
project_dir = "C:/Code/OmniCorp/data_10G/967-0.9.0"
project_dir = "C:/Code/fuzz_test/cgltf"

'''
C:\Code\OmniCorp\output\42744-0.9.2-rc1.post2_1.json is wrong
C:\Code\OmniCorp\output\41478-v1.8.0.9_1.json is wrong
C:\Code\OmniCorp\output\967-0.9.0_1.json is wrong
'''

config_dict = {}
config_dict[c_lang] = c_lib_path
config_dict[cpp_lang] = cpp_lib_path
config_c = Data.Config(c_lib_path,'c')
config_cpp = Data.Config(cpp_lib_path,'cpp')

# print(source_file1)


target_set = set()

to_analyze = [source_file1]
project_dir = "C:/Code/exiv2"
# project_dir = "C:/Code/OmniCorp/data_10G/141373-v0.9.9"
# project_dir = "D:/BaiduNetdiskDownload/fuzz/141373-v0.9.9"
source_file1 = "C:/Code/OmniCorp/data_10G/1187566-v0.4.0pre4/contrib/libucl/tests/fuzzers/ucl_msgpack_fuzzer.c"
# D:\tmp_fuzzer_data\1187566-v0.4.0pre4
with open("../Lang_config.json","r") as f:
    config = json.load(f)
config_cpp = Data.Config(config['cpp'],'cpp')
config_c = Data.Config(config['c'],'c')
test_cpp = Data.NormalFile(source_file1 ,config_c)
count = 0
count_len = 0
for node in test_cpp.ele_list:
    if node.type == "ERROR":
        count += 1
        count_len += len(node.text)
        # print(node.type,node.text)
print('c count:',count)
print('c len:',count_len)

test_cpp = Data.NormalFile(source_file1 ,config_cpp)
count = 0
count_len = 0
for node in test_cpp.ele_list:
    if node.type == "ERROR":
        count += 1
        count_len += len(node.text)
        # print(node.type,node.text)
print('cpp count:',count)
print('cpp len:',count_len)
os._exit(0)
# driver_cpp = Data.DriverFile("D:/BaiduNetdiskDownload/fuzz/141373-v0.9.9/test/fuzzing/server_fuzzer.cc" ,config_cpp)

# test_cpp.get_namespace()
# test_cpp.get_all_functions()
# test_cpp.get_all_class()
# for cs in test_cpp.classstruct_list:
#     print(cs.name)
#     cs.get_base_class_list()
#     print(cs.base_class_name_list)
#     print(cs.node.text[:100])
#     # show_all_node(cs.node)
# # show_all_node(test_cpp.root_node)
# print('='*20)
# for one_func in test_cpp.func_list:
#     print(one_func.name,one_func.class_list)
    
# print('='*20)
# driver_cpp.get_all_call()
# for one_call in driver_cpp.call_list:
#     print(one_call.func_name,one_call.name_space_list)
#     if one_call.call_type == "field_expression":
#         print("variable",one_call.variable)
# os._exit(0)

test_project = Data.CXXProject(project_dir,config)
print(test_project.fuzz_file_list)
test_project.analyze_all_libfuzzer()
dirver = test_project.driver_list[-1]
print(dirver.file_path)
dirver_dict = {}
print("one call")
for one_call in dirver.call_list:
    print(one_call.func_name, one_call.name_space_list)
print("="*120)
print("dirver funcs")
for one_func in list(set(dirver.label1_list)):
    print(one_func.name,one_func.class_list)
print("="*20)
print("class name")
for one_class in dirver.label1_class:
    print(one_class.name)
    # print(one_func.body)

# for class_name in test_project.all_class_dict:
#     one_class = test_project.all_class_dict[class_name]
#     print(one_class.name,one_class.base_class_name_list)
    


# for one_func in dirver.label1_list:
#     for one_call in dirver.call_list:
#         if one_call.func_name == one_func.name:
#             print(one_func.name)
#             print("call",one_call.name_space_list,one_call.variable)
#             # print(one_func.body)
#             print("func",one_func.class_list)
#             ins = set(one_call.name_space_list) & set(one_func.class_list)
#             print(len(ins))
# test_project.save_as_fuzzer("../")
os._exit(0)
test_cpp = Data.DriverFile(source_file1,config_cpp)
test_cpp.get_all_related_files(project_dir)
print(test_cpp.related_files)
os._exit(0)
all_files = []
for root, _, filenames in os.walk(project_dir):
    for filename in filenames:
        all_files.append(os.path.join(root, filename))


while len(to_analyze) > 0:
    source_file = to_analyze.pop()
    test_cpp = Data.NormalFile(source_file,config_cpp)
    result = []
    for node in test_cpp.ele_list:
        if node.type == "preproc_include":
            ele = iterate_tree(node)
            for n in ele:
                if n.type == "string_content":
                    tmp_str = n.text.decode("utf-8",errors="ignore")
                    result.append(tmp_str)
                elif n.type == "system_lib_string":
                    tmp_str = n.text.decode("utf-8",errors="ignore")
                    tmp_str = tmp_str.replace("<","")
                    tmp_str = tmp_str.replace(">","")
                    result.append(tmp_str)
    for file_name in result:
        for target in all_files:
            tmp_target = target.replace(project_dir,"")
            tmp_list = path_to_list(tmp_target)
            include_list = path_to_list(file_name)
            is_contain = True
            tmp_list.reverse()
            include_list.reverse()
            for i,one in enumerate(include_list):
                if one != tmp_list[i]:
                    is_contain = False
                    break
            if is_contain:
                if target not in target_set:
                    target_set.add(target)
                    to_analyze.append(target)
                    # print(file_name,target)
print(target_set)
test_cpp = Data.NormalFile(source_file1,config_cpp)




os._exit(0)

prompt = Prompt("codeqwen")
all_content = ""
for func in test_cpp.func_list:
    target_text = ""
    func_node = func.node
    all_content += func.body.decode("utf-8",errors='ignore').split("{")[0] + '{\n'
    all_nodes = iterate_tree(func_node)
    for node in all_nodes:
        if node.type == "call_expression":
            target_text += node.text.decode('utf-8',errors='ignore')
            target_text += "\n"
            all_content += node.text.decode('utf-8',errors='ignore') + "\n"
    all_content += "}\n"
    q = {}
    q["Instruction"] = "一句话总结下面函数的功能"
    print(func.body.decode("utf-8",errors='ignore'))
    print('**==**')
    print(target_text)
    q["Input"] = func.body.decode("utf-8",errors='ignore')
    myprompt = prompt.gen_prompt(q)
    api = llamacpp(host="10.17.188.201",port=7070)
    result = api.run(myprompt)
    print("Answer:")
    print(result)
    all_content += f"/*上面函数功能是:{result}*/\n"
    print("="*120)
    
print(all_content)

# test1_cpp = Data.DriverFile(source_file,config_cpp)
# test1_cpp.showALLCaller()

# for one_func in test_cpp.func_list:
#     print(one_func.name)

# show_all_node(test_cpp.root_node)

# test_project = Data.CXXProject(project_dir,config_dict)
# for one_func in test_project.label1_funcs:
#     print(f"harness func {one_func.name}")
# print(test_project.label1_funcs)

print("Run Over. Have a nice day!!")

# test_project.save_to_files("D:/tmp/")

# print(test_project)
# for one_func in test_cpp.func_list:
#     print(f"{one_func.name} {one_func.body}")
#     for one_parm in one_func.parm_list:
#         print(f"\t{one_parm.name} {one_parm.namespaces}")
#         if len(one_parm.name) > 0:
#             list_nodes = get_name_node_from_root_node(test1_cpp.root_node,one_parm.name)
#             for node in list_nodes:
#                 print(f"\t{node.type}-{node.text}")
#                 define_node = get_parent_till_variable_define(node,one_parm.name)
#                 if define_node is None:
#                     continue
#                 print(f"\t\tdefine node is {define_node.text}")


    # one_func.get_include_file_path(test_project.all_cxxfiles)
    # if len(one_func.include_file_path) ==0:
    #     print(f"{one_func.name} -- {one_func.body} -- {one_func.include_file_path}")

# show_all_node(test_cpp.root_node)

# for one_func in test_project.label1_funcs:
#     print(f"{one_func.name} -- {one_func.class_list}")
    # print(f"{one_func.return_parm.name}--{one_func.return_parm.body}")

# for one_func in test_cpp.func_list:
#     one_func.show_func()

#     print(get_parent_till_namespace(one_func.node))
#     one_func.get_arglist()
#     # one_func.show_all()
#     for one_parm in one_func.parm_list:
#         print(f"{one_parm.node.text}")


