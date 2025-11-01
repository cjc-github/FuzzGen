import os
import json
from tqdm import tqdm
import random


def split_list_into_n_parts(lst, n):
    total_sum = sum(lst)
    sorted_lst = sorted(lst)
    avg = total_sum / n
    result = []
    temp = []
    current_sum = 0
    for num in sorted_lst:
        if current_sum + num <= avg:
            temp.append(num)
            current_sum += num
        else:
            result.append(temp)
            temp = [num]
            current_sum = num
    result.append(temp)
    return result

'''
数据的构造，要遵循{"instruction":,"input":,"output":}
'''
Spliter = "\"\"\""
SelectorInstruction = '''
LibFuzzer is a fuzz testing tool for libraries (such as C/C++ libraries), which detects errors such as buffer overflows and heap corruption by continuously sending modified inputs to the target function. When choosing a target function for LibFuzzer testing, the following principles should typically be considered:
- Input Range: Choose functions with a wide input range. This means the function should accept various possible inputs that cover different scenarios you want to test.
- Complexity: Select parts of the function that have moderate complexity. Functions that are too simple may not likely cause errors, while overly complex functions may slow down the fuzzing process.
Expected Errors: Analyze the code to identify potential error points, such as memory errors and boundary condition errors. Choose code sections related to these errors for fuzzing.
- Function Call Chain: Select key functions in the call chain that may propagate errors or affect critical program states.
- Coverage Ability: Choose functions that are easily covered by the fuzz testing framework. This means the functions should be quickly callable and have input parameters that are simple basic types rather than complex data structures.
- Importance: Choose functions that have the most impact on the program's correctness. These functions may include critical algorithms, data structure operations, etc.

Which function below is suitable to serve as the target test function for libfuzzer? Output the function in JSON format and output none if no function is suitable.
'''
SelectorInstruction = '''
Which function below is suitable to serve as the target test function for libfuzzer? Output the function in JSON format and output none if no function is suitable.
'''
MAX_TOKEN_NUM = 6*1024

class OneProjectStore(object):
    def __init__(self,base_name,tokenizer) -> None:
        self.base_name = base_name
        self.tokenizer = tokenizer
        self.initialize()
    def initialize(self):
        data_file = OneFileDecode(self.base_name)
        all_funcs = data_file['funcs']
        body = data_file['body']
        cops = data_file['cops']
        if len(all_funcs) == 0:
            print(f"{self.base_name} is wrong")
            self.selector_qa_list = None
            self.generator_qa_list = None
            return
        if len(body) == 0:
            print(f"{self.base_name} is wrong")
            self.generator_qa_list = None
            self.selector_qa_list = None
            return
        classes = data_file['class']
        selector_gen_one = SelectorGen(all_funcs)
        selector_gen_one.gen_qa_by_file(self.tokenizer)
        self.selector_qa_list = selector_gen_one.qa_list[:]

        generator_gen_one = GeneratorGen(body,all_funcs,classes,cops)
        generator_gen_one.gen_qa()
        self.generator_qa_list = generator_gen_one.qa_list[:]

    def selector_save_to_json(self,output_path):
        base_name = os.path.splitext(os.path.basename(self.base_name))[0]
        target_path = os.path.join(output_path,base_name + "_Selector_QA.json")
 
        with open(target_path,'w') as f:
            json.dump(self.selector_qa_list,f)
        print(f"write to {target_path}")
    
    def generator_save_to_json(self,output_path):
        base_name = os.path.splitext(os.path.basename(self.base_name))[0]
        target_path = os.path.join(output_path,base_name + "_Generator_QA.json")
        with open(target_path,'w') as f:
            json.dump(self.generator_qa_list,f)
        print(f"write to {target_path}")
    


class OneFileDecode(object):
    def __init__(self,file_path) -> None:
        self.file_path = file_path
        self.__decode_jsonl()
    
    
    def __decode_jsonl(self):
        with open(self.file_path,'r') as f:
            self.ele_list = json.load(f)

