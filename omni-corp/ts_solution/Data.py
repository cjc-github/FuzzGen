import os
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
from  Analysis import *
import os
import json
from tqdm import tqdm
from APIWarp import *
'''
函数的各种定义

在 C++ 中，变量声明的语法结构相对简单，但它的 declaration 节点的 children 可能包含以下情况：
变量名（identifier）：变量的名称是必须的，它作为声明的一部分，例如：
cpp
int x;
在这个例子中，x 是变量的名称。
类型（type）：声明中必须指定变量的类型，例如 int、float、std::string 等，例如：
cpp
int x;
在这个例子中，int 是变量的类型。
初始化表达式（initializer）：声明中可以包含初始化表达式，用于在声明时初始化变量，例如：
cpp
int x = 10;
在这个例子中，10 是初始化表达式。
修饰符（modifiers）：变量声明中可能包含一些修饰符，如 const、static、extern 等，用于修饰变量的属性，例如：
cpp
static const int SIZE = 100;
在这个例子中，static 和 const 是修饰符。
存储类别（storage class specifier）：C++ 中的变量声明可能包含存储类别，如 auto、register、extern 等，例如：
cpp
extern int globalVar;
在这个例子中，extern 是存储类别。

这些是变量声明可能包含的子节点。具体的节点结构会根据编译器的具体实现和语法分析器的设计而有所不同。

分析 call_expression

C++的函数调用主要分为以下几个场景
// 调用普通函数
functionName(arg1, arg2);

// 调用成员函数
object.method(arg1, arg2);

// 调用命名空间中的函数
namespaceName::functionName(arg1, arg2);

// 调用函数指针
*functionPointer(arg1, arg2);

// 调用模板函数
templateFunction<int>(arg1, arg2);

详情可见上一层文件夹中的test.cpp，函数调用基本上分为四种，分别是identifier，field_expression，qualified_identifier以及template_function
'''

Code_suffix = {".cpp",".c",".h",".hpp",".cxx",".cc",".C",".inl",".c++",".h++",".hcc",".hh",".h++",".incl_cpp"}
CXX_suffix = {".cpp",".c",".cxx",".cc",".C",".c++",".incl_cpp"}
Header_suffix = {".h",".hpp"".h++",".hcc",".hh",".h++"}
# Code_suffix = {".c",".h",".C",".H"}
# CXX_suffix = {".c",".C"}
# Header_suffix = {".h",".H"}

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
        return hash(self.func_name)
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
                # analysis_field_expression(c,self.field_list,identifier_list)
                # self.variable = identifier_list[0]
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
        # if self.call_type is None:
        #     print("[ERROR] Class caller Call expression unkown")
        #     show_all_node(self.node)
        #     print("=="*60)
            # os._exit(0)
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


'''

'''
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
            class_list = qualified_identifier_get_namespace(self.node)
            self.name = class_list[-1]
            self.class_list = class_list[:-1]
        elif self.type == "type_identifier":
            self.name = self.node.text
        elif self.type == "primitive_type":
            self.name = ""
        # elif self.type == "struct_specifier":
        #     self.name = specifier_get_identifier(self.node)
        # elif self.type == "enum_specifier":
        #     self.name = specifier_get_identifier(self.node)
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
        self.contain_file_path = ""
        self.include_file_path = ""
        self.is_driver_func = 0
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

        func_dict["body"] = bytearray2str(self.body)

        func_dict["class"] = []
        if len(self.class_list) > 0:
            for one_class in self.class_list:
                func_dict["class"].append(bytearray2str(one_class))
        func_dict["isdriver"] = self.is_driver_func
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



