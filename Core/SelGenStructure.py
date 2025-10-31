from Core.GenData import *
from Core.CustomAlgorithm import *
from Core.CustomStructure import *
from Core.APIWarp import *
from Core.Utils import *
from Core.api import *
import networkx as nx
import re
from Core.logger import logger
from Core.promptRUN import *


def dict_to_doc(result_dict):
    # 假定传入的dict都是符合标准的dict
    api_doc = "### 函数签名\n"
    api_doc += result_dict["funciton_sign"] + "\n"
    api_doc += "### 函数功能\n"
    api_doc += result_dict["functional"] + "\n"
    api_doc += "### 应用场景\n"
    api_doc += result_dict["application_scenario"] + "\n"
    api_doc += "### 示例代码\n"
    api_doc += "```c\n"
    api_doc += result_dict["example_code"]
    api_doc += "\n```"
    return api_doc
    
def get_func_by_name(func_name,func_list):
    for one_func in func_list:
        tmp_body  = bytearray2str(one_func.body)
        tmp_func_name = tmp_body.split("{")[0].split('(')[0]
        if func_name in tmp_func_name:
            return one_func
        # if one_func.name.decode('utf-8',errors='ignore') == func_name:
        #     return one_func
    return None
def extract_json_from_text(text):
    # 使用正则表达式查找 JSON 格式的字符串
    json_regex = r'\{.*?\}'
    json_strings = re.findall(json_regex, text, re.DOTALL)
    
    # 尝试解析每个找到的 JSON 字符串
    json_objects = []
    for json_str in json_strings:
        try:
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # 如果解析失败，跳过这个字符串
            # print("JSON Decode Failed")
            continue
    
    return json_objects


def TS_filter_input_funcs_by_parameter(one_func,project):
    # 输出的是节点列表
    return_list = []
    import tree_sitter_c as tsc
    from tree_sitter import Language, Parser
    C_LANGUAGE = Language(tsc.language())
    parser = Parser(C_LANGUAGE)
    tree = parser.parse(one_func.body)
    root_node = tree.root_node
    # 找到函数定义头
    delcartor_node = next((node for node in iterate_tree(root_node) if node.type == "function_declarator"), None)
    if not delcartor_node:
        print(f"ERROR {one_func.name} has no function_declarator")
        return None
    # 找到参数列表
    parameter_list_node = next((node for node in iterate_tree(delcartor_node) if node.type == "parameter_list"), None)
    if not parameter_list_node:
        print(f"ERROR {one_func.name} has no parameter_list")
        return None
    # 将各个参数节点存入列表
    parameter_nodes = [node for node in iterate_tree(parameter_list_node) if node.type == "parameter_declaration"]
    if len(parameter_nodes) == 0:
        return False
    is_conatain_non_struct_pointer = False
    for parameter_node in parameter_nodes:
        ele_list = iterate_tree(parameter_node)
        if any(node.type == "pointer_declarator" for node in ele_list):
            # 将浮点数排除
            if any(node.text == b"float" for node in ele_list):
                continue
            # 排除指针数组
            if any(node.type == "number_literal" for node in ele_list):
                continue
            type_identifier_list = [node for node in ele_list if node.type == "type_identifier"]
            if not any(node.text in project.all_class_dict for node in type_identifier_list):
                # print(f"good parameter {parameter_node.text}")
                is_conatain_non_struct_pointer = True
                break   
        elif any(node.type == "array_declarator" for node in ele_list) and not any(node.type == "number_literal" for node in ele_list):
            # 将浮点数排除
            if any(node.text == b"float" for node in ele_list):
                continue
            type_identifier_list = [node for node in ele_list if node.type == "type_identifier"]
            if not any(node.text in project.all_class_dict for node in type_identifier_list):
                is_conatain_non_struct_pointer = True
                # print(f"good parameter {parameter_node.text}")
                break   
    return is_conatain_non_struct_pointer
def TS_get_func_return_parm(one_func,project):
    stack = [one_func.node]
    analyze_list = []
    while stack:
        node = stack.pop()
        for child in node.children:
            if child.type == "function_declarator":
                continue
            elif child.type == "compound_statement":
                continue
            stack.append(child)
            analyze_list.append(child)
    return_list = []
    for node in analyze_list:
        if node.text in project.all_class_dict:
            return_list.append(project.all_class_dict[node.text])
    return_list = list(set(return_list))
    if len(return_list) == 1:
        return return_list[0]
    elif len(return_list) > 1:
        print(f"ERROR get_return_parm {return_list}")
        return None
    else:
        return None