'''
一般来说是针对一个工程内的函数进行QA对生成
'''
class SelectorGen(object):
    '''
    传入的都是func_list
    '''
    def __init__(self,file_path,tokenizer) -> None:
        self.file_path = file_path
        self.tokenizer = tokenizer
        self.func_list = []

    def init(self):
        with open(self.file_path,'r') as f:
            self.func_list = json.load(f)
        self.__classify_funcs()
        if len(self.func_list) == 0:
            print(f"ERROR {self.file_path} contains no funcs")
            return
        self.readme = self.func_list[0]['readme']
        self.qa_list = []
        if len(self.readme) > 0:
            self.instruction = f"There is a project with a core functionality described as {self.readme}.\nThe code snippet below is part of this project.  Please select the appropriate function from the code below to use as the libfuzzer function. Output the function in JSON format and output none if no function is suitable.\n"
        else:
            self.instruction = f"Please select the appropriate function from the code below to use as the libfuzzer function. Output the function in JSON format and output none if no function is suitable.\n"
        # self.__filter_funcs()

    def process(self):
        self.init()
        if not self.func_list:
            return
        print(f'[SelectorGen] get {len(self.func_list)} funcs')
        self.gen_qa_by_file()

    def __classify_funcs(self):
        self.all_class_func_dict = dict()
        self.none_class_func_dict = dict()
        for func_dict in self.func_list:
            class_set = set(func_dict['class'])
            key_str = str(class_set)
            if key_str == str(set([])):
                if func_dict['contain']  in self.none_class_func_dict:
                    if func_dict['isdriver'] == 1:
                        self.none_class_func_dict[func_dict['contain']][1].append(func_dict)
                    else:
                        self.none_class_func_dict[func_dict['contain']][0].append(func_dict)
                else:
                    self.none_class_func_dict[func_dict['contain']] = [[],[]]
                    if func_dict['isdriver'] == 1:
                        self.none_class_func_dict[func_dict['contain']][1] = [func_dict]
                        self.none_class_func_dict[func_dict['contain']][0] = []
                    else:
                        self.none_class_func_dict[func_dict['contain']][1] = []
                        self.none_class_func_dict[func_dict['contain']][0] = [func_dict]
            else:
                if key_str not in self.all_class_func_dict:
                    self.all_class_func_dict[key_str] = [[],[]]
                    if func_dict['isdriver'] == 1:
                        self.all_class_func_dict[key_str][1] = [func_dict]
                        self.all_class_func_dict[key_str][0] = []
                    else:
                        self.all_class_func_dict[key_str][0] = [func_dict]
                        self.all_class_func_dict[key_str][1] = []
                else:
                    if func_dict['isdriver'] == 1:
                        self.all_class_func_dict[key_str][1].append(func_dict)
                    else:
                        self.all_class_func_dict[key_str][0].append(func_dict)

    
    def construct_qa(self,label1_list,label0_list):
        qa_dict ={}
        qa_dict["instruction"] = self.instruction
        all_list = label1_list + label0_list
        random.shuffle(all_list)
        Question = ""
        for func_dict in all_list:
            Question += Spliter + "\n"
            Question += func_dict['body'] + "\n" + Spliter + "\n"
        qa_dict['input'] = Question
        if len(label1_list) == 0:
            Answer = "{\n\t\"target\": \"None\",\n}" 
        else:
            Answer = "{\n\t\"target\":["
            for func_dict in label1_list[:-1]:
                Answer += "\"" + func_dict['name'] +"\","
            Answer += "\"" + label1_list[-1]['name'] +"\"]\n}"
        qa_dict['output'] = Answer
        return qa_dict

            
    def save_to_json(self,output_path):
        with open(output_path,'w') as f:
            json.dump(self.qa_list,f)

    
    def __get_token_num(self,qa_dict):
        try:
            body = qa_dict['instruction'] + qa_dict['input'] + qa_dict['output']
            model_inputs = self.tokenizer(body)
            return len(model_inputs['input_ids'])
        except Exception as e:
            return 999999999999999999999999
    def __get_str_token_num(self,body):
        model_inputs = self.tokenizer(body)
        return len(model_inputs['input_ids'])


    def gen_qa_by_file(self):
        if len(self.all_class_func_dict.keys()) > 0:
            for class_name in tqdm(self.all_class_func_dict):
                label0_list = self.all_class_func_dict[class_name][0][:]
                label1_list = self.all_class_func_dict[class_name][1][:]
                if not label1_list:
                    continue

                tmp_dict = self.construct_qa(label1_list,label0_list)
                if self.__get_token_num(tmp_dict) < MAX_TOKEN_NUM:
                    self.qa_list.append(tmp_dict)
                else:
                    # 如果一个类或者文件中的所有函数长度过长，那么就平均分成n份
                    all_list = label0_list + label1_list
                    len_list = []
                    len_dict = {}
                    for i,func_dict in enumerate(all_list):
                        tmp_len = self.__get_str_token_num(func_dict['body'])
                        if tmp_len > MAX_TOKEN_NUM:
                            continue
                        len_list.append(tmp_len)
                        if tmp_len in len_dict:
                            len_dict[tmp_len].append(i)
                        else:
                            len_dict[tmp_len] = [i]
                    len_dict_str = json.dumps(len_dict)
                    if len(all_list) > 2:
                        for n in range(2,len(all_list)):
                            tmp_len_dict = json.loads(len_dict_str)
                            tmp_len_list = len_list[:]
                            tmp_list = []
                            is_need = True
                            parted_list = split_list_into_n_parts(tmp_len_list,n)
                            for one_list in parted_list:
                                tmp_label1_list =[]
                                tmp_label0_list = []
                                for one_len in one_list:
                                    index = tmp_len_dict[str(one_len)].pop()
                                    func_dict = all_list[index]
                                    if func_dict['isdriver'] == 1:
                                        tmp_label1_list.append(func_dict)
                                    else:
                                        tmp_label0_list.append(func_dict)
                                tmp_dict = self.construct_qa(tmp_label1_list,tmp_label0_list)
                                if self.__get_token_num(tmp_dict) < MAX_TOKEN_NUM:
                                    tmp_list.append(tmp_dict)
                                else:
                                    is_need = False
                                    break
                            if is_need:
                                self.qa_list += tmp_list
                                break
                            
        if len(self.none_class_func_dict.keys()) > 0:
            for source_file in tqdm(self.none_class_func_dict):
                label0_list = self.none_class_func_dict[source_file][0][:]
                label1_list = self.none_class_func_dict[source_file][1][:]
                if not label1_list:
                    continue

                tmp_dict = self.construct_qa(label1_list,label0_list)
                if self.__get_token_num(tmp_dict) < MAX_TOKEN_NUM:
                    self.qa_list.append(tmp_dict)
                else:
                    # 如果一个类或者文件中的所有函数长度过长，那么就平均分成n份
                    all_list = label0_list + label1_list
                    len_list = []
                    len_dict = {}
                    for i,func_dict in enumerate(all_list):
                        tmp_len = self.__get_str_token_num(func_dict['body'])
                        if tmp_len > MAX_TOKEN_NUM:
                            continue
                        len_list.append(tmp_len)
                        if tmp_len in len_dict:
                            len_dict[tmp_len].append(i)
                        else:
                            len_dict[tmp_len] = [i]
                    len_dict_str = json.dumps(len_dict)
                    if len(all_list) > 2:
                        for n in range(2,len(all_list)):
                            tmp_len_dict = json.loads(len_dict_str)
                            tmp_len_list = len_list[:]
                            tmp_list = []
                            is_need = True
                            parted_list = split_list_into_n_parts(tmp_len_list,n)
                            for one_list in parted_list:
                                tmp_label1_list =[]
                                tmp_label0_list = []
                                for one_len in one_list:
                                    index = tmp_len_dict[str(one_len)].pop()
                                    func_dict = all_list[index]
                                    if func_dict['isdriver'] == 1:
                                        tmp_label1_list.append(func_dict)
                                    else:
                                        tmp_label0_list.append(func_dict)
                                tmp_dict = self.construct_qa(tmp_label1_list,tmp_label0_list)
                                if self.__get_token_num(tmp_dict) < MAX_TOKEN_NUM:
                                    tmp_list.append(tmp_dict)
                                else:
                                    is_need = False
                                    break
                            if is_need:
                                self.qa_list += tmp_list
                                break



                        
        

