
import os

'''
各种分析算法
'''

def get_code_from_content(content):
    code = content.split('```c')[-1]
    code = code.split('```')[0]
    return code
def get_file_front_line_content(file_name,line_num):
    with open(file_name,'r') as f:
        content = f.read()
        lines = content.splitlines()
        new_string = "\n".join(lines[:line_num])
    return new_string
def TS_check_pointer_const(one_func,pointer_name):
    import tree_sitter_c as tsc
    from tree_sitter import Language, Parser
    C_LANGUAGE = Language(tsc.language())
    parser = Parser(C_LANGUAGE)
    tree = parser.parse(one_func.body)
    root_node = tree.root_node
    delcartor_node = next((node for node in iterate_tree(root_node) if node.type == "function_declarator"), None)
    parameter_list_node = next((node for node in iterate_tree(delcartor_node) if node.type == "parameter_list"), None)
    parameter_nodes = [node for node in iterate_tree(parameter_list_node) if node.type == "parameter_declaration"]
    # 遍历每个节点
    for parameter_node in parameter_nodes:
        ele_list = iterate_tree(parameter_node)
        target_node = next( (node for node in ele_list if bytearray2str(node.text) == pointer_name),None)
        if target_node is None:
            continue
        if any(node.text == b"const" for node in ele_list):
            return True
    return False

   
def TS_check_memroy_pointer(one_func,pointer_name):
    import tree_sitter_c as tsc
    from tree_sitter import Language, Parser
    C_LANGUAGE = Language(tsc.language())
    parser = Parser(C_LANGUAGE)
    tree = parser.parse(one_func.body)
    root_node = tree.root_node
    delcartor_node = next((node for node in iterate_tree(root_node) if node.type == "function_declarator"), None)
    parameter_list_node = next((node for node in iterate_tree(delcartor_node) if node.type == "parameter_list"), None)
    parameter_nodes = [node for node in iterate_tree(parameter_list_node) if node.type == "parameter_declaration"]
    # 遍历每个节点
    for parameter_node in parameter_nodes:
        ele_list = iterate_tree(parameter_node)
        target_node = next( (node for node in ele_list if bytearray2str(node.text) == pointer_name),None)
        if target_node is None:
            continue
        # 浮点数直接不算
        if any(node.text == b'float' for node in ele_list):
            return False
        # 出现类似于结构体的变量，直接用llm判断
        if any(node.type == "type_identifier" for node in ele_list):
            return "struct"
        # 如果是字符串，需要进一步判断
        if any(node.text == b'char' for node in ele_list):
            return "char"
        return True
    return False

'''
遍历node,返回list，以后所有都在这个list基础上进行分析
'''
# def traverse_all_node(node, return_list):
#     if node is None:
#         return
#     if not isinstance(return_list, list):
#         raise TypeError("return_list should be a list")
    
#     return_list.append(node)
#     for child in node.children:
#         traverse_all_node(child, return_list)
def remove_comments(root_node):
    ele_list = iterate_tree(root_node)
    to_remove = []
    for node in ele_list:
        if node.type == "comment":
            to_remove.append(node.text)
    removed_code = root_node.text
    for comment in to_remove:
        removed_code = removed_code.replace(comment,b'')
    return removed_code


def bytearray2str(target_str):
    if type(target_str) == type('123'):
        return target_str
    else:
        return target_str.decode('utf-8',errors='ignore')



def is_libfuzzer(full_file_path):
    with open(full_file_path,'rb') as f:
        code = f.read()
    if b"LLVMFuzzerTestOneInput" in code:
        return True
    else:
        return False

def iterate_tree(root_node):
    stack = [root_node]
    return_list = []
    while stack:
        node = stack.pop()
        return_list.append(node)
        # 在这里处理节点的逻辑，比如打印节点的类型、内容等
        # print("Node Type:", node.type)
        # print("Node Content:", node.utf8_content)
        # 将子节点添加到堆栈中，以便迭代处理
        for child in node.children:
            stack.append(child)
    return return_list

'''
展示一个Node下的构架
'''
def show_all_node(node,depth=0):
    print("\t"*depth,node.type,"--",node.text)
    for child in node.children:
        show_all_node(child, depth+1)

'''
将路径分割为list
'''
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

'''
找到所有函数调用
'''

def get_all_call(ele_list):
    return_list = []
    for node in ele_list:
        if "call_expression" in node.type:
            return_list.append(node)
    return return_list


