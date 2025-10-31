'''
该文件主要存储各种Prompt，包含各种字符串
'''
from Core.CustomAlgorithm import *

#TODO 关于对函数参数的判断，是否需要全部先转变成函数签名，然后再转变为对函数签名的判断。
##########################################
###### 函数参数相关处理prompt #############
##########################################

def INS_parameter_memory_size():
    # 判断并给出函数是否同时存在指向内存和对应内存区域大小的输入参数，是判定函数是否是Libfuzzer目标函数重要依据。
    ins = """
下面的函数是否同时拥有下面两个参数：
1.这个参数本身指向某段被解析内存的指针，指向的区域是连续的字节序列或者连续的文本数据（不包括文件名或其他具有语义的内容），而不是路径名、文件名、结构体或者浮点数等其他特定结构数据。
2.这个参数是指向内存区域的大小的数值。
以json格式输出答案，下面是个示例：
{
    "answer":"yes" or "no",
    "pointer_name":"name of the parameter that point to the memory region",
    "size_name":"name of the parameter that stores size"
}
 """
    return ins
#下面函数的输入参数是否包含直接指向连续字节序列或文本数据的指针，而非指向文件名、结构体或浮点数等结构化数据。
def INS_parameter_memory_pointer():
    ins = """
下面的函数是否存在指向某段被解析内存的指针的输入参数，这个输入参数指向的区域是连续的字节序列或者连续的文本数据（不包括文件名或其他具有语义的内容），而不是路径名、文件名、结构体或者浮点数等其他特定结构数据。
以json格式输出答案，下面是个示例：
{
    "answer":"yes" or "no",
    "pointer_name":"name of the parameter that point to the memory region"
}
 """
    return ins

def INS_parameter_check_memory_pointer_3(pointer_name):
    ins = f"""
根据下面描述，`{pointer_name}`作为文本数据，指向的数据是下面哪一种？
A.文件名  B.路径名  C.人名  D.地名  E.无明确语义的文本数据
回答采用json格式输出，下面是输出示例:
{{
    "reason":"解释原因",
    "answer":"A"
    
}}
"""
    return ins
def INS_parameter_check_memory_pointer_2(pointer_name):
    ins = f"""
按照如下思考顺序回答问题：
逐步分析下面的函数，分析函数签名。
然后分析输入参数`{pointer_name}`，查看该参数的数据类型定义。
最后根据函数对参数`{pointer_name}`处理过程，回答问题，参数`{pointer_name}`指向的数据类型是什么？
"""
    return ins

def INS_parameter_check_memory_pointer_1(pointer_name):
    ins = f"""
根据下面描述，回答问题，`{pointer_name}`的数据类型是下面哪一种？
A.二进制数据 B. 文本数据 C.结构体 D.浮点数 E.其他 
回答采用json格式输出，下面是输出示例:
{{
    "reason":"解释原因",
    "answer":"A"    
}}
"""
    return ins

def INS_parameter_check_pointer_size(pointer_name,size):
    ins = f"""
下面函数的输入参数{size}是否表示输入参数{pointer_name}指向内存数据大小或者长度？
回答采用json格式输出，下面是输出示例:
{{
    "answer":"yes" or "no"
}}
"""
    return ins

def INS_parameter_return_value():
    # 找出函数的返回值类型
    ins = """
找出下面函数的返回值类型，直接输出返回值的类型，以json格式输出，下面是输出示例：
{
    "return_parameter_type":"函数返回值的参数类型"
}
"""
    return ins