'''
Generator 需要目标的libfuzzer，以及选择的函数，函数摘要，以及其他函数。

把Project的路径给出，然后读取每个Libfuzzer的文件，根据文件，判断label1 func是否在其中，以此找到合适的函数。
'''        

class GeneratorGen(object):
    def __init__(self,file_path,tokenizer) -> None:
        self.file_path = file_path
        self.tokenizer = tokenizer

    def init(self) -> None:
        with open(self.file_path,'r') as f:
            driver_dict = json.load(f)
        
        self.instruction = "Based on the functions or class listed above and their descriptions, write a libfuzzer to test as many of the above codes as possible. Use JSON format to output the codes that have not been used."

        self.driver = driver_dict['body']
        self.cop_list = driver_dict['cops']
        self.func_list = driver_dict['funcs']
        self.class_list = driver_dict['class']
        self.qa_list = []

        class_name_set = set()
        for class_dict in class_name_set:
            class_name_set.add(class_dict['name'])
        self.target_funcs = []
        self.label1_funcs = []

        for func_dict in self.func_list:
            if func_dict['isdriver'] == 1:
                self.label1_funcs.append(func_dict)
        
        for func_dict in self.label1_funcs:
            if len(func_dict['class']) == 0:
                self.target_funcs.append(func_dict)
            else:
                is_need = True
                for class_name in func_dict['class']:
                    if class_name in class_name_set:
                        is_need = False
                        break
                if is_need:
                    self.target_funcs.append(func_dict)
    def process(self):
        self.init()
        if len(self.label1_funcs) ==0:
            return
        if len(self.func_list) == 0:
            return
        self.gen_qa()

    def save_to_json(self,output_path):
        with open(output_path,'w') as f:
            json.dump(self.qa_list,f)

    def construct_qa(self):
        qa_dict = {}
        qa_dict["instruction"] = self.instruction
        Question = ""

        for class_dict in self.class_list:
            Question += Spliter + '\n' + class_dict['body'] + Spliter + '\n'

        for func_dict in self.target_funcs:
            Question += Spliter + "\n" + "//Include Path: " + func_dict["include"] + "\n" + func_dict["body"] + "\n"
            if len(func_dict['return']) > 0:
                Question += "/* Return Type is:" + func_dict['return'] + "\n */"
            if len(func_dict["parm"]) > 0:
                Question += "/* Paramters are:\n"
                for parm_str in func_dict['parm']:
                    Question += parm_str + "\n"
                Question += "*/\n"
            Question += "\n" + Spliter + "\n" 
        Answer = Spliter +self.driver  + Spliter + "\n"
        if len(self.cop_list) > 0:
            for cop_str in self.cop_list:
                Answer += Spliter + cop_str + Spliter + "\n"

        qa_dict["input"] = Question
        qa_dict["output"] = Answer
        return qa_dict
    
    def gen_qa(self):
        self.qa_list = [self.construct_qa()]

    