'''
找到所有field_expression
'''
def get_all_field_expression(ele_list):
    return_list = []
    for node in ele_list:
        if "field_expression" in node.type:
            return_list.append(node)
    return return_list


'''
找到所有identifier
'''
def get_all_identifier(ele_list):
    return_list = []
    for node in ele_list:
        if "identifier" in node.type:
            return_list.append(node)
    return return_list


'''
找到包含节点，好好考虑一下吧。
'''

def get_contain(ele,node_list):
    # return_list = []
    for node in node_list:
        if ele.text in node.text:
            return node
    return None        
def is_contain(ele,node_list):
    for node in node_list:
        if ele.text in node.text:
            return True
    return False

def get_contain_nodes(lista,listb):
    return_list = []
    for node in lista:
        father_node = get_contain(node,listb)
        if father_node is not None:
            return_list.append((node,father_node))
    return return_list

'''
找到所有声明
'''
def get_all_declaration(ele_list):
    return_list = []
    for node in ele_list:
        if "declaration" in node.type:
            return_list.append(node)
    return return_list

'''
分析filed_expreesion
'''
def analysis_field_expression(node):
    print(f"{node.type} - {node.text}")
    for child in node.children:
        analysis_field_expression(child)
    
'''
分析qualified_identifier

qualified_identifier节点下的子节点中，有些是type_identifier（类型标识符），有些是identifier（标识符）。这两者的区别在于标识符的含义不同：
type_identifier（类型标识符）：用于表示在代码中被用作类型的标识符，比如类名、结构体名等。在很多编程语言中，类型标识符通常是大写字母开头的，或者遵循某种特定的命名规范。
identifier（标识符）：表示在代码中用作普通标识符的标识符，比如变量名、函数名等。这些标识符可以是小写字母开头的，通常不作为类型名。

因此，qualified_identifier节点下的子节点中，如果是type_identifier，则表示这是一个被限定的类型名；如果是identifier，则表示这是一个被限定的普通标识符，可能是变量名、函数名等。
'''
def iter_qualified_identifier(root_node):
    if root_node.type != "qualified_identifier":
        print(f"iter_qualified_identifier {root_node.type} {root_node.text} is not qualified_identifier")
        return None
    stack = [root_node]
    return_list = []
    while stack:
        node = stack.pop()
        return_list.append(node)
        # 在这里处理节点的逻辑，比如打印节点的类型、内容等
        # print("Node Type:", node.type)
        # print("Node Content:", node.utf8_content)
        # 将子节点添加到堆栈中，以便迭代处理
        for child in node.children:
            if child.type not in {"argument_list","template_argument_list","parameter_list"}:
                stack.append(child)
    return return_list

def qualified_identifier_get_namespace(node):
    if node.type != "qualified_identifier":
        print(f"{node.type} {node.text} is not qualified_identifier")
        return None
    ele_list = []
    # traverse_all_node(node, ele_list)
    ele_list = iter_qualified_identifier(node)
    return_list = []
    in_argument = False
    arg_count = 0
    for c in ele_list:
        # 必须严格将argument_list的内容完全排除
        if in_argument:
            if c.type == "(":
                arg_count +=1
            elif c.type == ")":
                arg_count -=1
                if arg_count == 0:
                    in_argument = False
        else:
            if c.type == "namespace_identifier":
                return_list.append(c.text)
            elif c.type == "type_identifier":
                return_list.append(c.text)
            elif c.type == "identifier":
                return_list.append(c.text)
            elif c.type == "template_function":
                return_list.append(template_function_get_identifier(c))
            elif c.type == "operator_name":
                # 如果是operator,那就没必要进行后面的分析了
                return_list = []
                return []
            elif c.type in {"argument_list","template_argument_list","parameter_list"}:
                in_argument = True
    return return_list[::-1]



'''
提取源码中的参数定义
'''
def get_declaration(ele_list):
    return_list = []
    for node in ele_list:
        if "declaration"==node.type:
            return_list.append(node)
    return return_list


def declaration_get_identifier(node):
    # ele_list = []
    # traverse_all_node(node, ele_list)
    stack = [node]
    while stack:
        node = stack.pop()
        if node.type == "identifier":
            return node.text
        for child in node.children:
            if child.type not in {"argument_list","template_argument_list","parameter_list","call_expression","field_expression"}:
                stack.append(child)

