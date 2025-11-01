import os
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
from  Analysis import *
import os
import json
from tqdm import tqdm
from APIWarp import *
import deepseek


Code_suffix = {".cpp",".c",".h",".hpp",".cxx",".cc",".C",".inl",".c++",".h++",".hcc",".hh",".h++",".incl_cpp"}
CXX_suffix = {".cpp",".c",".cxx",".cc",".C",".c++",".incl_cpp"}
Header_suffix = {".h",".hpp"".h++",".hcc",".hh",".h++"}
CPP_LANGUAGE = Language(tscpp.language())
C_LANGUAGE = Language(tsc.language())

def bytearray2str(target_str):
    if type(target_str) == type('123'):
        return target_str
    else:
        return target_str.decode('utf-8',errors='ignore')

class caller(object):
    def __init__(self,node) -> None:
        self.node = node
        self.call_type = None
        self.func_name = ""
        self.variable = ""
        self.name_space_list = []
        self.init()

    def __hash__(self) -> int:
        return hash(bytearray2str(self.func_name)+ str(self.name_space_list))
    def __str__(self) -> str:
        return bytearray2str(self.func_name)
    def __repr__(self) -> str:
        return bytearray2str(self.func_name) + ":" + str(self.name_space_list)
    def __eq__(self,other):
        if isinstance(other,caller):
            if self.func_name == other.func_name:
                return True
        return False

    def __process_qualified_identifier(self,root_node):
        if root_node.type != "qualified_identifier":
            print(f"__process_field_expression {root_node.type} {root_node.text} is not qualified_identifier")
            return None
        stack = [root_node]
        while stack:
            node = stack.pop()
            if node.type == "namespace_identifier":
                self.name_space_list.append(node.text)
            elif node.type in {"identifier","type_identifier"}:
                self.func_name = node.text

            for child in node.children:
                if child.type not in {"argument_list","template_argument_list","parameter_list"}:
                    stack.append(child)
        self.name_space_list = self.name_space_list[::-1]
            
    def __process_field_expression(self,root_node):
        if root_node.type != "field_expression":
            print(f"{root_node.type} {root_node.text} is not field_expression ")
            return []
        stack = [root_node]
        while stack:
            node = stack.pop()
            if node.type == "identifier":
                self.variable = node.text
            elif node.type == "field_identifier":
                self.name_space_list.append(node.text)

            for child in node.children:
                if child.type not in {"argument_list","template_argument_list","parameter_list"}:
                    stack.append(child)
        self.name_space_list =self.name_space_list[::-1]
        try:
            self.func_name = self.name_space_list[-1]
        except:
            print(self.node.text)
            show_all_node(self.node)
            os._exit(0)
        self.name_space_list = self.name_space_list[:-1]


    def gen_dict(self):
        """
        生成一个字典，用于存储函数调用的相关信息。
        
        这个方法将当前实例的函数名、调用类型和命名空间列表转换为一个字典，
        其中包含了函数名、调用类型和类名列表。如果实例具有命名空间列表，
        则类名列表将包含这些命名空间。
        
        Returns:
            dict: 包含函数调用信息的字典。
        """
        call_dict = {}
        call_dict['name'] = bytearray2str(self.func_name)
        call_dict['type'] = "call"
        call_dict['class'] = []
        if self.name_space_list:
            for class_name in self.name_space_list:
                call_dict["class"].append(bytearray2str(class_name))
        return call_dict

    def init(self):
        for c in self.node.children:
            if c.type == "argument_list":
                continue
            elif c.type == "identifier":
                self.call_type = "identifier"
                self.func_name = c.text
            elif c.type == "field_expression":
                self.name_space_list = []
                self.variable = ""
                self.call_type = "field_expression"
                self.__process_field_expression(c)
                if len(self.func_name) == 0:
                    print(f"{c.text} - {c.type} is error")
            elif c.type == "qualified_identifier":
                self.call_type = "qualified_identifier"
                self.name_space_list = []
                self.__process_qualified_identifier(c)
            elif c.type == "template_function":
                self.call_type = "template_function"
                self.func_name = template_function_get_identifier(c)
            else:
                continue
    def find_declaration(self,ele_list):
        if self.call_type != "field_expression":
            return
        if self.variable == "":
            return
        for one_node in ele_list:
            if "declaration"==one_node.type:
                if self.variable not in one_node.text:
                    continue
                tmp_identifier = declaration_get_identifier(one_node)
                if tmp_identifier == self.variable:
                    self.name_space_list += declaration_get_namespacelist(one_node)
            elif "parameter_declaration" == one_node.type:
                if self.variable not in one_node.text:
                    continue
                tmp_identifier = declaration_get_identifier(one_node)
                if tmp_identifier == self.variable:
                    self.name_space_list += declaration_get_namespacelist(one_node)



