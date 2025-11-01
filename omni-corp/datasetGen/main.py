import os
import argparse
import sys
from Data import *
from transformers import AutoTokenizer
import json
import time

model_path = "D:/models/codeqwen"
model_path = "/root/llama/qwen1.5"
# model_path = "D:/codeqwen"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='包含json文件的文件夹')
    parser.add_argument("-o","--output",type=str,help='输出数据库的文件夹')
    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    checked_file_path = set()
    base_path_set = set()
    for file_name in os.listdir(input_dir):
        if file_name in checked_file_path:
            continue
    for file_name in os.listdir(input_dir):
        if file_name in checked_file_path:
            continue
        full_name = os.path.join(input_dir,file_name)
        if "-funcs_selector.json" in file_name:
            print(f"Analyzing {full_name}")
            target_file_name = file_name.replace("-funcs_selector.json","")
            target_file_path = os.path.join(output_dir,target_file_name+"-Selector.json")
            one_selector = SelectorGen(full_name,tokenizer)
            one_selector.process()
            if not one_selector.func_list:
                continue
            one_selector.save_to_json(target_file_path)
            checked_file_path.add(file_name)
        elif "-generator.json" in file_name:
            print(f"Analyzing {full_name}")
            target_file_name = file_name.replace("-generator.json","")
            target_file_path = os.path.join(output_dir,target_file_name+"-Generator.json")
            one_generator = GeneratorGen(full_name,tokenizer)
            one_generator.process()
            if not one_generator.qa_list:
                continue
            one_generator.save_to_json(target_file_path)
            checked_file_path.add(file_name)