def get_func_parm_as_return_struct_list(one_func,project,model_type="codeqwen",run_count=1):
    # 针对函数的每个输入参数，检测其是否是传引用。
    # 这里判断函数是否对输入参数进行初始化进行判断。因为有些更改输入参数指针的行为也容易被误判为传引用。
    logger.info(f"get_func_parm_as_return_struct_list({one_func.name},{one_func.parm_list},{run_count})")
    return_list = []
    if len(one_func.parm_list) == 0:
        return return_list
    G = construct_graph(project.all_funcs)

    delcartor_node = next((node for node in iterate_tree(one_func.node) if node.type == "function_declarator"), None)
    parameter_list_node = next((node for node in iterate_tree(delcartor_node) if node.type == "parameter_list"), None)
    parameter_nodes = [node for node in iterate_tree(parameter_list_node) if node.type == "parameter_declaration"]
    for parameter_node in parameter_nodes:
        ele_list = iterate_tree(parameter_node)
        if not any(node.type == "pointer_declarator" for node in ele_list):
            continue
        if any(node.type == "const" for node in ele_list):
            continue
        type_identifier_list = [node for node in ele_list if node.type == "type_identifier"]
        target_node = next((node for node in type_identifier_list if node.text in project.all_class_dict), None)
        if target_node is None:
            continue
        #TODO 把对函数的初始化参数判断转变成对一堆函数列表的判断，防止出现判断失误
        # 提取one_func能够到达的所有函数
        
        func_str = bytearray2str(one_func.body)
        successors = nx.descendants(G, one_func)
        distance_dict = {node: nx.shortest_path_length(G, one_func, node) for node in successors}
        sorted_descendants = sorted(successors, key=lambda node: distance_dict[node])
        for tmp_func in sorted_descendants:
            is_need_func = False
            if distance_dict[tmp_func] > 2:
                continue
            for one_parm in tmp_func.parm_list:
                if bytearray2str(one_parm.name) == bytearray2str(target_node.text):
                    is_need_func = True
                    break
            # 如果行数超过400，那就说明内容过长了
            if is_need_func:
                new_str = func_str + bytearray2str(tmp_func.body)
                if len(new_str.split("\n")) > 400:
                    break
                func_str += "\n" + bytearray2str(tmp_func.body)
        if RUN_Prompt_is_func_parm_struct_init(func_str,bytearray2str(target_node.text),model_type,run_count):
            return_list.append(project.all_class_dict[target_node.text])

    logger.info(f"get_func_parm_as_return_struct_list({one_func.name},{one_func.parm_list},{run_count}) return {return_list}")
    return return_list

class ParmCode():
    def __init__(self,one_parm,func_list,model_type):
        self.parm = one_parm
        self.func_list = func_list
        self.parm_code = ""
        self.model_type = model_type
        self.other_parms = []
    
    def is_same_func_list(self,fronzen_set):
        return fronzen_set == frozenset(self.func_list)

    def output_all_parm_name_str(self):
        output_str = f"`{bytearray2str(self.parm.name)}`"
        if self.other_parms:
            output_str += ","
            for one_parm in self.other_parms[:-1]:
                output_str += f"`{bytearray2str(one_parm.name)}`,"
            output_str += f"`{bytearray2str(self.other_parms[-1].name)}`"
        
        return output_str
    def get_func_str(self):
        func_name_str = ""
        for one_func in self.func_list[:-1]:
            func_name_str += f"`{bytearray2str(one_func.name)}`,"
        func_name_str += f"`{bytearray2str(self.func_list[-1].name)}`"
        return func_name_str
    
    def gen_parm_code(self):
        #TODO 当func_list包含函数超过3个时候，需要分批次融合。
        if len(self.func_list) <= 1:
            self.parm_code = self.func_list[0].api_doc
            return

        ins = INS_generate_parm_funcs(self.func_list,self.parm)
        print(f"gen code by parm {self.func_list}")
        logger.info(f"gen code by parm {self.func_list}")
        
        prompt_str = construct_prompt_str(ins,"",self.model_type)
        #log
        log_prompt = construct_prompt_str(ins,"","content")
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
        logger.info(log_str)

        self.parm_code = run_llm_custom(prompt_str)
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{self.parm_code}<end>"
        logger.info(log_str)

    