# def INS_parameter_input_paramter_is_return():
#     # 判断函数的输入参数是否被用作函数返回值
#     ins = """
# 下面函数的指向结构体的输入参数是否存在传引用？请按照如下的思路思考并回答问题：
# 1. 检查函数的参数类型，如果函数的参数是指针类型，并且是指向结构体的指针，那么它很可能是在实现传引用的效果。
# 2. 查看函数内部是否解引用指针，解引用指针（使用*操作符）意味着函数正在通过指针修改外部变量的值。
# 3. 查看函数内部是否修改指针指向内存地址的值。
# 4. 查看函数内部是否对输入参数指针动态分配内存并返回数据给调用者。
# 回答采用json格式输出，下面是输出示例:
# {
#     "answer":"yes" or "no",
#     "variable_name":"被传引用的函数输入参数结构体变量名",
#     "variable_type":"被传引用的函数输入参数结构体的名称",
#     "reason" : "解释原因"
# }
# """
#     return ins

# def INS_parameter_struct_is_return(parm_name):
#     ins = f"""
# 下面函数是否使用函数输入参数结构体{parm_name}指向内存作为函数输出？
# 回答采用json格式输出，下面是输出示例:
# {{
#     "answer":"yes" or "no",
#     "variable_name":"当作函数输出的参数名称",
#     "reason":"解释原因"
# }}
# """
    # return ins

def INS_parameter_destory_struct():
    ins ="""
下面函数是否是资源回收类函数？
回答采用json格式，下面是输出示例：
{
    "answer": "yes" or "no",
    "destroy_parameter_type" : "被函数回收/销毁的结构体名称"
}
"""
    return ins

##########################################
######## 函数功能判断prompt ###############
##########################################

def INS_function_benchmark():
    ins = """
下面的函数是否是基准测试函数(Benchmark Functions)？
回答采用json格式输出，下面是输出示例:
{
    "answer": "yes" or "no"
}
"""
    return ins
    
def INS_function_test():
    ins = """
下面的函数是否是测试函数（Test Function）?
回答采用json格式输出，下面是输出示例:
{
    "answer": "yes" or "no"
}
"""
    return ins
def INS_function_file_op():
    # 判断函数是否存在文件读写操作
    ins = """
下面函数中是否有文件读写操作。
以下面json格式输出。
{
    "answer": "yes" or "no"
}
"""
    return ins


# def INS_function_memory_load():
#     # 判断函数是否从内存缓冲区读取数据并进行解析，是判断函数是否具有libfuzzer目标函数的功能。
#     ins ="""
# 下面函数是否从内存缓冲区读取数据，并将其改数据转换为特定的结构体数据或者对数据进行解码、编码等具有一定逻辑复杂度的操作。
# 以下面json格式输出。
# {
#     "answer": "yes" or "no",
#     "structure_name": "the name of transfered structure"
# }
# """
#     return ins

def INS_function_global_variable_write():
    ins = """
下面函数中是否存在对全局变量的读写操作，忽视可能的宏定义，忽略函数参数和函数内定义的变量，按照下面json格式输出：
{
    "answer":"yes" or "no"
    "global_variable_name":"global variable name"
}
"""
    return ins

# def INS_function_init():
#     # 判断函数是否是完成某个结构体的初始化功能
#     ins = """
# 下面函数是否是初始化函数？
# 用json格式输出，下面是json格式示例：
# {
#     "answer":"yes" or "no"
# }
# """
#     return ins

def INS_function_return_struct_init(parm_name):
    ins = f"""
Does the following function perform an initial initialization of the {parm_name} struct and return it?
Think step by step and output your think step in JSON format, with the following example output:
{{
    "think_step1":"",
    "think_step2":"",
    ...
    "reason":"explain the reason",
    "answer":"yes" or "no"

}}
"""
    return ins

def INS_function_parm_struct_init(parm_name):
    # Does the following function implement the initialization of the struct {parm_name}?
    ins = f"""
下面的函数是否包含对结构体`{parm_name}`初始化的过程？
Think step by step and output your think step in JSON format, with the following example output:
{{
    "think_step1":"",
    "think_step2":"",
    ...
    "reason":"Explain the reasoning through the processing steps of the input parameter {parm_name} struct in the function",
    "answer":"yes" or "no"
}}
"""
    return ins

