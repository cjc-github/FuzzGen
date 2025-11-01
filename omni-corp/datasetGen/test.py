import os
from Data import *
import json
from transformers import AutoTokenizer
model_path = "D:/models/codeqwen"
model_path = "D:/codeqwen"
target_file = 'D:/rawdata/output/4291-v1.2-funcs_selector.json'

if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # file_path = "../exiv2-fuzz-read-print-write-generator.json"
    one_selector = SelectorGen(target_file,tokenizer)
    print('begin process')
    one_selector.process()
    one_selector.save_to_json("../Generator.json")

    # with open(target_file,'r') as f:
    #     data = json.load(f)

    # for one in data:
    #     print(one.keys())
    # print(len(data))