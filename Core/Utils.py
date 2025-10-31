from Core.CustomAlgorithm import *
from Core.CustomStructure import *
from Core.APIWarp import *
from Core.api import *
import networkx as nx
import json



SelectorInstruction = '''
Which function below is suitable to serve as the target test function for libfuzzer? You can choose multiple functions, output the function in JSON format and output none if no function is suitable. The following is an example of output:
{
    "target":["function name" or "None"]
}
'''

'''
请选择以下哪些函数适合作为 libfuzzer 的目标测试函数。适合的函数应当具有以下特征：能够处理大量输入、具有复杂的逻辑路径、以及在处理不同输入时表现出不同的行为。请以 JSON 格式输出结果。如果没有任何函数适合，请输出 "None"。格式示例如下：
{
    "target": ["function1", "function2", ..., "None"]
}
'''

GeneratorInstruction_c = "The following codes belong to a *C* project, base on the functions listed below and their descriptions, write a libfuzzer to test as many of the following codes as possible."

GeneratorInstruction_cpp = "The following code belong to a *C++* project, base on the classes and functions listed below and their descriptions, write a libfuzzer to test as many of the following codes as possible."


ClassInstruction = '''
Identify which of the following classes/functions should be included in several libfuzzer tests, focusing only on the defined functions and not on the functions they call. Output the results in JSON format. Below is an example output.
{
    "libfuzzer1":["function1","function2"],
    "libfuzzer2":["function1","function3","function5"],
    ...
}
'''
SummaryInstruction = '''
Summarize the function below using the standard for generating libfuzzer, with the goal of creating a concise summary that allows for accurate generation of a libfuzzer based solely on the summary.
The following is an example answer, you should answer like the following:
[The function qoi_decode decodes a QOI (Quite OK Image) format image into raw pixel data. It takes four parameters:
data: A pointer to the input QOI image data.
size: The size of the input data in bytes.
desc: A pointer to a qoi_desc structure that will be filled with image metadata.
channels: The desired number of channels in the output image (0, 3, or 4). If 0, the channel count from the QOI header is used.
The function performs the following steps:
Input Validation: Checks if data or desc is NULL, if channels is invalid, or if the input size is too small to contain the QOI header and padding.
Header Parsing: Reads and validates the QOI header, extracting image width, height, channels, and colorspace into the desc structure.
Memory Allocation: Allocates memory for the output pixel array based on the image dimensions and the specified or parsed number of channels.
Initialization: Initializes the pixel array and a color index array.
Decoding Loop: Iterates through the QOI data, decoding pixel chunks according to the QOI specification:
Handles different chunk types (QOI_OP_RGB, QOI_OP_RGBA, QOI_OP_INDEX, QOI_OP_DIFF, QOI_OP_LUMA, QOI_OP_RUN).
Updates the current pixel color based on the chunk type.
Stores the decoded pixel color in the output array and updates the color index array.
Return: Returns a pointer to the decoded pixel array or NULL if any error occurs.
Key Operations to Test:
Validate header integrity (magic number, dimensions, channels, and colorspace).
Decode different QOI operations (RGB, RGBA, index, diff, luma, run).
Handle various edge cases (invalid data, insufficient buffer size, etc.).
This summary covers the essential aspects of the function needed to generate a libfuzzer that will test for various inputs and edge cases in the QOI decoding process.]

'''

ClassifyInstruction = '''下面的代码属于哪个类别？用json格式返回：
A.功能处理  B.功能/资源初始化  C.资源回收  D.测试类  E.以上都不属于
回答样本:
{
    "answer": "A",
    "reason":"reason why select the answer"
}
'''
def find_func_by_call(func_list:list,one_call:caller):
    for one_func in func_list:
        if one_call.func_name == one_func.name:
            if not one_func.class_list and not one_call.name_space_list:
                return one_func
            elif one_func.class_list and one_call.name_space_list:
                if one_func.class_list[0] == one_call.name_space_list[0]:
                    return one_func
    return None

def construct_graph(func_list):
    '''
    将所有的函数都作为节点放到图中
    '''
    G = nx.DiGraph()
    for one_func in func_list:
        if bytearray2str(one_func.name) in {"main","LLVMFuzzerTestOneInput"}:#将输入转化为字符串
            continue
        G.add_node(one_func)
        if not one_func.call_list:
            continue
        for one_call in one_func.call_list:
            tmp_func = find_func_by_call(func_list,one_call)
            if not tmp_func:
                continue
            G.add_edge(one_func,tmp_func)
    return G


def get_str_token_num(tokenizer,prompt_str):
    model_inputs = tokenizer(prompt_str)
    return len(model_inputs['input_ids'])


def construct_select_prompt_str(func_list,USE_MODEL_TYPE):
    question = {}
    readme = func_list[0].readme
    if readme:
        selector_instruction_str = f"Based on the overall requirements provided below\n{readme}\n{SelectorInstruction}\n"
    else:
        selector_instruction_str = SelectorInstruction
        
    question['Instruction'] = selector_instruction_str
    # print(SelectorInstruction)
    question['Input'] = construct_select_input_str(func_list)
    selection_prompt = Prompt(USE_MODEL_TYPE)
    prompt_str = selection_prompt.gen_prompt(question)
    return prompt_str

def construct_select_input_str(func_list):
    content = ""
    for one_func in func_list:
        content += '\n\'\'\'\n' + bytearray2str(one_func.body)+ '\n\'\'\'\n' 
    return content

def construct_select_answer_str(func_list):
    label1_name_list = []
    for one_func in func_list:
        label1_name_list.append(bytearray2str(one_func.name))
    return_dict = {}
    if label1_name_list:
        return_dict['target'] = label1_name_list
    else:
        return_dict['target'] = "None"
    return json.dumps(return_dict)




def split_select_func_list(func_list,tokenizer,MAX_TOKEN_NUM):
    return_list = []
    tmp_list = []
    count = 0
    for one_func in func_list:
        tmp_list.append(one_func)
        tmp_prompt_str = construct_select_input_str(tmp_list)
        count += 1
        if get_str_token_num(tokenizer,tmp_prompt_str) > MAX_TOKEN_NUM:
            if len(tmp_list) ==1:
                return_list.append(tmp_list[:])
                tmp_list = []
                count = 0
            else:
                tmp_list.pop()
                return_list.append(tmp_list[:])
                tmp_list = [one_func]
                count = 1
        elif count > 8:
            return_list.append(tmp_list[:])
            tmp_list = []
            count = 0

    if tmp_list:
        return_list.append(tmp_list)
    return return_list

def is_connected(G,one_func1,one_func2):
    '''
    判断两个函数是否在图上有关系
    '''
    if nx.has_path(G,one_func1,one_func2) or nx.has_path(G,one_func2,one_func1):
        return True
    else:
        return False
    
# Generator
def gen_func_summary(func_body,model_type):
    question = {}
    question['Instruction'] = SummaryInstruction
    question['Input'] = func_body
    summary_prompt = Prompt(model_type)
    prompt_str = summary_prompt.gen_prompt(question)
    result = run_llm_custom(prompt_str)
    return result


def construct_prompt_str(Ins,input_str,model_type):
    question = {}
    question["Instruction"] = Ins
    question['Input'] = input_str
    prompt = Prompt(model_type)
    return prompt.gen_prompt(question)




