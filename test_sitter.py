import os
import tree_sitter
import argparse

# 加载 C++ 语言的语法文件
LANG = tree_sitter.Language("C:/Code/tree-sitter-cpp/build/cpp.dll","cpp")



# def print_field_expression(node):
#     for c in node.children:
#         if c.type == 

def extract_qualified_identifier(node,return_list=[]):
    # print(f"{node.type} {node.text}")
    if node.type == "identifier":
        return_list += [node.text]
    elif node.type == "namespace_identifier":
        return_list += [node.text] 
    for c in node.children:
        extract_qualified_identifier(c,return_list)

def extract_declare_qualified_identifier(node,return_list=[]):
    if node.type == "type_identifier":
        return_list += [node.text]
    elif node.type == "namespace_identifier":
        return_list += [node.text] 
    for c in node.children:
        extract_declare_qualified_identifier(c,return_list)


def extract_field_expression(node,return_list=[]):
    if node.type == "identifier":
        return_list += [node.text]
    elif node.type == "field_identifier":
        return_list += [node.text]
    for c in node.children:
        extract_field_expression(c,return_list)



def print_call_expression(node,func_dict={}):
    for c in node.children:
        print(f"{c.type} {c.text}")
        if c.type == "field_expression":
            func_list = []
            extract_field_expression(c,func_list)
            func_dict[func_list[-1]] = func_list[:-1]
            # print(f"func list is {func_list}")
        elif c.type == "qualified_identifier":
            func_list = []
            extract_qualified_identifier(c,func_list)
            func_dict[func_list[-1]] = func_list[:-1]
            # print(f"func_list is {func_list}")
            # for cc in c.children:
            #     print(f"\t{cc.type} {cc.text}")
        elif c.type == "identifier":
            # print(f"func is {c.text}")
            func_dict[c.text] = []
    print("="*20)


def print_all_declaration(node,return_dict = {}):
    id_name = ""
    class_list = []
    for c in node.children:
        print(f"{c.type} {c.text}")
        if c.type == "init_declarator":
            # id_name = c.child_by_field_name("identifier").text
            for cc in c.children:
                if cc.type == "identifier":
                    id_name = cc.text
                # print(f"\t{cc.type} {cc.text}")
        elif c.type == "function_declarator":
            # id_name = c.child_by_field_name("identifier").text
            for cc in c.children:
                if cc.type == "identifier":
                    id_name = cc.text
        elif c.type == "qualified_identifier":
            extract_declare_qualified_identifier(c,class_list)
            print(class_list)
        elif c.type == "primitive_type":
            class_list = [c.text]
        elif c.type == "identifier":
            id_name = c.text
        
    return_dict[id_name] = class_list
    print("="*60)

'''{}

qualified_identifier 表示一个由多个标识符组成的限定符，比如例如：std::vector<int> v; // 函数名为 vector，限定符为 std

identifier 表示函数调用表达式，它由两部分组成：函数名和参数列表。比如foo(); // 函数名为 foo

field_expression表示调用函数是一个结构体或者类的调用
field_identifier 表示一个字段的标识符。它通常用于表示结构体、联合体、枚举类型等数据类型中的字段名。

'''
def traverse_declare_call(node,declare_dict={},func_dict={}):
    if node.type == "declaration":
        print_all_declaration(node,declare_dict)
    elif node.type == "call_expression":
        print_call_expression(node,func_dict)
    # if "identifier" in node.type:
    #     print('  ' * depth + node.type + "---"+str(node.text))
    # else:
    #     print('  ' * depth + node.type)
    # if node.type == "call_expression":
    #     print_call_expression(node)
    for child in node.children:
        traverse_declare_call(child,declare_dict,func_dict)

def show_declaration_list(node):
    for c in node.children:
        if c.type == "function_definition":
            print(f"{c.type}<><><>{c.text}")
            print("="*30)



def print_all_nodes(node,depth=0):
    if len(node.children) == 0 and node.type != "comment":
        print("\t"*depth,node.type,node.text)
    elif node.type != "comment":
        print("\t"*depth,node.type)
    # if "namespace_definition" in node.type:
    #     print(f"{node.type} {node.text}")
        # show_declaration_list(node)
        # print('  ' * depth + node.type + "---"+str(node.text))
    # else:
    #     print('  ' * depth + node.type)
    # print('  ' * depth + node.type + "---"+str(node.text))
    for child in node.children:
        print_all_nodes(child,depth+1)


def traverse_function_definition(node,func_list=[]):
    if node.type == "function_declarator":
        for c in node.children:
            # print(f"{c.type} {c.text}")
            if c.type == "qualified_identifier":
                extract_qualified_identifier(c,func_list)
            elif c.type == "identifier":
                if len(func_list) == 0:
                    func_list = [c.text]
    for c in node.children:
        traverse_function_definition(c,func_list)