class parm(object):
    def __init__(self,node) -> None:
        self.node = node
        self.body = ""
        self.name = ""
        self.class_list = []
        self.is_get_origin_define_ran = False
        self.init()
    def init(self):
        if self.node is None:
            self.type = ""
            return
        self.type = self.node.type
        if self.type == "qualified_identifier":
            tmp_class_list = qualified_identifier_get_namespace(self.node)
            self.name = tmp_class_list[-1]
            self.class_list = tmp_class_list[:-1]
        elif self.type == "type_identifier":
            self.name = self.node.text
        elif self.type == "primitive_type":
            self.name = ""
        elif self.type in {"class_specifier","struct_specifier", "enum_specifier"}:
            self.name = specifier_get_identifier(self.node)
        else:
            self.name = ""
    def get_origin_define(self,all_project_list):
        if self.is_get_origin_define_ran:
            return
        if len(self.name) == 0:
            return 
        if len(self.body) > 0:
            return  
        for one_cxx_file in all_project_list:
            # if self.name not in one_cxx_file.code:
            #     continue
            # list_nodes = get_name_node_from_root_node(one_cxx_file.root_node,self.name)
            if self.name not in one_cxx_file.id_dict:
                continue
            list_nodes = one_cxx_file.id_dict[self.name]
            for node in list_nodes:
                define_node = get_parent_till_variable_define(node,self.name)
                if define_node is None:
                    continue
                self.body = define_node.text
                self.is_get_origin_define_ran = True
                return
        self.is_get_origin_define_ran = True
    
    def gen_dict(self):
        parm_dict = {}
        parm_dict['name'] = bytearray2str(self.name)
        parm_dict['type'] = "parm"
        parm_dict['body'] = bytearray2str(self.body)
        parm_dict['class'] = []
        if self.class_list: 
            for class_name in self.class_list: 
                parm_dict['class'].append(bytearray2str(class_name))
        return parm_dict