def declaration_get_namespacelist(node):
    # ele_list = []
    # traverse_all_node(node, ele_list)
    if not node:
        return []
    return_list  = []
    target_node = None
    for child in node.children:
        if child.type == "qualified_identifier":
            target_node = child
        elif child.type == "type_identifier":
            return [child.text]
        elif child.type == "template_type":
            for cc in child.children:
                if cc.type == "type_identifier":
                    return [cc.text]
    if not target_node:
        return []

    ele_list = iterate_tree(target_node)
    
    for c in ele_list:
        if "type_identifier" == c.type:
            return_list.append(c.text)
        elif "namespace_identifier" == c.type:
            return_list.append(c.text)
    return_list.reverse()
    return return_list


'''
function_definition函数定义提取所在类
'''
def function_declarator_get_namespaces(node):
    if node.type != "function_declarator":
        print(f"ERROR function_declarator_get_namespaces {node.type} is not function_declarator")
        return []
    for c in node.children:
        if c.type == "qualified_identifier":
            return qualified_identifier_get_namespace(c)
        elif c.type == "identifier":
            return [c.text]
        elif c.type == "field_identifier":
            return [c.text]
        elif c.type == "parameter_list":
            # 对于操作符和析构函数，直接忽略，因为他们不可能是libfuzzer目标函数
            return []
    return []

def parameter_declaration_get_node(node):
    if node.type != "parameter_declaration":
        print(f"ERROR parameter_declaration_get_node {node.type} is not parameter_declaration")
        os._exit(0)
    target_type = { "qualified_identifier","type_identifier","primitive_type","sized_type_specifier","template_type","dependent_type","enum_specifier","union_specifier","struct_specifier","class_specifier","placeholder_type_specifier","decltype","placeholder_type_specifier","macro_type_specifier"}
    for c in node.children:
        if c.type in target_type:
            return c

    print(f"[ERROR] parameter_declaration_get_node {node.text} can not be analyze")
    show_all_node(node)
    os._exit(0)

def function_declarator_get_parm_list(node):
    if node.type != "function_declarator":
        print(f"ERROR  function_declarator_get_parm_list {node.type} is not function_declarator")
        return []
    return_list = []
    for c in node.children:
        if c.type ==  "parameter_list":
            for cc in c.children:
                if cc.type == "parameter_declaration":
                    return_list.append(parameter_declaration_get_node(cc))
    return return_list
        

def function_definition_get_namespaces(node):
    if node.type != "function_definition":
        print(f"ERROR {node.type} is not function_definition")
        return []
    # print(f"processing {node.text}")
    body = node.text
    body_head = body.split(b"{")[0]
    ele_list = []
    stack = [node]
    while stack:
        tmp_node = stack.pop()
        ele_list.append(tmp_node)
        for child in tmp_node.children:
            if child.type != "compound_statement":
                stack.append(child)
    for c in ele_list:
        if c.type == "function_declarator":
            if c.text in body_head:
                return function_declarator_get_namespaces(c)
    return []
    # for c in node.children:
    #     # class,struct和operator暂时不处理
    #     if c.type in {"class_specifier","struct_specifier","operator_cast"}:
    #         return []

    # ele_list = []
    # stack = [node]
    # while stack:
    #     tmp_node = stack.pop()
    #     ele_list.append(tmp_node)
    #     for child in tmp_node.children:
    #         if child.type != "compound_statement":
    #             stack.append(child)
    # for c in ele_list:
    #     if c.type == "function_declarator":
    #         # print(f"get {c.text}")
    #         # print("="*60)
    #         return function_declarator_get_namespaces(c)
    # return []

def function_definition_get_parm_list(node):
    if node.type != "function_definition":
        print(f"ERROR {node.type} is not function_definition")
        return []
    for c in node.children:
        # class,struct和operator暂时不处理
        # 删除了ERROR
        if c.type in {"class_specifier","struct_specifier","operator_cast"}:
            return []
    # ele_list = []
    # traverse_all_node(node, ele_list)
    ele_list = iterate_tree(node)
    for c in ele_list:
        if c.type == "function_declarator":
            return function_declarator_get_parm_list(c)
    return []
        