# def INS_function_struct_init(parm_name):
#     # 判断函数是否对某特定数据结构完成初始化
#     ins = f"""
# Does the following function implement the initialization of the struct {parm_name}?
# Respond in JSON format, with the following example output:
# {{
#     "answer":"yes" or "no",`
#     "reason":"通过函数对输入参数{parm_name}结构体的处理过程解释原因"
# }}
# """
#     return ins

def INS_function_classify():
    ins = """
下面的代码属于哪个类别？用json格式返回：
A.功能处理  B.功能/资源初始化  C.资源回收  D.测试类  E.以上都不属于
回答采用json格式输出，下面是输出示例:
{
    "reason":"reason why select the answer",
    "answer": "A"
}
"""
    return ins

def INS_function_common():
    ins = """
通用工具类函数指的是函数复杂度不高，只实现了单一的`字符串处理`、`内存管理`、`数学计算`或者`时间处理`功能的函数。
分析下面函数功能，根据函数复杂度和功能，判断下面的函数是否是通用工具类函数？
用json格式输出，下面是json格式示例：
{
    "reason":"解释原因",
    "answer":"yes" or "no"
}
"""
    return ins
def INS_function_sign():
    ins = """
根据下面函数，按照下面要素总结分析函数签名。并按照如下markdown格式输出：

- *函数签名*

- *参数分析*

- *返回值分析*

- *功能概述*

"""
    return ins

def INS_function_parameter_sign_output(pointer_name):
    ins = f"""
根据下面的函数签名描述，如果想调用该函数，调用该函数是否需要调用者提供`{pointer_name}`指向的内存的内容？
{{
    "reason": "解释原因",
    "answer": "yes" or "no"
}}
"""
    return ins



##########################################
########### 代码生成prompt ###############
##########################################

def INS_function_api_doc():
    ins = """
分析下面函数的功能，根据函数使用场景，给出符合函数使用场景的调用该函数的代码片段。
回答要严格按照下面的markdown模板进行输出。

- *函数签名*

<!-- 简要介绍该函数的函数签名 -->

- *函数功能*

<!-- 尽可能简要的介绍函数的功能 -->

- *应用场景*

<!-- 尽可能简要的介绍函数的使用场景 -->

- *示例代码*

```c
<!-- 请给出调用该函数的示例代码，注意示例代码要尽可能的简洁 -->
```

"""
    return ins
def INS_generate_no_parm_funcs(func_list):
    func_name_str = ""
    func_api_doc = ""
    for i,one_func in enumerate(func_list[:-1]):
        func_name_str += f"`{bytearray2str(one_func.name)}`,"
        func_api_doc += f"## 函数{i+1} {bytearray2str(one_func.name)}\n"
        func_api_doc += one_func.api_doc + "\n\n"
        
    func_name_str += f"`{bytearray2str(func_list[-1].name)}`"
    func_api_doc += f"## 函数{len(func_list)} {bytearray2str(func_list[-1].name)}\n"
    func_api_doc += func_list[-1].api_doc
    
    ins = f"""
下面列出了{len(func_list)}个函数的功能和调用片段，根据函数使用场景，写出符合{len(func_list)}个函数{func_name_str}调用场景的同时调用{len(func_list)}个函数的示例代码。
回答要尽可能精准和简洁，代码要尽可能的优化且要符合函数功能的逻辑调用关系。
注意：必须确保每个函数{func_name_str}都必须被显示的调用，最后要解释{func_name_str}都是如何被调用的。
生成完毕后，检查生成的代码，检查{func_name_str}函数是否都被显示的调用了，如果没有，则重新生成代码。
注意：1.生成的代码均是C语言代码，而不是C++的。2.代码中出现的函数和结构体均已经在别处被定义，不必补全代码实现。3.代码中出现的函数均在头文件中已经定义，不要定义这些函数。4.不要出现示例代码中没有出现的函数。

{func_api_doc}
"""
    return ins  
