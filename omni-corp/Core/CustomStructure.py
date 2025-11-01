import os
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
from  Core.CustomAlgorithm import *
from Core.APIWarp import *
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
            elif node.type == "destructor_name":
                self.func_name = ""
                return
            for child in node.children:
                if child.type not in {"argument_list","template_argument_list","parameter_list"}:
                    stack.append(child)
        self.name_space_list =self.name_space_list[::-1]
        try:
            self.func_name = self.name_space_list[-1]
        except:
            print(self.node.text)
            show_all_node(self.node)
            print(f"exit caller __process_field_expression")
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
    def __hash__(self) -> int:
        return hash(self.name)
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} : {self.class_list}"
        else:
            return ""
    def __repr__(self) -> str:
        return self.__str__()
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
        self.summary = ""
        self.call_list = []
        self.is_get_namespace_ran = False
        self.is_get_include_file_path_ran = False
        self.type = None
        self.input_parm_set = None
        self.output_parm_set = None
        self.init_parm_set = None
        self.init_return_set = None
        self.sign = None
        self.apidoc = None
        self.init()
    def is_func_analyzed(self):
        if self.input_parm_set is None:
            return False
        if self.output_parm_set is None:
            return False
        if self.init_parm_set is None:
            return False
        if self.init_return_set is None:
            return False
        return True
        
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
            print("exit func init")
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
        suffix = os.path.splitext(base_name)[1]
        if ".h" in suffix:
            self.include_file_path = self.contain_file_path
            self.is_get_include_file_path_ran = True
            return
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

    def remove_comments(self,code):#从代码中移除所有注释
        tree = self.parser.parse(code)#使用 tree-sitter 解析器将代码解析为语法树。
        root_node = tree.root_node
        ele_list = iterate_tree(root_node)#树的深度优先遍历，并将所有节点按遍历顺序存储在一个列表中返回
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
        self.call_list = []
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
            elif node.type == "type_definition":
                for child in node.children:
                    if child.type == "struct_specifier":
                        tmp_struct = classstruct(node)
                        self.classstruct_list.append(tmp_struct)

                
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
    def __hash__(self):
        return hash(self.body)
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
        elif self.node.type == "type_definition":
            for child in self.node.children:
                if child.type == "struct_specifier":
                    self.type = "struct"
                elif child.type == "type_identifier":
                    self.name = child.text
                
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