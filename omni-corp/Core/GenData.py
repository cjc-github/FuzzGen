from Core.CustomStructure import *
from Core.CustomAlgorithm import *
from Core.APIWarp import *
from Core.api import *
from Core.promptRUN import *
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
import json
from tqdm import tqdm


'''
针对一个工程文件夹进行分析，直接整理出目标文件
找到fuzzer文件夹，将fuzzer部分打标签为1，其他的函数标签为0，标签为0的函数中剔除行数<10的。

下面要做的，遍历文件夹，将所有函数提取，并管理，然后搜索函数，最后打标签，并输出到文本中。
以libfuzzer为主，分析libfuzzer所带的所有文件
'''

class CXXProject(object):
    def __init__(self,project_dir) -> None:
        self.project_dir = project_dir
        self.all_files = []
        self.all_file_dict = {}
        self.all_file_obj_dict = {}
        self.all_funcs = []
        self.readme =""
        self.all_class_dict = {}
        # self.__run()
        self.initial()

    def __is_need_file(self,file_name):
        file_extension = os.path.splitext(file_name)[1]
        if file_extension in Code_suffix:
            return True
        return False
    def filter_file_by_llm(self,model_type):
        print(f"[project] filtering files by llm")
        self.parse_readme_file()#读取readme文件
        if not self.readme:
            return
        lines = self.readme.splitlines()#将字符串按行分割为列表，移除默认移除换行符。
        new_string = "\n".join(lines[:500])#取前500行
        readme_summary = RUN_prompt_get_readme_summary(new_string,model_type)#使用大语言模型生成摘要
        print(f"[project] readme summary: {readme_summary}")
        new_target_file_list = []
        for file_name in self.all_files:
            new_string = get_file_front_line_content(file_name,500)#取前500
            new_string = f"// {file_name} \n {new_string}"
            print(f"[project] checking {file_name}...")
            if not RUN_prompt_is_file_related(readme_summary,new_string,model_type):#大模型询问
                print(f"[project] {file_name} not related to project, delete")
                continue
            print(f"[project] {file_name} related to project")
            new_target_file_list.append(file_name)
        self.all_files = new_target_file_list[:]



    def __get_all_files(self):
         for root, _, filenames in os.walk(self.project_dir):
             for filename in filenames:
                 if self.__is_need_file(filename):
                     self.all_files.append(os.path.join(root,filename))

    def judge_file_type(self,full_file_path):
        base_name = os.path.basename(full_file_path)
        suffix = base_name.split('.')[-1]
        front_base_name = base_name.split('.')[0]
        if suffix in {"c",'C'}:
            return 'c'
        elif suffix in {'cpp','cc','hpp','hh','cxx','c++','h++','hcc','inl','incl_cpp'}:
            return 'cpp'
        elif suffix in {'h','H'}:
            # 对于.h或者.H文件，很难判断是C还是C++文件，需要进一步分析文件内容
            same_front_base_name_list = self.all_base_file_dict[front_base_name][:]
            for full_one_file in same_front_base_name_list:
                if full_one_file == full_file_path:
                    continue
                tmp_suffix = os.path.basename(full_one_file).split('.')[-1]
                if tmp_suffix in {"c",'C'}:
                    return 'c'
                elif tmp_suffix in {'cpp','cc','hpp','hh','cxx','c++','h++','hcc','inl','incl_cpp'}:
                    return 'cpp'
            # 如果找不到对应的C/C++文件，那么就分析文件
            # config_cpp = Config(self.config['cpp'],'cpp')
            # config_c = Config(self.config['c'],'c')
            test_cpp = CXXFile(full_file_path,'cpp')
            count_cpp_error = 0
            for node in test_cpp.ele_list:
                if node.type == 'ERROR':
                    count_cpp_error += 1
            test_c = CXXFile(full_file_path,'c')
            count_c_error = 0
            # 遍历 C 语法树的节点列表
            for node in test_c.ele_list:
                if node.type =='ERROR':
                    count_c_error+=1
            # 比较错误数量，判断文件类型
            if count_c_error < count_cpp_error:
                return 'c'
            else:
                return 'cpp'
        return ""
    
    def initial(self):
        # self.parse_readme_file()
        self.__get_all_files()
        print(f"[Project] initial gets {len(self.all_files)} files")
        self.all_base_file_dict = dict()
        for full_file_name in self.all_files:
            base_name = os.path.basename(full_file_name)
            front_base_name = base_name.split('.')[0]
            if base_name in self.all_file_dict:
                self.all_file_dict[base_name].append(full_file_name)
            else:
                self.all_file_dict[base_name] = [full_file_name]

            if front_base_name in self.all_base_file_dict:
                self.all_base_file_dict[front_base_name].append(full_file_name)
            else:
                self.all_base_file_dict[front_base_name] = [full_file_name]

    
    def process(self):
        all_files = []
        for source_file in tqdm(self.all_files,desc="Processing Files..."):
            target_lang = self.judge_file_type(source_file)#区分文件类型
            tmp_cxx_data = NormalFile(source_file,target_lang)
            if tmp_cxx_data.is_test_file():#检查当前对象是否是一个测试文件
                continue
            tmp_cxx_data.get_namespace()#解析文件中的命名空间（namespace）定义，并将命名空间及其内容存储到 self.namespace_dict
            tmp_cxx_data.get_all_functions(self.project_dir)#从 self.ele_list 中提取所有的函数定义，并将它们封装为 func 对象，存储到 self.func_list 列表中
            tmp_cxx_data.get_all_class()#从 self.ele_list 中提取所有的类（class）和结构体（struct）定义，并将它们封装为 classstruct 对象，存储到 self.classstruct_list 列表中
            self.all_file_obj_dict[source_file] = tmp_cxx_data
            self.all_funcs += tmp_cxx_data.func_list
            all_files.append(tmp_cxx_data)
        for one_func in tqdm(self.all_funcs,desc='Processing Functions:'):
            one_func.readme = self.readme
            one_func.is_driver_func = 0 #表示该函数不是驱动函数
            one_func.get_include_file_path(all_files)
            one_func.return_parm.get_origin_define(all_files)
            for one_parm in one_func.parm_list:
                one_parm.get_origin_define(all_files)
        for one_file in all_files:
            for cs in one_file.classstruct_list:
                if cs.name:
                    cs.get_base_class_list()
                    self.all_class_dict[cs.name] = cs
    def __func_get_class(self,one_func:func):
        if not one_func.class_list:
            return None
        for class_name in one_func.class_list[::-1]:
            if class_name in self.all_class_dict:
                return class_name
        return None
    def __caller_get_class(self,one_call:caller):
        if not one_call.name_space_list:
            return None
        for class_name in one_call.name_space_list[::-1]:
            if class_name in self.all_class_dict:
                return class_name
        return None
    def __parm_get_class(self,one_parm:parm):
        if not one_parm.class_list:
            return None
        for class_name in one_parm.class_list[::-1]:
            if class_name in self.all_class_dict:
                return class_name
        return None
    def get_related_class(self):
        for one_func in self.all_funcs:
            target_class_name = self.__func_get_class(one_func)
            if not target_class_name:
                continue
            # 先找一下函数的调用函数，是否存在其他的类
            # for one_call in one_func.call_list:
            #     one_call_class_name = self.__caller_get_class(one_call)
            #     if not one_call_class_name:
            #         continue
            #     if one_call_class_name != target_class_name:
            #         if one_call_class_name not in self.all_class_dict[target_class_name].base_class_name_list:
            #             self.all_class_dict[target_class_name].related_class_set.add(one_call_class_name)

            # 再看关于函数调用参数,是否存在其他的类
            for one_parm in one_func.parm_list:
                one_parm_class_name = self.__parm_get_class(one_parm)
                if not one_parm_class_name:
                    continue
                if one_parm_class_name != target_class_name:
                    if one_parm_class_name not in self.all_class_dict[target_class_name].base_class_name_list:
                        self.all_class_dict[target_class_name].related_class_set.add(one_parm_class_name)

            # 再看函数返回参数，是否存在其他类
            return_parm_class_name = self.__parm_get_class(one_func.return_parm)
            if not return_parm_class_name:
                continue
            if return_parm_class_name != target_class_name:
                if return_parm_class_name not in self.all_class_dict[target_class_name].base_class_name_list:
                    self.all_class_dict[target_class_name].related_class_set.add(return_parm_class_name)

    '''
    解析readme文件
    '''
    def parse_readme_file(self):
        for file_name in os.listdir(self.project_dir):
            if os.path.isdir(os.path.join(self.project_dir,file_name)):
                continue
            lowercase_string = file_name.casefold()
            if lowercase_string in {"readme","readme.md"}:
                with open(os.path.join(self.project_dir,file_name),'rb') as f:
                    readme_content = f.read()
                    readme_content = readme_content.decode('utf-8',errors='ignore')
                if len(readme_content) == 0:
                    print("readme file contains nothing")
                self.readme = readme_content