def INS_generate_parm_funcs(func_list,one_parm):
# 函数的顺序必须提前定好，且需要按照静态分析的情况来定。
# 当前模型基本上不支持给函数排序的功能。
    func_name_str = ""
    func_api_doc = ""
    for i,one_func in enumerate(func_list[:-1]):
        if one_func.include_file_path == "":
            include_path = one_func.include_file_path
        else:
            include_path = one_func.contain_file_path
        func_name_str += f"`{bytearray2str(one_func.name)}`,"
        func_api_doc += f"## 函数{i+1} {bytearray2str(one_func.name)} include in {include_path}\n"
        func_api_doc += one_func.api_doc + "\n\n"

    if func_list[-1].include_file_path == "":
        include_path = func_list[-1].include_file_path
    else:
        include_path = func_list[-1].contain_file_path    
    func_name_str += f"`{bytearray2str(func_list[-1].name)}`"
    func_api_doc += f"## 函数{len(func_list)} {bytearray2str(func_list[-1].name)} include in {one_func.include_file_path}\n"
    func_api_doc += func_list[-1].api_doc
    
    ins = f"""
下面列出了{len(func_list)}个函数的功能和调用片段，根据函数使用场景，以及函数在调用过程中对`{bytearray2str(one_parm.name)}`结构体处理的逻辑关系，写出符合{len(func_list)}个函数{func_name_str}调用场景的同时调用{len(func_list)}个函数的示例代码。
回答要尽可能精准和简洁，先按照正常调用这些函数的逻辑关系安排调用顺序和对应的程序结构，并输出理由，然后生成代码，代码要尽可能的优化且要符合函数功能的*逻辑调用*关系。
注意：必须确保{len(func_list)}个函数{func_name_str}都必须被显示的调用，最后要解释{func_name_str}都是如何被调用的。
生成完毕后，检查生成的代码，检查{func_name_str}函数是否都被显示的调用了，如果没有，则重新生成代码。
在生成时还需注意：1.生成的代码均是C语言代码，而不是C++的。2.代码中出现的函数和结构体均已经在别处被定义，不必补全代码实现。3.代码中出现的函数均在头文件中已经定义，不要定义这些函数。4.不要出现示例代码中没有出现的函数。
其中`{bytearray2str(one_parm.name)}`的实现如下：
```
{bytearray2str(one_parm.body)}
```

{func_api_doc}
"""
    return ins


def INS_generate_robo_code(robo_dict,parm_code):
    parm_name_list_str  = ""
    parm_list = list(robo_dict['parm_set'])
    for one_parm in parm_list[:-1]:
        parm_name_list_str += f"`{bytearray2str(one_parm.name)}`,"
    parm_name_list_str += f"`{bytearray2str(parm_list[-1].name)}`"
    content = f"## 对{parm_name_list_str}结构体处理代码片段\n{robo_dict['code']}\n"
    content += f"## 对{parm_code.output_all_parm_name_str()}结构体处理代码片段\n{parm_code.parm_code}\n"
    ins = f"""
下面两段带有描述的代码片段分别是对结构体{parm_name_list_str}和结构体{parm_code.output_all_parm_name_str()}进行处理的片段。根据下面两段代码对各个函数调用的逻辑关系，给出同时处理结构体`{parm_name_list_str}`和结构体`{bytearray2str(parm_code.parm.name)}`的代码。
回答要尽可能精准和简洁，下面代码片段中出现的函数都要进行显示的调用，代码要尽可能的优化且要符合函数功能的逻辑调用关系。
注意：生成的代码均是C语言代码，而不是C++的。不要杜撰上文没有提及的代码。

{content}
"""
    return ins