class Config(object):
    def __init__(self,lib_path,lang) -> None:
        self.lib_path = lib_path
        self.lang = lang


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
        self.all_file_dict = dict()
        self.common_file_list = []
        self.fuzz_file_list = []
        self.all_cxxfiles = []
        self.driver_list = []
        self.common_dict = dict()
        self.label1_funcs = []
        self.label0_funcs = []
        self.readme =""
        # self.__run()
        self.initial()

    def save_as_fuzzer(self,target_floder):
        if len(self.driver_list) == 0:
            print("[Save] no libfuzzer found")
            return
        project_name = os.path.basename(os.path.normpath(self.project_dir))
        funcs_selector_name = os.path.join(target_floder,f"{project_name}-funcs_selector.json")
        print(f"[save_as_fuzzer] saving {funcs_selector_name}")
        save_list = []
        for one_func in self.all_funcs:
            save_list.append(one_func.gen_func_dict())
        with open(funcs_selector_name,'w') as f:
            json.dump(save_list,f)

        for fuzzer in self.driver_list:
            libfuzzer_name = os.path.basename(fuzzer.file_path).split(".")[0]
            print(f"[save_as_fuzzer] saving {libfuzzer_name}")
            driver_file_name = os.path.join(target_floder,f"{project_name}-{libfuzzer_name}-generator.json")
            driver_dict = {}
            fuzzer_code = fuzzer.code
            driver_dict['body'] = f"// {os.path.basename(fuzzer.file_path)}\n"+remove_comments(fuzzer.root_node,fuzzer_code).decode('utf-8',errors='ignore')
            print(f"[save_as_fuzzer]  {libfuzzer_name} gen body over")
            driver_dict['cops'] = []
            if len(fuzzer.cop_fuzz_list) > 0:
                for cop_fuzzer in fuzzer.cop_fuzz_list:
                    cop_code = cop_fuzzer.code
                    tmp_code =  f"// {os.path.basename(cop_fuzzer.file_path)}\n" + remove_comments(cop_fuzzer.root_node,cop_code).decode('utf-8',errors='ignore')
                    driver_dict['cops'].append(tmp_code)
            print(f"[save_as_fuzzer]  {libfuzzer_name} gen cops over")
            driver_dict["funcs"] = []
            for one_func in fuzzer.label1_list:
                one_func.is_driver = 1
                driver_dict["funcs"].append(one_func.gen_func_dict())
            for one_func in fuzzer.label0_list:
                one_func.is_driver = 0
                driver_dict["funcs"].append(one_func.gen_func_dict())
            print(f"[save_as_fuzzer]  {libfuzzer_name} gen funcs over")
            driver_dict["class"] = []
            for one_class in fuzzer.label1_class:
                driver_dict['class'].append(one_class.gen_dict())
            print(f"[save_as_fuzzer]  {libfuzzer_name} gen class over")
            with open(driver_file_name,'w') as f:
                json.dump(driver_dict,f)
            print(f"[save_as_fuzzer] {driver_file_name} is saved")


    def __is_need_file(self,file_name):
        file_extension = os.path.splitext(file_name)[1]
        if file_extension in Code_suffix:
            return True
        return False
    
    def __get_all_files(self):
         for root, dirs, filenames in os.walk(self.project_dir):
             for filename in filenames:
                 if self.__is_need_file(filename):
                     self.all_files.append(os.path.join(root,filename))

    def __get_all_libfuzzer_files(self):
        for full_file_path in self.all_files:
            base_name = os.path.basename(full_file_path)
            file_extension = os.path.splitext(base_name)[1]
            if file_extension in CXX_suffix:
                if is_libfuzzer(full_file_path):
                    self.fuzz_file_list.append(full_file_path)

    def get_one_related(self,libfuzzer_full_file_name):
        related_files = set()
        to_analyze = [libfuzzer_full_file_name]
        # 如果fuzzer是C++，那么假定所有都是C++，反之是C

        analyzed_set = set()
        while len(to_analyze) > 0:
            source_file = to_analyze.pop()
            target_lang = self.judge_file_type(source_file)
            if len(target_lang) == 0:
                print(f'[ERROR] {source_file} can not judge type')
                os._exit(0)
            # if source_file[-2:] in {".c",".C",".h",".H"}:
            #     target_config = Config(self.config['c'],'c')
            # else:
            #     target_config = Config(self.config['cpp'],'cpp')
            # target_config =  Config(self.config[target_lang],target_lang)
            if source_file in self.common_dict:
                tmp_data = self.common_dict[source_file]
            else:
                tmp_data = NormalFile(source_file,target_lang)
                tmp_data.setProjectREADME(self.readme)
                self.common_dict[source_file] = tmp_data
            
            header_list = []
            include_list = []
            for node in tmp_data.ele_list:
                if node.type == "preproc_include":
                    include_list.append(node)
            for include_node in include_list:
                tmp_ele_list = iterate_tree(include_node)
                for node in tmp_ele_list:
                    if node.type == "string_content":
                        tmp_str = node.text.decode("utf-8",errors="ignore")
                        if ".." in tmp_str:
                            tmp_str = tmp_str.replace("..","")
                            tmp_str = tmp_str.replace("/","")
                            tmp_str = tmp_str.replace("\\","")
                        header_list.append(tmp_str)
                    elif node.type == "system_lib_string":
                        tmp_str = node.text.decode("utf-8",errors="ignore")
                        tmp_str = tmp_str.replace("<","")
                        tmp_str = tmp_str.replace(">","")
                        header_list.append(tmp_str)
                
            
            for file_name in header_list:
                include_list = path_to_list(file_name)
                if not include_list:
                    continue
                if include_list[-1] not in self.all_file_dict:
                    continue
                else:
                    for target in self.all_file_dict[include_list[-1]]:
                        tmp_target = target.replace(self.project_dir,"")
                        tmp_list = path_to_list(tmp_target)
                        is_contain = True
                        tmp_list.reverse()
                        include_list.reverse()
                        for i,one in enumerate(include_list):
                            if one != tmp_list[i]:
                                is_contain = False
                                break
                        if is_contain:
                            if target not in related_files:
                                related_files.add(target)
                                if target not in analyzed_set:
                                    to_analyze.append(target)
                                    analyzed_set.add(target)

        add_list = []
        for header_file in related_files:
            tmp_list = path_to_list(header_file)
            tmp_file_name = tmp_list[-1]
            tmp_file_name = tmp_file_name.split(".")[0]
            for one_file in self.all_files:
                if one_file in related_files:
                    continue
                if tmp_file_name not in one_file:
                    continue
                one_file_list = path_to_list(one_file)
                one_file_name = one_file_list[-1]
                one_file_name = one_file_name.split(".")[0]
                if one_file_name == tmp_file_name:
                    add_list.append(one_file)
        for one in add_list:
            # if one[-2:] in {".c",".C",".h",".H"}:
            #     target_config = Config(self.config['c'],'c')
            # else:
            #     target_config = Config(self.config['cpp'],'cpp')

            if one not in self.common_dict:
                target_lang = self.judge_file_type(one)
                if len(target_lang) == 0:
                    print(f'[ERROR] {one} cannot judge type')
                    os._exit(0)
                # target_config =  Config(self.config[target_lang],target_lang)
                tmp_data = NormalFile(one,target_lang)
                self.common_dict[one] = tmp_data

            related_files.add(one)
        return related_files

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
        
        self.__get_all_libfuzzer_files()
        print(f"[Project] initial gets {len(self.fuzz_file_list)} libfuzzer")
        # self.parse_readme_file()
    '''
    如何判断是否是related fuzz file呢？
    头文件和C文件都必须跟fuzzer在一个文件夹中。
    如果所有的C++/C源码文件都在一块，那说明作者把fuzzer和工程放在一块开发
    '''
    def fuzzer_get_cop_fuzzer(self,fuzzer):
        if len(fuzzer.related_files) == 0:
            return
        target_dir_name = os.path.dirname(fuzzer.file_path)
        same_floder_list = []
        for file_path in fuzzer.related_files:
            if file_path == fuzzer.file_path:
                continue
            if os.path.dirname(file_path) == target_dir_name:
                if is_libfuzzer(file_path):
                    continue
                same_floder_list.append(file_path)
        print(f"same_floder_list {same_floder_list}")
        # 认为如果一个文件夹内的fuzzer占比所有related files的比例太高，就认为不是cop fuzzer
        if len(same_floder_list) ==0 or float(len(same_floder_list))/len(fuzzer.related_files) > 0.6 or len(same_floder_list) > 3:
            return
        
        for file_path in same_floder_list:
            fuzzer.cop_fuzz_list.append(self.common_dict[file_path])
        # self.related_fuzz_files = same_floder_list[:]


    def analyze_one_libfuzzer(self,libfuzzer_full_file_name):
        # 先找到所有调用相关的文件
        related_files = self.get_one_related(libfuzzer_full_file_name)
        print(f"[analyze_one_libfuzzer] {libfuzzer_full_file_name} first gets {len(related_files)} related files")
        if len(related_files) == 0:
            print(f"[ERROR] {libfuzzer_full_file_name} has no related files")
            return
        fuzzer_config = self.common_dict[libfuzzer_full_file_name].config
        fuzzer = DriverFile(libfuzzer_full_file_name,fuzzer_config)
        fuzzer.setProjectREADME(self.readme)
        fuzzer.set_related_files(related_files)
        if not fuzzer.is_libfuzzer:
            return
        self.fuzzer_get_cop_fuzzer(fuzzer)
        if len(fuzzer.cop_fuzz_list) > 0:
            print(f"[analyze_one_libfuzzer] {libfuzzer_full_file_name} first gets {len(fuzzer.cop_fuzz_list)} cop fuzzer")
            for fuzz_cop in fuzzer.cop_fuzz_list:
                print(f"[analyze_one_libfuzzer] {libfuzzer_full_file_name} analyzing {fuzz_cop.file_path} cop fuzzer")
                tmp_related_files = self.get_one_related(fuzz_cop.file_path)
                related_files = related_files.union(tmp_related_files)
        print(f"[analyze_one_libfuzzer] {libfuzzer_full_file_name} finally gets {len(related_files)} related files")
        fuzzer.set_related_files(related_files)
        fuzzer.get_all_call()
        fuzzer.get_related_fuzzer()
        # self.all_cxxfiles.append(fuzzer)
        
        self.all_funcs = []
        all_files = []
        self.common_dict[fuzzer.file_path].is_fuzzer_file = 1
        self.common_dict[fuzzer.file_path].get_namespace()
        self.common_dict[fuzzer.file_path].get_all_functions(self.project_dir)
        self.common_dict[fuzzer.file_path].get_all_class()
        all_files.append(self.common_dict[fuzzer.file_path])
        for source_file in tqdm(related_files,desc=f"...{os.path.basename(libfuzzer_full_file_name)} Processing related files:"):
            is_fuzzer_file = False
            if source_file == fuzzer.file_path:
                is_fuzzer_file = True
            for cop_fuzzer in fuzzer.cop_fuzz_list:
                if source_file == cop_fuzzer.file_path:
                    is_fuzzer_file = True
                    break
            if is_fuzzer_file:
                self.common_dict[source_file].is_fuzzer_file = 1

            self.common_dict[source_file].get_namespace()
            self.common_dict[source_file].get_all_functions(self.project_dir)
            self.common_dict[source_file].get_all_class()
            if not is_fuzzer_file:
                self.all_funcs += self.common_dict[source_file].func_list
            all_files.append(self.common_dict[source_file])

        all_class_dict = {}
        for one_file in all_files:
            for cs in one_file.classstruct_list:
                if cs.name:
                    cs.get_base_class_list()
                    all_class_dict[cs.name] = cs
        print(f"[analyze_one_libfuzzer] get {len(all_class_dict.keys())} classes")
        for cs_name in all_class_dict:
            traced_set = set()
            stack = all_class_dict[cs_name].base_class_name_list[:]
            while stack:
                parent = stack.pop()
                if parent in all_class_dict:
                    for parent_name in all_class_dict[parent].base_class_name_list:
                        if parent_name not in all_class_dict[cs_name].base_class_name_list:
                            all_class_dict[cs_name].base_class_name_list.append(parent_name)
                    for base in all_class_dict[parent].base_class_name_list:
                        if base not in traced_set:
                            stack.append(base)
                            traced_set.add(base)
        if len(self.all_funcs) == 0:
            print("[ERROR no funcs get]")
            return
        
        # 对call所属的类为fuzzer自行定义的情况进行处理
        for one_call in fuzzer.call_list:
            target_list = []
            for call_name in one_call.name_space_list:
                if call_name in all_class_dict and all_class_dict[call_name].is_fuzzer_class == 1:
                    for base_class_name in all_class_dict[call_name].base_class_name_list:
                        if base_class_name in all_class_dict and all_class_dict[base_class_name].is_fuzzer_class == 0:
                            target_list.append(base_class_name)
                else:
                    target_list.append(call_name)
            one_call.name_space_list = target_list[:]        


        for one_func in tqdm(self.all_funcs,desc=f"...{os.path.basename(libfuzzer_full_file_name)} Process funcs:"):
            one_func.is_driver_func = 0
            one_func.get_include_file_path(all_files)
            one_func.return_parm.get_origin_define(all_files)
            for one_parm in one_func.parm_list:
                one_parm.get_origin_define(all_files)

        label1_func_dict = {}
        func_max_score_dict = {}
        for one_func in tqdm(self.all_funcs,desc=f"...{os.path.basename(libfuzzer_full_file_name)} Classify funcs:"):
            one_func.is_driver_func = 0
            for one_call in fuzzer.call_list:
                if one_call.func_name not in label1_func_dict:
                    label1_func_dict[one_call.func_name] = []
                    func_max_score_dict[one_call.func_name] = -1

                if one_call.func_name == one_func.name:
                    cur_score = 0
                    for call_name in one_call.name_space_list:
                        for func_class_name in one_func.class_list:
                            if call_name == func_class_name:
                                cur_score += 1
                            else:
                                if func_class_name in all_class_dict:
                                    if call_name in all_class_dict[func_class_name].base_class_name_list:
                                        cur_score += 1
                    if cur_score > func_max_score_dict[one_call.func_name]:
                        func_max_score_dict[one_call.func_name] = cur_score
                        label1_func_dict[one_call.func_name] = [one_func]
                    elif cur_score == func_max_score_dict[one_call.func_name]:
                        label1_func_dict[one_call.func_name].append(one_func)
        # Classifty labels
        for func_name in label1_func_dict:
            for one_func in label1_func_dict[func_name]:
                one_func.is_driver_func = 1
                one_func.get_include_file_path(all_files)
                one_func.return_parm.get_origin_define(all_files)
                for one_parm in one_func.parm_list:
                    one_parm.get_origin_define(all_files)
                fuzzer.label1_list.append(one_func)
                
        for one_func in self.all_funcs:
            if one_func.is_driver_func == 0:
                fuzzer.label0_list.append(one_func)

        #Classify class,
        call_class_set = set()
        for one_call in fuzzer.call_list:
            if len(one_call.name_space_list) > 0:
                for call_name in one_call.name_space_list:
                    call_class_set.add(call_name)
        

        # TODO 使用call_list中类去填充，首先填充所有的call
        for one_call in fuzzer.call_list:
            # 找出那些因为auto等无法定义的call
            if one_call.call_type == 'field_expression' and len(one_call.name_space_list) == 0:
                candidate_class_list = []
                candidate_class_set = set()
                for one_func in fuzzer.label1_list:
                    if one_call.func_name == one_func.name:
                        if str(set(one_func.class_list)) not in candidate_class_set:
                            candidate_class_list.append(one_func.class_list[:])
                            candidate_class_set.add(str(set(one_func.class_list)))
                max = -1
                target_list = []
                for candidate_class in candidate_class_list:
                    cur_score = 0
                    for class_name in candidate_class:
                        if class_name in call_class_set:
                            cur_score += 1
                    if cur_score > max:
                        target_list = candidate_class[:]
                        max = cur_score
                one_call.name_space_list = target_list[:]
        # 再次获取目标类，对于fuzzer来说，就是call本身所用的类，要分清楚，函数的筛选和fuzzer的构建是不一样的。
        # 同时区分fuzzer 自定义的类，将fuzzer自定义的类的父类作为label1的类
        for one_call in fuzzer.call_list:
            if len(one_call.name_space_list) > 0:
                for call_name in one_call.name_space_list:
                    if call_name in all_class_dict and all_class_dict[call_name].is_fuzzer_class:
                        for base_class_name in all_class_dict[call_name].base_class_name_list:
                            if base_class_name in all_class_dict:
                                if not all_class_dict[base_class_name].is_fuzzer_class:
                                    call_class_set.add(base_class_name)
                                    break
                    else:
                        call_class_set.add(call_name)

        # 最后class分配的时候，对于fuzzer自定义的类，主要是找到其父类作为label1的类，否则不作为label1的类
        
        for class_name in all_class_dict:
            if class_name in call_class_set:
                if not all_class_dict[class_name].is_fuzzer_class:
                    fuzzer.label1_class.append(all_class_dict[class_name])
            else:
                if all_class_dict[class_name].is_fuzzer_class:
                    for base_class_name in all_class_dict[class_name].base_class_name_list:
                        if base_class_name not in call_class_set and base_class_name in all_class_dict:
                            fuzzer.label1_class.append(all_class_dict[base_class_name])
                else:
                    fuzzer.label0_class.append(all_class_dict[class_name])
        self.driver_list.append(fuzzer)
        print(f"[analyze_one_libfuzzer] {libfuzzer_full_file_name} gets {len(fuzzer.label1_list)} label 1 funs, {len(fuzzer.label0_list)} lable 0 funcs")


    def analyze_all_libfuzzer(self):
        if len(self.fuzz_file_list) == 0:
            print(f"[ERROR] no libfuzzer file")
            return
        for fuzz_file in self.fuzz_file_list:
            print(f"[Projcet] analyze_all_libfuzzer analyzing {fuzz_file}...")
            self.analyze_one_libfuzzer(fuzz_file)
        
        if len(self.driver_list) > 0:
            self.label_all_funcs()

    def label_all_funcs(self):
        all_func_set = set()
        for fuzzer in self.driver_list:
            for one_func in fuzzer.label1_list:
                if one_func.body not in all_func_set:
                    all_func_set.add(one_func.body)
                    self.label1_funcs.append(one_func)
        for one_func in self.all_funcs:
            if one_func.body not in all_func_set:
                one_func.is_driver_func = 0
                self.label0_funcs.append(one_func)
        
        


    def __run(self):
        '''
        old file
        '''
        self.parse_readme_file()
        self.__organize_folder()
        self.__analysis_fuzzer_files()
        
        if not self.is_contain_libfuzzer:
            print(f"[CXXProject] __analysis_fuzzer_files {self.project_dir} contains no libfuzzer")
            return
        self.__analysis_common_files()
        # 找到label 1的函数，获取函数的Include Path，找到label 1函数返回参数和函数参数的定义
        self.__get_label1_funcs()

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
    对于包含的第三方库，就不进行测试了。
    '''
    def __organize_folder(self):
        '''
        old file
        '''
        target_floder = {"fuzz","libfuzzer","fuzeer","fuzzing","harness","fuzz_driver"}
        fuzz_dir = ""
        for root, dirs, files in os.walk(self.project_dir):
            # print(f"当前目录: {root}")
            # 此文件夹内均是测试文件
            third_party_keywords = {"third_party", "contrib", "libs", "external", "deps", "vendors","ext"}
            if any(keyword in root for keyword in third_party_keywords):
                continue
            if root == fuzz_dir:
                for file in files:
                    if self.__is_need_file(file):
                        self.fuzz_file_list.append(os.path.join(root,file))
            else:
                for directory in dirs:
                    if directory in target_floder:
                        fuzz_dir = os.path.join(root,directory) 
                for file in files:
                    if self.__is_need_file(file):
                        self.common_file_list.append(os.path.join(root,file))

    def __analysis_fuzzer_files(self):
        '''
        old file
        '''
        self.label1_calls = []
        self.is_contain_libfuzzer = False
        for fuzz_file_path in tqdm(self.fuzz_file_list,desc=f"...{self.project_dir[-18:]} Processing fuzzer files:"):
            # print(f"Analyzing {fuzz_file_path}")
            if fuzz_file_path[-2:] in {".c",".C",".h"}:
                target_config = Config(self.config['c'],'c')
            else:
                target_config = Config(self.config['cpp'],'cpp')
            fuzz_driver = DriverFile(fuzz_file_path,target_config)
            if fuzz_driver.is_libfuzzer:
                self.is_contain_libfuzzer = True
            # 将所有的cxxfile类存储起来    
            self.all_cxxfiles.append(fuzz_driver)
            self.driver_list.append(fuzz_driver)
            self.label1_calls += fuzz_driver.call_list
        self.label1_calls = list(set(self.label1_calls))

    def __analysis_common_files(self):
        '''
        old file
        '''
        self.all_funcs = []
        for common_file_path in tqdm(self.common_file_list,desc=f"...{self.project_dir[-18:]} Processing Common files:"):
            if common_file_path[-2:] in {".c",".C",".h"}:
                target_config = Config(self.config['c'],'c')
            else:
                target_config = Config(self.config['cpp'],'cpp')
            comm_file = NormalFile(common_file_path,target_config)
            comm_file.setProjectREADME(self.readme)
            # 将所有的cxxfile类存储起来
            self.all_cxxfiles.append(comm_file)
            self.all_funcs += comm_file.func_list


    def __get_label1_funcs(self):
        '''
        old file
        '''
        self.label1_funcs = []
        self.label0_funcs = []
        for one_func in tqdm(self.all_funcs,desc=f"...{self.project_dir[-18:]} Processing funcs:"): 
            if self.__is_label1_func(one_func):
                for driver in self.driver_list:
                    for one_call in driver.call_list:
                        if one_call.func_name == one_func.name:
                            driver.func_list.append(one_func)
                            break
                one_func.is_driver_func = 1    
                one_func.get_include_file_path(self.all_cxxfiles)
                one_func.return_parm.get_origin_define(self.all_cxxfiles)
                for one_parm in one_func.parm_list:
                    one_parm.get_origin_define(self.all_cxxfiles)
                self.label1_funcs.append(one_func)
            else:
                one_func.get_include_file_path(self.all_cxxfiles)
                one_func.return_parm.get_origin_define(self.all_cxxfiles)
                for one_parm in one_func.parm_list:
                    one_parm.get_origin_define(self.all_cxxfiles)
                self.label0_funcs.append(one_func)
    # 暂定用函数名相同确定目标函数
    def __is_label1_func(self,one_func):
        '''
        old file
        '''
        for one_call in self.label1_calls:
            if one_call.func_name == one_func.name:
                return True
        return False

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
        # self.__dectect_file_encoding()
        try:
            # with open(self.file_path,"r", encoding=self.encoding) as f:
            #     self.code = f.read()
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
Driver类主要是维护fuzz driver文件中所调用的所有函数
'''
class DriverFile(CXXFile):
    def __init__(self, file_path, config) -> None:
        super().__init__(file_path, config)
        self.func_list = []
        self.related_files = set()
        self.label1_class = []
        self.label0_class = []
        self.label0_list = []
        self.label1_list = []
        self.cop_fuzz_list = []
        self.__is_libfuzzer()

        self.is_get_all_call_ran = False
        self.is_get_related_fuzzer_ran = False


    def __is_libfuzzer(self):
        self.is_libfuzzer = False
        for node in self.ele_list:
            if node.type == "function_definition":
                tmp_func = func(node)
                if tmp_func.name == b"LLVMFuzzerTestOneInput":
                    self.is_libfuzzer = True
    
        # print(f"{self.file_path} {self.is_libfuzzer} is libfuzzer")

    def get_all_call(self):
        if self.is_get_all_call_ran:
            return
        self.call_list = []
        for node in self.ele_list:
            if "call_expression" in node.type:
                tmp_caller = caller(node)
                tmp_caller.find_declaration(self.ele_list)
                self.call_list.append(tmp_caller)
        self.is_get_all_call_ran = True

    def set_related_files(self,related_files):
        self.related_files = related_files
    '''
    fuzz list是 NormalFile的list
    '''
    def get_related_fuzzer(self):
        if self.is_get_related_fuzzer_ran:
            return
        if len(self.cop_fuzz_list) == 0:
            return
        for one_file in self.cop_fuzz_list:
            for node in one_file.ele_list:
                if "call_expression" in node.type:
                    tmp_caller = caller(node)
                    tmp_caller.find_declaration(one_file.ele_list)
                    self.call_list.append(tmp_caller)
        self.is_get_related_fuzzer_ran = True

    def showALLCaller(self):
        for call_node in self.call_list:
            if call_node.call_type == "field_expression":
        # call_node.find_declaration(all_nodes)
                print(f"[CALLER] {call_node.call_type} -- {call_node.func_name} -- {call_node.name_space_list}  -- {call_node.variable}")
            elif call_node.call_type == "identifier":
                print(f"[CALLER] {call_node.call_type} -- {call_node.func_name}")
            elif call_node.call_type == "qualified_identifier":
                print(f"[CALLER] {call_node.call_type} -- {call_node.func_name} -- {call_node.name_space_list}")



'''
正常文件
'''
class NormalFile(CXXFile):
    def __init__(self, file_path, config) -> None:
        super().__init__(file_path, config)
        
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

    def __repr__(self) -> str:
        return f"{self.type} {self.name}"
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