def traverse_func_define(node,func_dict={}):
    if node.type == "function_definition":
        func_list = []
        traverse_function_definition(node,func_list)
        print(func_list)
        # for c in node.children:
        #     print(f"{c.type} {c.text}")
        #     if c.type == "function_declarator":
        #         for cc in c.children:
        #             print(f"\t{cc.type} {cc.text}")
        #     elif c.type == "reference_declarator":
        #         for cc in c.children:
        #             if cc.type == "function_declarator":
        #                 #TODO
        #                 pass
        #             print(f"\t{cc.type} {cc.text}")
        #     elif c.type == "pointer_declarator":
        #         for cc in c.children:
        #             if cc.type == "function_declarator":
        #                 #TODO
        #                 pass
        #             print(f"\t{cc.type} {cc.text}")
        print("="*20)
    for child in node.children:
        traverse_func_define(child,func_dict)



def get_cpp_file(file_path:str):
    with open(file_path, 'r') as f:
        code = f.read()

    # 初始化 tree-sitter parser 并解析代码
    parser = tree_sitter.Parser()
    parser.set_language(LANG)
    tree = parser.parse(bytes(code, 'utf8'))

    root_node = tree.root_node
    func_dict = {}
    traverse_func_define(root_node,func_dict)


def deal_with_namespace(node):
    print(node.text)

def traverse_class_define(node,func_dict):
    if node.type == "namespace_definition":
        deal_with_namespace(node)
        print("\n"*5)
    elif node.type == "":
        pass
    for c in node.children:
        traverse_class_define(c,func_dict)
        

    
def get_raw_class(file_path:str):
    with open(file_path, 'r') as f:
        code = f.read()

    # 初始化 tree-sitter parser 并解析代码
    parser = tree_sitter.Parser()
    parser.set_language(LANG)
    tree = parser.parse(bytes(code, 'utf8'))
    root_node = tree.root_node
    func_dict = {}
    # 针对嵌套式的结构，不同节点所属类/命名空间的判别方法
    # 先获取类/命名空间本身，建立相关结构体，将命名和text段都保存起来
    # 后续的类或者函数，通过text判断所属关系。
    traverse_class_define(root_node,func_dict)


def get_fuzzer_file(file_path: str):
    with open(file_path, 'r') as f:
        code = f.read()

    # 初始化 tree-sitter parser 并解析代码
    parser = tree_sitter.Parser()
    parser.set_language(LANG)
    tree = parser.parse(bytes(code, 'utf8'))

    root_node = tree.root_node
    declare_dict = {}
    func_dict = {}
    traverse_declare_call(root_node,declare_dict,func_dict)
    print(f"declare dict is {declare_dict}")
    print("="*20)
    print(f"func dict {func_dict}")
    print("="*20)
    target_find_dict = {}
    for func_name in func_dict:
        target_find_dict[func_name] = []
        for declare_name in func_dict[func_name]:
            if declare_name in declare_dict:
                for declare_class in declare_dict[declare_name]:
                    target_find_dict[func_name].append(declare_class)
            else:
                target_find_dict[func_name].append(declare_name)
                
    print(f"find name {target_find_dict}") 
    return target_find_dict


def parse_file(file_path: str):
    with open(file_path, 'r') as f:
        code = f.read()

    # 初始化 tree-sitter parser 并解析代码
    parser = tree_sitter.Parser()
    parser.set_language(LANG)
    tree = parser.parse(bytes(code, 'utf8'))

    root_node = tree.root_node

    print_all_nodes(root_node)

        
    os._exit(0)

# 遍历语法树节点
    for node in root_node.children:
        # 进行相应的分析操作，如获取变量、函数等信息
        print(f"Type:{node.type}, ID:{node.id}")
        methods = dir(node)
        for method in methods:
            print("\t",method)
        os._exit(0)
        if node.type == 'namespace_definition':
            for child_node in node.children:
                print(f"\tType:{child_node.type}")
                if child_node.type == "namespace":
                    print(f"\t\t{child_node.text}")
                elif child_node.type == "namespace_identifier":
                    print(f"\t\t{child_node.text}")
                elif child_node.type == "declaration_list":
                    for dc in child_node.children:
                        print(f"\t\tType:{dc.type}")
                        if dc.type == "function_definition":
                            # print(f"\t\t{dc.text}")
                            for c in dc.children:
                                print(f"\t\t\tType: {c.type} {c.text}")
            # function_name = code[node.start_byte:node.end_byte]
            # print('NAME SPACE:', function_name)


source_file = "C:/Code/exiv2/src/image.cpp"
source_file = "C:/Code/exiv2/src/exif.cpp"
source_file = "C:/Code/exiv2/include/exiv2/image.hpp"
# source_file = "C:/Code/exiv2/fuzz/fuzz-read-print-write.cpp"
# parse_file(source_file)
get_raw_class(source_file)
# get_cpp_file(source_file)
# get_fuzzer_file(source_file)