'''
存储函数的类
#todo 将返回类型和参数定义找到
'''            
#TODO 关于函数的输出格式需要进行再次定义
#函数的输出内容，除了函数本体，还应该包括函数返回值类型（如果不是预定义的类型需要指出），函数的非预定义参数类型。还有找到该函数的头文件位置，主要包括函数的定义，参数的定义，尤其是结构体的具体内容，枚举类型的具体内容。
class func(object):
    def __init__(self,node) -> None:
        self.node = node
        self.type = "function"
        self.contain_file_path = ""
        self.include_file_path = ""
        self.readme = ""
        self.call_list = []
        self.is_get_namespace_ran = False
        self.is_get_include_file_path_ran = False
        self.init()
        
    def __hash__(self):
        return hash(self.body)
    def __repr__(self):
        return bytearray2str(self.name)+ ":"+ str(self.class_list)
    
    def init(self):
        self.return_type = function_definition_get_return_type(self.node)
        self.return_parm = parm(function_definition_get_return_node(self.node))
        self.body = self.node.text
        func_list = function_definition_get_namespaces(self.node)
        parm_node_list = function_definition_get_parm_list(self.node) 
        self.parm_list = [parm(cc) for cc in parm_node_list]
        try:
            if len(func_list) == 0:
                # print(f"ERROR {self.body} ")
                # 如果是操作符或者析构函数，这些一般不会用在libfuzzer构建上，因此直接忽略
                self.name = ""
                self.class_list = []
            else:
                # 通过向上回溯，看看是不是在类中或者namespace中
                tmp_class_list = get_parent_till_namespace(self.node)
                new_class_list = []
                for class_name in tmp_class_list:
                    if class_name not in func_list:
                        new_class_list.append(class_name)
                self.class_list = new_class_list[::-1] + func_list[:-1]
                self.name = func_list[-1]
        except Exception as e:
            print(f"[func] TYPE PROCESSING ERROR! {e}")
            print(self.node.text)
            show_all_node(self.node)
            print("="*120)
            show_all_node(self.node.parent)
            os._exit(0)
        # 获取函数的所有调用函数
        self.get_all_call()
    def get_all_call(self):
        # 如果当前函数没有名字，则不继续处理
        if self.name == "":
            return
        self.ele_list = iterate_tree(self.node)
        for node in self.ele_list:
            if "call_expression" in node.type:
                tmp_caller = caller(node)
                tmp_caller.find_declaration(self.ele_list)
                self.call_list.append(tmp_caller)
        self.call_list = list(set(self.call_list))

    def get_namespace(self,namespace_dict):
        if self.is_get_namespace_ran:
            return
        for key in namespace_dict:
            if self.body in namespace_dict[key]:
                self.class_list = [key] + self.class_list
        self.is_get_namespace_ran = True

    def show_all(self):
        show_all_node(self.node)

    def set_contain_file_path(self,file_path):
        self.contain_file_path = file_path

    def show_func(self):
        func_content = f"name:{self.name}\treturn:{self.return_type}\tclass:{self.class_list}"
        print(func_content)

    def get_include_file_path(self,all_cxxfiles):
        if len(self.include_file_path) > 0:
            return 
        if self.is_get_include_file_path_ran:
            return
        base_name = os.path.basename(self.contain_file_path)
        file_name = os.path.splitext(base_name)[0]
        # 第一轮，找文件名相同的.hxx文件中的文件是否存在定义
        for one_cxx_file in all_cxxfiles:
            tmp_base_name = os.path.basename(one_cxx_file.file_path)
            if tmp_base_name == base_name or ".c" in tmp_base_name:
                continue
            tmp_file_name = os.path.splitext(tmp_base_name)[0]
            if file_name == tmp_file_name:
                for node in one_cxx_file.function_declarator_list:
                    for c in node.children:
                        if c.type not in {"argument_list","template_argument_list","parameter_list"}:
                            if self.name in c.text:
                                self.include_file_path = one_cxx_file.file_path
                                self.is_get_include_file_path_ran = True
                                return
                        else:
                            break
        # 第二轮，所有文件都找一轮
        for one_cxx_file in all_cxxfiles:
            tmp_base_name = os.path.basename(one_cxx_file.file_path)
            if tmp_base_name == base_name or ".c" in tmp_base_name:
                continue
            tmp_file_name = os.path.splitext(os.path.basename(one_cxx_file.file_path))[0]
            if file_name != tmp_file_name:
                for node in one_cxx_file.function_declarator_list:
                    for c in node.children:
                        if c.type not in {"argument_list","template_argument_list","parameter_list"}:
                            if self.name in c.text:
                                self.include_file_path = one_cxx_file.file_path
                                self.is_get_include_file_path_ran = True
                                return
                        else:
                            break
        self.is_get_include_file_path_ran = True
    def gen_func_dict(self):
        func_dict = {}
        func_dict["name"] = bytearray2str(self.name)
        func_dict['type'] = 'function'
        func_dict["body"] = bytearray2str(self.body)
        func_dict["class"] = []
        if len(self.class_list) > 0:
            for one_class in self.class_list:
                func_dict["class"].append(bytearray2str(one_class))
        func_dict["include"] = ""
        if len(self.include_file_path) > 0:
            func_dict["include"] = bytearray2str(self.include_file_path)

        func_dict["contain"] = ""
        if len(self.contain_file_path) > 0:
            func_dict["contain"] = bytearray2str(self.contain_file_path)

        func_dict["readme"] = ""
        if len(self.readme) > 0:
            func_dict["readme"] = bytearray2str(self.readme)

        func_dict["parm"] = []
        if len(self.parm_list) > 0:
            for one_parm in self.parm_list:
                if len(one_parm.name) > 0:
                    func_dict["parm"].append(one_parm.gen_dict())

        func_dict["return"] = ""
        if len(self.return_parm.name) > 0:
            func_dict["return"] = self.return_parm.gen_dict()
        func_dict['call_list'] = []
        for one_call in self.call_list:
            func_dict['call_list'].append(one_call.gen_dict())
        return func_dict





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
            for node in test_c.ele_list:
                if node.type =='ERROR':
                    count_c_error+=1
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
            target_lang = self.judge_file_type(source_file)
            tmp_cxx_data = NormalFile(source_file,target_lang)
            if tmp_cxx_data.is_test_file():
                continue
            tmp_cxx_data.get_namespace()
            tmp_cxx_data.get_all_functions(self.project_dir)
            tmp_cxx_data.get_all_class()
            self.all_file_obj_dict[source_file] = tmp_cxx_data
            self.all_funcs += tmp_cxx_data.func_list
            all_files.append(tmp_cxx_data)
        for one_func in tqdm(self.all_funcs,desc='Processing Functions:'):
            one_func.is_driver_func = 0
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
                # prompt = Prompt("mistral")
                prompt = Prompt("content")
                q = {}
                # q["Instruction"] = "根据下面的Readme的一部分，用一句话概括该工程实现的核心功能，只需要介绍实现的功能即可，其他的不需要提及\n"
                q["Instruction"] = "Based on a section of the Readme, summarize the core functionality of the project in one sentence. Focus only on the functionality implemented, without mentioning any other details.\n"
                q["Input"] = readme_content[:5000]
                readme_prompt = prompt.gen_prompt(q)
                api = llamacpp(host="10.17.188.201",port=7070)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面描述，简要概括一下工程实现的核心功能。\n"
                q["Instruction"] = "Briefly summarize the core functionality implemented in the project based on the description provided.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面描述，用一句话概括工程的核心功能:\n"
                q["Instruction"] = "Summarize the core functionality of the project in one sentence based on the description provided.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面的描述，用一句话且用尽可能少的文字总结下面文字中工程的核心功能\n"
                q["Instruction"] = "Summarize the core functionality of the project in the text below using one sentence and as few words as possible.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f"如果要对实现【{result}】功能的工程编写libfuzzer，都需要测试具有哪些功能的函数？\n"
                q["Instruction"] = f"What functions need to be tested when writing a libfuzzer for a C/C++ source code project that aims to achieve the functionality of [{result}]?\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f"用一段话非常简要概括下面的文字\n"
                q["Instruction"] = f"Summarize the text briefly in a single paragraph.\n"
                # q["Input"] = result + "\n- 选择各功能的初始化和资源销毁回收相关函数，这些函数是libfuzzer测试功能所必须的函数。\n - 从内存读取数据的初始化函数要优先于从文件读取数据的初始化函数。\n - 一些资源或者功能初始化函数，可能看上去比较简单，但是也是libfuzzer构造所必须的，需要进行选择。"
                q["Input"] = result + "\n- Select the initialization and resource destruction/recycling functions that are essential for the libfuzzer testing functionality.\n - The initialization function for reading data from memory should be prioritized over the initialization function for reading data from files.\n - Some resource or functionality initialization functions may seem simple, but they are also necessary for the construction of libfuzzer and should be selected accordingly."
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f" 根据下面的描述，用一段话非常概要的描述下面的文字\n"
                q["Instruction"] = f" Based on the description below, provide a very concise summary of the text in a single sentence.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = api.run(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)
                # while True:
                #     api = llamacpp(host="10.17.188.201",port=7070)
                #     result = api.run(readme_prompt)
                #     print(result)
                #     if len(result) < 2000:
                #         break
                self.readme = result



