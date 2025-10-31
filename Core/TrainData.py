from Core.CustomStructure import *
from Core.CustomAlgorithm import *
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
import json
from tqdm import tqdm
from Core.APIWarp import *
from Core.api import *
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
        self.all_funcs = []
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
        # 如果最终没有找到label1函数，那么就不要装入到driver list 中
        if fuzzer.label1_list:
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
        
    '''
    解析readme文件
    '''
    def parse_readme_file(self,model_type):
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
                prompt = Prompt(model_type)
                q = {}
                # q["Instruction"] = "根据下面的Readme的一部分，用一句话概括该工程实现的核心功能，只需要介绍实现的功能即可，其他的不需要提及\n"
                q["Instruction"] = "Based on a section of the Readme, summarize the core functionality of the project in one sentence. Focus only on the functionality implemented, without mentioning any other details.\n"
                q["Input"] = readme_content[:5000]
                readme_prompt = prompt.gen_prompt(q)
                # api = llamacpp(host="10.17.188.201",port=7070)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面描述，简要概括一下工程实现的核心功能。\n"
                q["Instruction"] = "Briefly summarize the core functionality implemented in the project based on the description provided.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面描述，用一句话概括工程的核心功能:\n"
                q["Instruction"] = "Summarize the core functionality of the project in one sentence based on the description provided.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = "根据下面的描述，用一句话且用尽可能少的文字总结下面文字中工程的核心功能\n"
                q["Instruction"] = "Summarize the core functionality of the project in the text below using one sentence and as few words as possible.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f"如果要对实现【{result}】功能的工程编写libfuzzer，都需要测试具有哪些功能的函数？\n"
                q["Instruction"] = f"What functions need to be tested when writing a libfuzzer for a C/C++ source code project that aims to achieve the functionality of [{result}]?\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f"用一段话非常简要概括下面的文字\n"
                q["Instruction"] = f"Summarize the text briefly in a single paragraph.\n"
                # q["Input"] = result + "\n- 选择各功能的初始化和资源销毁回收相关函数，这些函数是libfuzzer测试功能所必须的函数。\n - 从内存读取数据的初始化函数要优先于从文件读取数据的初始化函数。\n - 一些资源或者功能初始化函数，可能看上去比较简单，但是也是libfuzzer构造所必须的，需要进行选择。"
                q["Input"] = result + "\n- Select the initialization and resource destruction/recycling functions that are essential for the libfuzzer testing functionality.\n - The initialization function for reading data from memory should be prioritized over the initialization function for reading data from files.\n - Some resource or functionality initialization functions may seem simple, but they are also necessary for the construction of libfuzzer and should be selected accordingly."
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)

                # q["Instruction"] = f" 根据下面的描述，用一段话非常概要的描述下面的文字\n"
                q["Instruction"] = f" Based on the description below, provide a very concise summary of the text in a single sentence.\n"
                q["Input"] = result
                readme_prompt = prompt.gen_prompt(q)
                result = run_llm_custom(readme_prompt)
                # result = deepseek.run(readme_prompt)
                print(f"readme result\n{result}")
                print("="*20)
                self.readme = result