def function_definition_get_return_type(node):
    if node.type != "function_definition":
        print(f"ERROR {node.type} is not function_definition")
        return []
    body = node.text
    body_head = body.split(b"{")[0]

    for c in node.children:
        if c.text not in body_head:
            continue
        if c.type == "qualified_identifier":
            return qualified_identifier_get_namespace(c)
        elif c.type == "struct_specifier":
            return [c.text]
    return []

def function_definition_get_return_node(node):
    if node.type != "function_definition":
        print(f"ERROR function_definition_get_return_node {node.type} is not function_definition")
        os._exit(0)
    body = node.text
    body_head = body.split(b"{")[0]
    for c in node.children:
        if c.text not in body_head:
            continue
        if c.type == "qualified_identifier":
            return c
        elif c.type == "type_identifier":
            return c
        elif c.type == "primitive_type":
            return c
        elif c.type == "struct_specifier":
            return c
    return None



def specifier_get_identifier(node):
    if "specifier" not in node.type:
        print(f"[ERROR] {node.type} is not specifier")
        return  ""
    for c in node.children:
        if c.type in {"type_identifier","identifier"}:
            return c.text
    return ""

def template_function_get_identifier(node):
    if node.type != "template_function":
        print(f"[ERROR] {node.type} is not template_function")
        return  ""
    for c in node.children:
        if c.type == "identifier":
            return c.text
    return ""

def is_contain_class_or_struct(node):
    for c in node.children:
        if c.type in {"class_specifier","struct_specifier"}:
            return True
    return False

def get_parent_till_namespace(node):
    tmp_node = node
    return_list = []
    # 不断向上找namespace定义父类，去找包含的namespace定义。
    while True:
        if tmp_node is None:
            break
        if tmp_node.type == "namespace_definition":
            for c in tmp_node.children:
                if c.type == "namespace_identifier":
                    return_list.append(c.text)
                    break
        elif tmp_node.type == "class_specifier":
            for c in tmp_node.children:
                if c.type == "type_identifier":
                    return_list.append(c.text)
                elif c.type == "identifier":
                    return_list.append(c.text)
        elif tmp_node.type == "function_definition":
            if is_contain_class_or_struct(tmp_node):
                for c in tmp_node.children:
                    if c.type == "type_identifier":
                        return_list.append(c.text)
                    elif c.type == "identifier":
                        return_list.append(c.text)
        elif tmp_node.type == "struct_specifier":
            for c in tmp_node.children:
                if c.type == "type_identifier":
                    return_list.append(c.text)
                elif c.type == "identifier":
                    return_list.append(c.text)
        elif tmp_node.type == "translation_unit":
            # over
            break
        tmp_node = tmp_node.parent
    return return_list

def get_name_node_from_root_node(node,name):
    # ele_list = []
    return_nodes = []
    # traverse_all_node(node,ele_list)
    ele_list = iterate_tree(node)
    for node in ele_list:
        if node.text == name:
            return_nodes.append(node)
    return return_nodes

def get_parent_till_variable_define(node,target_text):
    # "enum_specifier"
    tmp_node = node
    return_node = None
    while True:
        if tmp_node is None:
            break
        elif tmp_node.type == "translation_unit":
            break
        elif tmp_node.type == "enum_specifier":
            for c in tmp_node.children:
                if c.type in {"identifier","type_identifier"}:
                    if c.text == target_text:
                        return_node = tmp_node
                    break
            break
        elif tmp_node.type in {"class_specifier","struct_specifier"}:
            for c in tmp_node.children:
                if c.type in {"identifier","type_identifier"}:
                    if c.text == target_text:
                        return_node = tmp_node
                    break
            break
        elif tmp_node.type in {'type_definition'}:
            for c in tmp_node.children:
                if c.type in {"struct_specifier"}:
                    for cc in tmp_node.children:
                        if cc.type == "type_identifier" and cc.text == target_text:
                            return_node = tmp_node
                            break
                    break
            break
        elif tmp_node.type in {"parameter_list","argument_list","template_argument_list"}:
            break
        # 这个部分是因为tree-sitter解析C++代码出现错误，比如，无法正确解析class EXIV2 jpg : public(aaa) 的情况
        elif tmp_node.type == "function_definition":
            if is_contain_class_or_struct(tmp_node):
                for c in tmp_node.children:
                    if c.type in {"identifier","type_identifier"}:
                        if target_text == c.text:
                            return_node = tmp_node
                            break
                break
        tmp_node = tmp_node.parent
    return return_node






            