'''
一个CXXFile类，主要是维护一个C/C++文件内所有的node
'''
class CXXFile(object):
    def __init__(self, file_path, config) -> None:
        self.file_path = file_path
        self.config = config
        self.id_dict = {}
        self.function_declarator_list = []
        self.readme = ""
        self.initialize()

    def remove_comments(self,code):
        tree = self.parser.parse(code)
        root_node = tree.root_node
        ele_list = iterate_tree(root_node)
        to_remove = []
        for node in ele_list:
            if node.type == "comment":
                to_remove.append(node.text)
        removed_code = code
        for comment in to_remove:
            removed_code = removed_code.replace(comment,b'')
        return removed_code

    def setProjectREADME(self,readme):
        self.readme = readme

    def __iterate_tree(self):
        stack = [self.root_node]
        return_list = []
        while stack:
            node = stack.pop()
            return_list.append(node)
            if node.type in {"type_identifier","identifier"}:
                if node.text in self.id_dict:
                    self.id_dict[node.text].append(node)
                else:
                    self.id_dict[node.text] = [node]
            elif node.type == "function_declarator":
                self.function_declarator_list.append(node)
            for child in node.children:
                stack.append(child)
        return return_list
    
    def initialize(self):
        try:
            with open(self.file_path,"rb") as f:
                self.code = f.read()
            
        except Exception as e:
            print(f"[FATAL] {self.file_path} read error: {e}")
            os._exit(0)

        try:
            if self.config == 'cpp':
                self.parser = Parser(CPP_LANGUAGE)
            elif self.config == 'c':
                self.parser = Parser(C_LANGUAGE)

            # tree = self.parser.parse(bytes(self.code, 'utf8'))
            tree = self.parser.parse(self.code)
            
            self.root_node = tree.root_node

            self.ele_list = self.__iterate_tree()

            # traverse_all_node(self.root_node, self.ele_list)
            # self.ele_list = iterate_tree(self.root_node)
            if len(self.ele_list) == 0:
                print(f"Nothing Read from {self.file_path}")
            
        except Exception as e:
            print(f"[FATAL] Error occurred while parsing file: {e} in {self.file_path}")
            os._exit(0)