def INS_generate_api_doc(one_func,selector):
    # 主要是根据函数的输入参数对应的初始化和销毁情况进行的。
    # 初始化和销毁都采用结构体的形式存储，key是参数名，value是对应的函数列表。
    init_struct = {}
    input_struct = {}
    destory_struct = {}
    if one_func.input_parm_set:
        for one_parm in one_func.input_parm_set:
            if selector.get_init_parm_funcs(one_parm.name):
                init_struct[one_parm.name] = selector.get_init_parm_funcs(one_parm.name)
                if not init_struct[one_parm.name]:
                    input_struct[one_parm.name] = selector.get_output_parm_funcs(one_parm.name)
            if selector.get_destory_parm_funcs(one_parm.name):
                destory_struct[one_parm.name] = selector.get_destory_parm_funcs(one_parm.name)
    note_str = ""
    if len(init_struct):
        note_str = "其中,"
        for parm_name in init_struct:
            note_str += f"{bytearray2str(parm_name)}结构体的初始化由"
            for one_func in init_struct[parm_name][:-1]:
                note_str += f"`{one_func.name}`,"
            note_str += f"`{bytearray2str(init_struct[parm_name][-1].name)}`"
            note_str += "函数完成\n"
        analyzed_set = set()
        note_str += "这些函数的原型或者调用方法如下:\n"
        for parm_name in init_struct:
            for one_func in init_struct[parm_name]:
                if one_func in analyzed_set:
                    continue
                analyzed_set.add(one_func)
                if one_func in selector.init_funcs:
                    note_str += f"`{one_func.api_doc}`\n"
                else:
                    # note_str += f"```\n{one_func.api_doc}\n````\n"
                    note_str += f"{one_func.api_doc}\n"
            
    if len(input_struct):
        note_str = "其中,"
        for parm_name in input_struct:
            note_str += f"{bytearray2str(parm_name)}结构体的由"
            for one_func in init_struct[parm_name][:-1]:
                note_str += f"`{one_func.name}`,"
            note_str += f"`{bytearray2str(init_struct[parm_name][-1].name)}`"
            note_str += "函数的输出提供\n"
            
    if len(destory_struct):
        note_str += "其中,"
        for parm_name in destory_struct:
            note_str += f"{bytearray2str(parm_name)}结构体的销毁由"
            for one_func in destory_struct[parm_name][:-1]:
                note_str += f"`{one_func.name}`,"
            note_str += f"`{bytearray2str(destory_struct[parm_name][-1].name)}`"
            note_str += "函数完成\n"
        note_str += "销毁函数函数原型为："
        for parm_name in destory_struct:
            for one_func in destory_struct[parm_name]:
                note_str += f"`{one_func.api_doc}`\n"
    
    ins = f"""
请分析下面的函数，并根据函数的功能与使用场景，生成一个符合实际使用的代码片段。请注意，代码中不要包含任何宏定义，且示例代码要尽可能清晰和简洁。

{note_str}

回答要严格按照下面的json模板进行输出。

{{
   "function_sign":"函数签名",
   "functional":"简要描述函数的功能，强调它的核心作用",
   "application_scenario":"函数的应用场景",
   "invoke_scenario": "调用该函数最符合应用场景用到的程序结构，例如顺序，循环等结构",
   "example_code":"请给出调用该函数的示例代码，注意示例代码要尽可能的简洁，且能够覆盖更多的代码区域，不要出现没有提供的函数"
}}

"""
    return ins


# 分析下面数据中包含的C语言代码，理清代码逻辑，去掉代码中printf类输出函数和文件操作函数，并将宏定义用具体数值代替，最后优化代码逻辑并输出。
# 注意：1.生成的代码均是C语言代码，而不是C++的。2.代码中出现的函数均已经在别处被定义，不必补全代码实现。3.不要出现示例代码中没有出现的函数。
# 一步一步分析，给出分析步骤，最后输出优化后的代码。
def INS_generate_opt_code():
    ins = """
分析下面数据中包含的C语言代码，理清代码逻辑，去掉代码中printf类输出函数和文件操作函数，最后优化代码逻辑并输出。
注意：1.生成的代码均是C语言代码，而不是C++的。2.代码中出现的函数均已经在别处被定义，不必补全代码实现。3.不要出现示例代码中没有出现的函数。4.尽可能剔除没有必要的条件验证结构。
一步一步分析，给出分析步骤，最后输出优化后的代码。
"""
    return ins

