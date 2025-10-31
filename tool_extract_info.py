from Core.api import *
import os
import sys
from promptRUN import *
import pandas as pd

def get_readme_file_content(target_dir):
    for file_name in os.listdir(target_dir): 
        # readme 可能是大写，可能是小写，需要把filename全部变成小写
        lower_file_name = file_name.lower()
        if "readme" in lower_file_name:
            full_path = os.path.join(target_dir,file_name)
            if os.path.isdir(full_path):
                continue
            with open(full_path,'r') as f:
                return f.read()
    return ""

target_floder = "/root/raw_data/tmp_fuzzer_data/"
floder_list = []
content_list = []
ins = """
根据下面readme，用一句话总结工程的功能。总结完毕后，分析刚刚的输入是否是最简，然后再输出最简的功能描述。
下面是输出示例：
{
    "function_summary": "功能总结",
    "analyze": "分析输入是否最简",
    "final_output": "最简功能描述"
}

"""
for floder_name in os.listdir(target_floder):
    print(floder_name)
    full_path = os.path.join(target_floder,floder_name)
    readme_content = get_readme_file_content(full_path)
    floder_list.append(floder_name)
    if readme_content == "":
        content_list.append("")
        continue
    prompt_str = f"{ins}\n{readme_content}"
    result = run_llm_custom(prompt_str)
    result_dict = get_return_dict(result,["function_summary","analyze","final_output"])
    print(result_dict)
    if result_dict:
        content_list.append(result_dict['final_output'])
    else:
        content_list.append("")

df1 = pd.DataFrame(floder_list)
df2 = pd.DataFrame(content_list)

with pd.ExcelWriter("output.xlsx") as writer:
    df1.to_excel(writer, sheet_name="Sheet1", index=False)
    df2.to_excel(writer, sheet_name="Sheet2", index=False)


    
    