'''
正常文件
'''
class NormalFile(CXXFile):
    def __init__(self, file_path, config) -> None:
        super().__init__(file_path, config)
        # self.__get_namespace()
        # self.__get_all_functions()
        
        self.classstruct_list = []
        self.is_fuzzer_file = 0
        self.func_list = []

        self.is_get_all_functions_ran = False
        self.is_get_namespace_ran = False
        self.is_get_all_class_ran = False
    def is_test_file(self):
        for node in self.ele_list:
            if node.type == 'preproc_include':
                if b"gtest.h" in node.text:
                    return True
        return False
    def get_namespace(self):
        if self.is_get_namespace_ran:
            return
        self.namespace_dict = dict()
        for node in self.ele_list:
            if node.type == "namespace_definition":
                for c in node.children:
                    if c.type == "namespace_identifier":
                        self.namespace_dict[c.text] = node.text
                        break
        self.is_get_namespace_ran = True

    def get_all_functions(self,project_dir=""):
        if self.is_get_all_functions_ran:
            return
        self.func_list = []
        for node in self.ele_list:
            if node.type == "function_definition":
                tmp_func = func(node)
                tmp_func.readme = self.readme
                # tmp_func.get_namespace(self.namespace_dict)
                contain_path = self.file_path.replace(project_dir,"")
                tmp_func.set_contain_file_path(contain_path)
                if len(tmp_func.name) > 0:
                    self.func_list.append(tmp_func)
        self.is_get_all_functions_ran = True
    
    def get_all_class(self):
        if self.is_get_all_class_ran:
            return
        for node in self.ele_list:
            if node.type in {"class_specifier","struct_specifier"}:
                if b'{' in node.text and b'}' in node.text:
                    tmp_class = classstruct(node)
                    tmp_class.get_namespace(self.namespace_dict)
                    tmp_class.is_fuzzer_class = self.is_fuzzer_file
                    self.classstruct_list.append(tmp_class)
            elif node.type == "function_definition":
                for child in node.children:
                    if child.type in {"class_specifier","struct_specifier"}:
                        tmp_class = classstruct(node)
                        tmp_class.get_namespace(self.namespace_dict)
                        tmp_class.is_fuzzer_class = self.is_fuzzer_file
                        self.classstruct_list.append(tmp_class)
                
        self.is_get_all_class_ran = True