def INS_generate_harness_code():
    ins = """
针对下面的代码，理清代码逻辑，将宏定义用具体数值代替，将下面代码转变为libfuzzer目标测试代码并输出。
注意：1.生成的代码均是C语言代码，而不是C++的。2.代码中出现的函数均已经在别处被定义，不必补全代码实现。3.不要出现示例代码中没有出现的函数。
一步一步分析，给出分析步骤，最后输出libfuzzer代码。
"""
    return ins


#################################
########对文件或者工程############
#################################

def INS_generate_readme_summary():
    ins = """
根据下面readme，用一句话总结工程的功能。总结完毕后，分析刚刚的输入是否是最简，然后再输出最简的功能描述。
以json的格式输出，下面是输出示例：
{
    "function_summary": "功能总结",
    "analyze": "分析输入是否最简，以及最简化改进方向",
    "final_output": "最简功能描述"
}
"""
    return ins

def INS_is_related_file(readme):
    ins = f"""
分析下面的源码文件文件名及其内容，判断下面的源码是否属于下面readme描述的工程中核心功能支持的部分，而不是测试或者其他代码：
{readme}
一步一步分析并以json的格式输出，下面是输出示例：
{{
    "think_step_1" : "分析第一步",
    "think_step_2" : "分析第二步",
    ...
    "reason": "分析原因",
    "answer": "yes or no"
}}
"""
    return ins

def INS_generate_header():
    ins = """
分析下面头文件内容，如果要单独写一个libfuzzer，调用下面文件内的函数，如何编写预定义以及头文件引用，才能保证编译通过？给出具体示例，只需要预定义和引用文件即可。一步一步分析，给出分析过程，最后按照如下json格式输出:

{
  "predefine": "#define XXX",
  "header": "#include XXXX"
}

"""
    return ins

##################################
#############生成反馈##############
##################################

def INS_regenerate_compile(fuzzer_code,error_message):
    ins = f"""
下面是生成的libfuzzer：
```c
{fuzzer_code}
```
上面的代码送入编译器编译时，报出如下错误：
'''
{error_message}
'''
请根据上面错误信息修改代码并以markdown格式输出正确代码。
"""
    return ins

def INS_regenerate_run(fuzzer_code,run_message):
    ins = f"""
下面是生成的libfuzzer，可以编译通过并能够运行：
```c
{fuzzer_code}
```
在运行一段时间20秒后，反馈如下：
'''
{run_message}
'''
请分析判断上面信息，判断上面的fuzz driver是否有改进的空间，如果有请给出改进后的代码（代码要能够直接通过编译并运行），如果没有，则只回复None.
如果需要改动，请按照如下的规则进行改动：
1. 代码内LLVMFuzzerTestOneInput函数参数data进行处理。
2. 尽可能减少验证逻辑，要尽可能简化放宽验证逻辑的条件。
3. 尽可能减少return的出现次数，能不return 尽量不要return。
3. 代码中的return不要出现return 1，只允许出现return 0。
4. 代码中严禁出现任何printf，fprintf等io输出类代码。
5. 要保证原代码中的函数都要在新代码中出现。
一步一步思考，输出思考过程，最后输出None或者改动后完整代码。
"""
    return ins

#################################
########种子生成############
#################################

def INS_generate_seed(parm_name,func_list):
    func_content = ""
    for one_func in func_list:
        func_content += f"```\n{bytearray2str(one_func.body)}\n```\n"
    ins = f"""
分析下面函数对参数`{parm_name}`指向内容的处理过程，给出10个`{parm_name}`指向内存内容的测试用例，以求能够达到下面输出函数最大覆盖率，用python的十六进制转义序列输出,每个用例长度不小于32。
以json格式输出：
{{
    "test_case1": "python十六进制转义序列，长度不少于32",
    "test_case2": "python十六进制转义序列，长度不少于32",
    ...
    "test_case20": "python十六进制转义序列，长度不少于32"
}}

{func_content}
"""
    return ins