# 负责生成C工程harness的类
class CGenerator():
    def __init__(self,selector,project,model_type="codeqwen"):
        self.selector = selector
        self.project = project
        self.model_type = model_type
    def filter_func(self):
        self.selector.filter_func()
    #对具有Process结构体的函数生成函数api文档（文档形式暂时未定），不对init函数和destory函数生成，这两种函数只需要知道函数定义即可调用。
    # TODO 定义文档基本格式和要素内容    
    def gen_api_doc(self):
        # init 获取api doc
        # init 函数只需要给出函数摘要就可以
        for one_func in self.selector.init_funcs:
            api_doc = bytearray2str(one_func.body).split("{")[0].replace("\n","")
            one_func.api_doc = api_doc
        # destory 函数获取api doc
        for one_func in self.selector.destory_funcs:
            func_head = bytearray2str(one_func.body).split('{')[0].replace("\n","")
            one_func.api_doc = func_head
        # input 获取api doc
        print(f"gen input func api doc {self.selector.input_func.name}")
        logger.info(f"gen input api doc {self.selector.input_func.name}")
        prompt_str = construct_prompt_str(INS_generate_api_doc(self.selector.input_func,self.selector),bytearray2str(self.selector.input_func.body),self.model_type)
        #log
        log_prompt = construct_prompt_str(INS_generate_api_doc(self.selector.input_func,self.selector),bytearray2str(self.selector.input_func.body),"content")
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
        logger.info(log_str)
        
        api_doc = run_llm_custom(prompt_str)


        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{api_doc}<end>"
        logger.info(log_str)
        self.selector.input_func.api_doc = api_doc

        # process函数获取api doc
        for one_func in self.selector.process_funcs:
            print(f"gen process api doc {one_func.name}")
            logger.info(f"gen process api doc {one_func.name}")
            prompt_str = construct_prompt_str(INS_generate_api_doc(one_func,self.selector),bytearray2str(one_func.body),self.model_type)
            #log
            log_prompt = construct_prompt_str(INS_generate_api_doc(one_func,self.selector),bytearray2str(one_func.body),"content")
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
            logger.info(log_str)

            api_doc = run_llm_custom(prompt_str)
            # result_dict = get_return_dict(result,["funciton_sign","functional","application_scenario","example_code"])
            # while result_dict is None:
            #         result = run_llm_custom(prompt_str)
            #         result_dict = get_return_dict(result,["funciton_sign","functional","application_scenario","example_code"])
            # api_doc = dict_to_doc(result_dict)
            # #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{api_doc}<end>"
            logger.info(log_str)
            
            one_func.api_doc = api_doc

    def gen_code_by_parm(self):
        # 根据对输入参数这个维度将函数分为若干组
        #TODO 当func_list包含函数超过3个时候，需要分批次融合。
        all_input_parms = self.selector.get_input_parms()
        self.parm_code_list = []
        self.parm_func_name_list = []
        self.input_parm_code_dict = {}
        analyzed_funcs_set = set()
        if len(all_input_parms) == 0:
            # 如果没有input parm，说明整个Input funcs就没有处理结构体，那么大概率就是单独函数，直接生成robo function
            all_funcs = self.selector.get_all_funcs()
            ins = INS_generate_no_parm_funcs(all_funcs)
            prompt_str = construct_prompt_str(ins,"",self.model_type)
            #log
            log_prompt = construct_prompt_str(ins,"","content")
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
            logger.info(log_str)
            self.robo_code = run_llm_custom(prompt_str)
            
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{self.robo_code}<end>"
            logger.info(log_str)
            return 
        # 暂时存储在这里
        print(f"gen code by parm: {all_input_parms} gen code")
        for one_parm in all_input_parms:
            func_list = self.selector.get_input_parm_funcs(one_parm.name)
            funcs_set = frozenset(func_list)
            # 防止出现重复分析相同的set
            if funcs_set in analyzed_funcs_set:
                for key in self.input_parm_code_dict:
                    if self.input_parm_code_dict[key].is_same_func_list(funcs_set):
                        self.input_parm_code_dict[key].other_parms.append(one_parm)
                continue
            analyzed_funcs_set.add(funcs_set)
            one_parm_code = ParmCode(one_parm,func_list,self.model_type)
            one_parm_code.gen_parm_code()
            self.input_parm_code_dict[one_parm] = one_parm_code
            
            # self.parm_func_name_list.append(func_name_str)
            
            
        
    def gen_robo_code(self):
        # 如果没有任何输入参数，那么说明只有单独一个input func，那么就直接跳过流程，直接生成harness code
        if not self.input_parm_code_dict:
            return 
        # 用有向图建立不同函数输入参数和输出参数之间的关系，形成参数的调用流程。进而对参数进行排序。
        parm_graph = nx.DiGraph()
        parm_list_sorted = []
        parm_dict = {}
        input_parms = self.selector.get_input_parms()
        for one_parm in input_parms:
            parm_graph.add_node(one_parm)
        all_funcs = self.selector.get_all_funcs()
        # 寻找处理输入结构体并返回结构体的函数，这样能够展示出结构体的流动状态，那些不在图里的结构体，暂定优先级是最高的。
        for one_func in all_funcs:
            if one_func.input_parm_set and one_func.output_parm_set:
                for out_parm in one_func.output_parm_set:
                    for in_parm in one_func.input_parm_set:
                        parm_graph.add_edge(in_parm,out_parm)
        for one_parm in self.input_parm_code_dict:
            parm_dict[one_parm] = len(list(nx.ancestors(parm_graph,one_parm)))
        sorted_keys = sorted(parm_dict, key=lambda x: parm_dict[x])
        for key in sorted_keys:
            parm_list_sorted.append(key)
        # 排序后的parm_list在parm_list_sorted中。

        # 根据结构体的情况，采用两两结合，按照逻辑顺序的方式生成代码。
        first_parm = parm_list_sorted[0]
        first_parm_code = self.input_parm_code_dict[first_parm]
        robo_dict = {}
        # robo_dict['parm_set'] = set(first_parm_code.parm) | set(first_parm_code.other_parms)
        robo_dict['parm_set'] = set([first_parm_code.parm] + list(first_parm_code.other_parms))
        robo_dict['func_list'] = first_parm_code.func_list
        robo_dict['code'] = first_parm_code.parm_code
        if len(parm_list_sorted) <= 1:
            self.robo_code = robo_dict["code"]
            return
        
        for one_parm in parm_list_sorted[1:]:
            if one_parm in robo_dict['parm_set']:
                continue
            parm_code = self.input_parm_code_dict[one_parm]
            print(f"gen robo code {robo_dict['parm_set']} {parm_code.parm}")
            logger.info(f"gen robo code {robo_dict['parm_set']} {parm_code.parm}")
            
            ins = INS_generate_robo_code(robo_dict,parm_code)
            prompt_str = construct_prompt_str(ins,"",self.model_type)
            #log
            log_prompt = construct_prompt_str(ins,"","content")
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
            logger.info(log_str)
            
            new_robo_code = run_llm_custom(prompt_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{new_robo_code}<end>"
            logger.info(log_str)
            
            robo_dict["parm_set"] |= set([parm_code.parm] + list(parm_code.other_parms))
            robo_dict['func_list'] += parm_code.func_list
            robo_dict['code'] = new_robo_code
            
        self.robo_code = robo_dict["code"]
            
    def gen_opt_code(self):
        # 如果robo code为空，说明不需要这个步骤（单独函数存在时候）
        if not self.robo_code:
            prompt_str = construct_prompt_str(INS_generate_opt_code(),self.opt_code,self.model_type)
            #log
            log_prompt = construct_prompt_str(INS_generate_opt_code(),self.opt_code,"content")
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
            logger.info(log_str)
            
            self.opt_code = run_llm_custom(prompt_str)
            #log
            log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{self.opt_code}<end>"
            logger.info(log_str)
            return 
        prompt_str = construct_prompt_str(INS_generate_opt_code(),self.robo_code,self.model_type)
        print("gen opt code")
        #log
        log_prompt = construct_prompt_str(INS_generate_opt_code(),self.robo_code,"content")
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
        logger.info(log_str)
        
        self.opt_code = run_llm_custom(prompt_str)
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{self.opt_code}<end>"
        logger.info(log_str)
    def gen_harness_code(self):
        prompt_str = construct_prompt_str(INS_generate_harness_code(),self.opt_code,self.model_type)
        #log
        log_prompt = construct_prompt_str(INS_generate_harness_code(),self.opt_code,"content")
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-question-<,sp1it.>-{log_prompt}<end>"
        logger.info(log_str)
        self.harness_code = run_llm_custom(prompt_str)
        #log
        log_str = f"<start>{hex(log_prompt.__hash__())}-<,sp1it.>-answer-<,sp1it.>-{self.harness_code}<end>"
        logger.info(log_str)
    
# 每一个Libfuzzer都是围绕一个input函数建立的
class OneSelectorGroup():
    def __init__(self,one_func) -> None:
        self.input_func = one_func
        self.destory_funcs = []
        self.init_funcs = []
        self.process_funcs = []
    
    # 首先剔除掉selector中输入结构体没有被初始化的函数（可能是筛选错误）。        
    def filter_func(self):
        filtered_process_func = []
        for one_func in self.process_funcs:
            is_need = True
            input_parms = one_func.input_parm_set
            for one_parm in input_parms:
                if not (self.get_init_parm_funcs(one_parm.name) or self.get_output_parm_funcs(one_parm.name)):
                    is_need = False
            if is_need:
                filtered_process_func.append(one_func)
        self.process_funcs = filtered_process_func

    def get_all_funcs(self):
        return_list = []
        return_list.append(self.input_func)
        return_list.extend(self.destory_funcs)
        return_list.extend(self.init_funcs)
        return_list.extend(self.process_funcs)
        return return_list

    def get_output_parms(self):
        output_parm_set = set()
        output_parm_set |= self.input_func.output_parm_set
        for one_func in self.process_funcs:
            output_parm_set |= one_func.output_parm_set
        for one_func in self.init_funcs:
            output_parm_set |= one_func.output_parm_set
        return output_parm_set

    # 找到所有的输入参数
    def get_input_parms(self):
        input_parm_set = set()
        input_parm_set |= self.input_func.input_parm_set
        for one_func in self.init_funcs:
            input_parm_set |= one_func.input_parm_set
        for one_func in self.process_funcs:
            input_parm_set |= one_func.input_parm_set
        return input_parm_set
    def get_init_parms(self):
        init_parm_set = set()
        for one_func in self.init_funcs:
            init_parm_set |= one_func.init_parm_set
            init_parm_set |= one_func.init_return_set
            
        init_parm_set |= self.input_func.init_parm_set
        init_parm_set |= self.input_func.init_return_set
        return init_parm_set
    
    def get_input_parm_funcs(self,parm_name):
        return_list = []
        if any(one_parm.name == parm_name for one_parm in self.input_func.input_parm_set):
            return_list.append(self.input_func)
        if any(one_parm.name == parm_name for one_parm in self.input_func.init_parm_set):
            if self.input_func not in return_list:
                return_list.append(self.input_func)

        for one_func in self.init_funcs:
            if any(one_parm.name == parm_name for one_parm in one_func.input_parm_set):
                return_list.append(one_func)
        for one_func in self.process_funcs:
            if any(one_parm.name == parm_name for one_parm in one_func.input_parm_set):
                return_list.append(one_func)

        return return_list
    
    def get_output_parm_funcs(self,parm_name):
        return_list = []
        if any(one_parm.name == parm_name for one_parm in self.input_func.output_parm_set):
            return_list.append(self.input_func)
        if self.init_funcs:
            for one_func in self.init_funcs:
                if any(one_parm.name == parm_name for one_parm in one_func.output_parm_set):
                    return_list.append(one_func)
        if self.process_funcs:
            for one_func in self.process_funcs:
                if any(one_parm.name == parm_name for one_parm in one_func.output_parm_set):
                    return_list.append(one_func)
        return return_list
    def get_init_parm_funcs(self,parm_name):
        return_list = []
        if any(one_parm.name == parm_name for one_parm in self.input_func.init_parm_set):
            return_list.append(self.input_func)
        if self.init_funcs:
            for one_func in self.init_funcs:
                if any(one_parm.name == parm_name for one_parm in one_func.init_parm_set):
                    return_list.append(one_func)
                elif any(one_parm.name == parm_name for one_parm in one_func.init_return_set):
                    return_list.append(one_func)
        # if self.process_funcs:
        #     for one_func in self.process_funcs:
        #         if any(one_parm.name == parm_name for one_parm in one_func.init_parm_set):
        #             return_list.append(one_func)
        return return_list
    def get_destory_parm_funcs(self,parm_name):
        return_list = []
        if self.destory_funcs:
            for one_func in self.destory_funcs:
                if any(one_parm.name == parm_name for one_parm in one_func.input_parm_set):
                    return_list.append(one_func)
        return return_list

    def show(self):
        return_str = f"input func is {self.input_func.name}\n"
        if self.init_funcs:
            return_str += "\n".join(f"init func {one_func.name}" for one_func in self.init_funcs) + "\n"

        if self.process_funcs:
            return_str += "\n".join(f"process func {one_func.name}" for one_func in self.process_funcs) + "\n"

        if self.destory_funcs:
            return_str += "\n".join(f"destory func {one_func.name}" for one_func in self.destory_funcs) + "\n"
        return return_str
    def todict(self):
        return_dict = {}
        input_func_dict = {}
        input_func_dict['name'] = bytearray2str(self.input_func.name)
        input_func_dict['input_parm'] = [bytearray2str(one_parm.name) for one_parm in self.input_func.input_parm_set]
        input_func_dict['init_parm'] = [bytearray2str(one_parm.name) for one_parm in self.input_func.init_parm_set]
        input_func_dict['output_parm'] = [bytearray2str(one_parm.name) for one_parm in self.input_func.output_parm_set]
        input_func_dict['return_init_parm'] = [bytearray2str(one_parm.name) for one_parm in self.input_func.init_return_set]
        return_dict['input'] = input_func_dict
        return_dict['init'] = [] 
        return_dict['process'] = []
        return_dict['destory'] = []
        for one_func in self.process_funcs:
            one_func_dict = {}
            one_func_dict['name'] = bytearray2str(one_func.name)
            one_func_dict['input_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.input_parm_set]
            one_func_dict['init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_parm_set]
            one_func_dict['output_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.output_parm_set]
            one_func_dict['return_init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_return_set]
            return_dict['process'].append(one_func_dict)
        for one_func in self.init_funcs:
            one_func_dict = {}
            one_func_dict['name'] = bytearray2str(one_func.name)
            if one_func.is_func_analyzed():
                one_func_dict['input_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.input_parm_set]
                one_func_dict['init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_parm_set]
                one_func_dict['output_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.output_parm_set]
                one_func_dict['return_init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_return_set]
            else:
                one_func_dict['input_parm'] = []
                one_func_dict['init_parm'] = []
                one_func_dict['output_parm'] = []
                one_func_dict['return_init_parm'] = []               
            return_dict['init'].append(one_func_dict)
        for one_func in self.destory_funcs:
            one_func_dict = {}
            one_func_dict['name'] = bytearray2str(one_func.name)
            if one_func.is_func_analyzed():
                one_func_dict['input_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.input_parm_set]
                one_func_dict['init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_parm_set]
                one_func_dict['output_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.output_parm_set]
                one_func_dict['return_init_parm'] = [bytearray2str(one_parm.name) for one_parm in one_func.init_return_set]
            else:
                one_func_dict['input_parm'] = []
                one_func_dict['init_parm'] = []
                one_func_dict['output_parm'] = []
                one_func_dict['return_init_parm'] = []   
            return_dict['destory'].append(one_func_dict)
        return return_dict


class CSelector():
    def __init__(self,func_list,project,model_type,run_acc) -> None:
        self.project = project
        self.model_type = model_type
        self.origin_list = func_list
        self.run_acc = run_acc
        self.func_list = func_list
        self.init()
    def init(self):
        self.G =  construct_graph(self.func_list)
        if self.run_acc == 1:
            self.run_count = 1
        elif self.run_acc == 2:
            self.run_count = 3
        elif self.run_acc == 3:
            self.run_count = 5
        elif self.run_acc == 4:
            self.run_count = 7
        elif self.run_acc == 5:
            self.run_count = 9
        else:
            print(f"ERROR not support run_acc {self.run_acc}")
            return 
    # 专门用来做测试的函数
    ########################################
    #########################################        
    def run(self):
        print(f"filtering functions")
        filtered_funcs = self.filter_funcs(self.func_list)
        print(f"filtered functions {list(set(self.func_list) - set(filtered_funcs))}")
        print("finding destory functions")
        destory_func_list = self.find_destory_funcs(filtered_funcs)
        print(f"destory func list {destory_func_list}")
 
        # 寻找input函数
        print("finding input functions")
        input_target_list = [one_func for one_func in filtered_funcs if one_func not in destory_func_list]
        input_func_list = self.find_input_funcs(input_target_list)

        # 过滤掉文件操作函数
        input_func_list = [one_func for one_func in input_func_list if not RUN_Prompt_is_func_contain_file_op(one_func,self.model_type,self.run_count)]
        print(f"input functions {input_func_list}")
        selector_list = [OneSelectorGroup(one_func) for one_func in input_func_list]

        init_target_func_list = [one_func for one_func in filtered_funcs if one_func.type not in ["input", "destory"]]

        # 每个处理外部输入的函数都要找到对应的初始化函数
        print("finding initial functions")
        for one_selector in selector_list:
            target_func = one_selector.input_func
            tmp_init_target_func_list = [tmp_func for tmp_func in init_target_func_list if not nx.has_path(self.G,target_func,tmp_func)]
            tmp_init_list = self.find_init_funcs(target_func,tmp_init_target_func_list)
            tmp_init_list = remove_inclusive(self.G,tmp_init_list)
            one_selector.init_funcs = tmp_init_list[:]
            print(f"{one_selector.input_func.name} init funcs {one_selector.init_funcs}")
            logger.info(f"{one_selector.input_func.name} init funcs {one_selector.init_funcs}")

        # 寻找对结构体进行处理的函数
        print("finding process functions")
        init_funcs_set = set([item for one_selector in selector_list for item in one_selector.init_funcs])
        process_target_funcs = [one_func for one_func in init_target_func_list if one_func not in init_funcs_set]
        for one_selector in selector_list:
            target_func = one_selector.input_func
            tmp_process_target_funcs = [tmp_func for tmp_func in process_target_funcs if not nx.has_path(self.G,target_func,tmp_func)]
            tmp_process_list = self.find_process_funcs(target_func,tmp_process_target_funcs)
            # tmp_process_list = remove_inclusive(tmp_process_list)
            # one_selector.process_funcs = tmp_process_list[:]
            # process func也要剔除掉包含文件操作的函数
            one_selector.process_funcs =  [one_func for one_func in tmp_process_list if not RUN_Prompt_is_func_contain_file_op(one_func,self.model_type,self.run_count)]
            print(f"{one_selector.input_func.name} process funcs {one_selector.process_funcs}")
            logger.info(f"{one_selector.input_func.name} process funcs {one_selector.process_funcs}")

        # 过滤处理函数
        print("filtering process functions")
        # 对selector_list 中每个selector中的process函数进行筛选
        input_list = []
        for one_s in selector_list:
            input_list.append(one_s.input_func)
        for one_s in selector_list:
            del_list = []
            for one_func in one_s.process_funcs:
                for input_func in input_list:
                    if nx.has_path(self.G,input_func,one_func):
                        del_list.append(one_func)
                        print(f"del {one_func.name}")
                        break
            for del_func in del_list:
                one_s.process_funcs.remove(del_func)
            one_s.filter_func()
                
        # 寻找每个selector的销毁函数
        print("matching destory functions")
        for one_selector in selector_list:
            target_func = one_selector.input_func
            tmp_destory_list = []
            output_parm_set = one_selector.get_output_parms()
            print(f"output parms {output_parm_set}")
            for one_parm in output_parm_set:
                for destory_func in destory_func_list:
                    if one_parm in destory_func.input_parm_set:
                        tmp_destory_list.append(destory_func)
            one_selector.destory_funcs = tmp_destory_list[:]
            print(f"{one_selector.input_func.name} destory funcs {one_selector.destory_funcs}")
            logger.info(f"{one_selector.input_func.name} destory funcs {one_selector.destory_funcs}")
        return selector_list
        

    def filter_funcs(self,func_list):
        pre_fobid_list = []
        if len(func_list) > 100:
            # 先根据每个函数被直接或者间接调用的次数排除部分被反复调用的函数，这种函数一般被认为是底层函数
            callee_dict = {}
            for one_func in func_list:
                callee_dict[one_func] = len(list(nx.ancestors(self.G, one_func)))
            sorted_keys = sorted(callee_dict, key=lambda x: callee_dict[x], reverse=True)
            if callee_dict[sorted_keys[0]] > 0.15 * len(func_list):
                thd_num = callee_dict[sorted_keys[0]] - (0.1 * len(func_list))
                for one_func in sorted_keys:
                    if callee_dict[one_func] > thd_num:
                        pre_fobid_list.append(one_func)
        print(f"pre forbid function list {pre_fobid_list}")
        target_func_list = [one_func for one_func in func_list if one_func not in pre_fobid_list]
        filtered_func_list =[]
        for one_func in target_func_list:
            func_name_str = bytearray2str(one_func.name)
            # 检测是否是测试函数，主要看文件名
            if not any(prefix in func_name_str for prefix in ["benchmark", "perf","test", "TEST","Test"]):
                filtered_func_list.append(one_func)
                continue
            if RUN_prompt_is_func_benchmark(one_func,self.model_type,self.run_count):
                continue
            if RUN_prompt_is_func_test(one_func,self.model_type,self.run_count):
                continue
            
            filtered_func_list.append(one_func)
        return filtered_func_list


    def find_input_funcs(self,func_list):
        # 首先通过判断函数参数个数筛选一遍函数
        target_func_list = [one_func for one_func in func_list if TS_filter_input_funcs_by_parameter(one_func, self.project)]
        print(f"finding input funcs, there are {len(target_func_list)} funcs")
        one_parm_func_list = select_one_paramter_funcs(target_func_list,self.model_type,self.run_count)
        two_parm_func_list = select_two_parameter_funcs(one_parm_func_list,self.model_type,self.run_count)
        one_parm_func_list = remove_inclusive(self.G,one_parm_func_list)
        two_parm_func_list = remove_inclusive(self.G,two_parm_func_list)
        return_list = []
        for one_func in list(set(one_parm_func_list+ two_parm_func_list)):
            if not RUN_prompt_is_func_common(one_func,self.model_type,self.run_count):
                return_list.append(one_func)
        [setattr(one_func, 'type', "input")  for one_func in return_list]
        return return_list  
    
    def find_init_funcs(self,one_func,func_list):
        return_list = []
        one_func.type = "input"
        self.analyze_funcs_parm([one_func])
        need_init_struct_list = list(one_func.input_parm_set)
        if not need_init_struct_list:
            return return_list
        self.analyze_funcs_parm(func_list)
        for tmp_func in func_list:
            for need_struct in need_init_struct_list:
                if need_struct in tmp_func.init_parm_set:
                    return_list.append(tmp_func)
                    break
                if need_struct in tmp_func.init_return_set:
                    return_list.append(tmp_func)
                    break
        return return_list

    def find_process_funcs(self,one_func,func_list):
        self.analyze_funcs_parm([one_func])
        self.analyze_funcs_parm(func_list)
        return_list = []
        analyze_list = [one_func]
        analyzed_set = set()
        while analyze_list:
            test_func = analyze_list.pop()
            output_struct_list = list(test_func.output_parm_set)
            if output_struct_list:
                for tmp_func in func_list:
                    if tmp_func in analyzed_set:
                        continue
                    for one_struct in output_struct_list:
                        if one_struct in tmp_func.input_parm_set:
                            analyze_list.append(tmp_func)
                            analyzed_set.add(tmp_func)
                            return_list.append(tmp_func)

        return list(set(return_list))
        
    def find_destory_funcs(self,func_list):
        return_list = []
        free_list = ["free","destroy","delete","clean","release","clear","dispose","deallocate","close","finalize","terminate","shutdown","uninitialize","reset"]
        tmp_candi_list = []
        # 如果函数中不包含free destory等关键字，那么是销毁函数的概率就比较低
        for one_func in func_list:
            func_str = bytearray2str(one_func.name)
            if any(keyword in func_str for keyword in free_list):
                tmp_candi_list.append(one_func)
        tmp_list = [one_func for one_func in tmp_candi_list if is_func_destory(one_func, self.model_type, self.run_count)]
        for one_func in tmp_list:
            return_obj = get_func_destory_object(one_func,self.project,self.model_type,self.run_count)
            if return_obj:
                if one_func.input_parm_set is None:
                    one_func.input_parm_set = set()
                    one_func.init_parm_set = set()
                    one_func.output_parm_set = set()
                    one_func.init_return_set = set()
                if return_obj != "N/A":
                    one_func.input_parm_set.add(return_obj)
                one_func.type = "destory"
                return_list.append(one_func)
        return return_list


    def analyze_funcs_parm(self,func_list):
        # 先将所有函数分析一遍参数,主要是输入和返回参数，以及这些参数是否涉及到初始化。
        for one_func in tqdm(func_list,desc="analyzing parms"):
            if one_func.is_func_analyzed():
                continue
            # 函数输入参数是否被函数初始化（为output_parm以及init parm)
            parm_struct_list = get_func_parm_as_return_struct_list(one_func,self.project,self.model_type,self.run_count)
            one_func.output_parm_set = set()
            one_func.init_parm_set = set()
            if parm_struct_list:
                for tmp_struct in parm_struct_list:
                    if tmp_struct.name in self.project.all_class_dict:
                        one_func.output_parm_set.add(self.project.all_class_dict[tmp_struct.name])
                        one_func.init_parm_set.add(self.project.all_class_dict[tmp_struct.name])
            one_func.input_parm_set = set()
            for one_parm in one_func.parm_list:
                if one_parm.name in self.project.all_class_dict:
                    tmp_struct = self.project.all_class_dict[one_parm.name]
                    if tmp_struct not in one_func.output_parm_set:
                        one_func.input_parm_set.add(tmp_struct)
            # 查看函数返回值
            one_func.init_return_set = set()
            # return_parm = get_func_return_struct(one_func,self.project,self.model_type,self.run_count)
            # 通过tree-sitter分析得到函数返回的结构体
            return_parm = TS_get_func_return_parm(one_func,self.project)
            if not return_parm:
                continue
            one_func.output_parm_set.add(return_parm)
            if RUN_Prompt_is_func_return_struct_init(one_func,bytearray2str(return_parm.name),self.model_type,self.run_count):
                if return_parm.name in self.project.all_class_dict:
                    one_func.init_return_set.add(self.project.all_class_dict[return_parm.name])