#TODO 下一步要将类中的各个函数加进去

class classstruct(object):
    def __init__(self,node) -> None:
        self.name = ""
        self.node = node
        self.body = node.text
        self.type = ""
        self.func_name_list = []
        self.func_name_node_dict = {}
        self.base_class_name_list = []
        self.is_fuzzer_class = 0
        self.related_class_set = set()
        self.init()
    def gen_dict(self):
        class_dict = {}
        class_dict['name'] = self.name.decode("utf-8",errors='ignore')
        class_dict['type'] = self.type
        # 最后给出的是去掉comment的类
        clean_code = remove_comments(self.node)
        clean_code = clean_code.replace(b"\n\n",b"\n")
        class_dict['body'] = clean_code.decode("utf-8",errors='ignore')
        class_dict['base'] = []
        for class_name in self.base_class_name_list:
            class_dict['base'].append(class_name.decode("utf-8",errors='ignore'))
        class_dict['relate'] = []
        for class_name in self.related_class_set:
            class_dict['relate'].append(class_name.decode("utf-8",errors='ignore'))
        return class_dict
        
    def get_namespace(self,namespace_dict):
        for key in namespace_dict:
            if key in self.base_class_name_list:
                continue
            if self.node.text in namespace_dict[key]:
                self.base_class_name_list = [key] + self.base_class_name_list

    def init(self):
        if self.node.type == "class_specifier":
            self.type = "class"
            for child in self.node.children:
                if child.type == "type_identifier":
                    self.name = child.text
                    return
                elif child.type == "qualified_identifier":
                    name_space_list = qualified_identifier_get_namespace(child)
                    self.name = name_space_list[-1]
                    self.base_class_name_list += name_space_list[:-1]
                    return
        elif self.node.type == "function_definition":
            for child in self.node.children:
                if child.type == "identifier":
                    self.name = child.text
                    return
                elif child.type == "ERROR":
                    for cc in child.children:
                        if cc.type == "identifier":
                            self.name = cc.text
                            return
                elif child.type == "struct_specifier":
                    self.type = "struct"
                elif child.type == "class_specifier":
                    self.type = "class"
        elif self.node.type =="struct_specifier":
            self.type = "struct"
            for child in self.node.children:
                if child.type == "type_identifier":
                    self.name = child.text
                    return
                elif child.type == "qualified_identifier":
                    name_space_list = qualified_identifier_get_namespace(child)
                    self.name = name_space_list[-1]
                    self.base_class_name_list += name_space_list[:-1]
                    return
                
    def get_base_class_list(self):
        code = self.node.text
        keycode = code.split(b'{')[0]
        if b':' not in keycode:
            return
        replace_bytearray = keycode.split(b':')[0]

        base_class_bytearray = keycode.replace(replace_bytearray,b'')

        base_class_list = base_class_bytearray.split(b' ')
        for class_name in base_class_list:
            if len(class_name) < 2:
                continue
            if class_name in {b'public',b'private'}:
                continue
            if b'::' in class_name:
                tmp_list = class_name.split(b"::")
                if len(tmp_list) > 0:
                    tmp_list.reverse()
                    self.base_class_name_list += tmp_list
            else:
                self.base_class_name_list.append(class_name)

   
    def get_all_funcs(self):
        self.func_name_list = []
        ele_list = iterate_tree(self.node)
        for node in ele_list:
            if node.type == "function_definition":
                tmp_func = func(node)
                if len(tmp_func.name) > 0 and tmp_func.name != self.name:
                    self.func_name_list.append(tmp_func.name)
                    self.func_name_node_dict[tmp_func.name] = node.text
            # if node.type == "function_declarator":
            #     for child in node.children:
            #         if child.type == "identifier":
            #             self.func_name_list.append(child.text)