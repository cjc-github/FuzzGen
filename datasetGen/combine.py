import json
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')
    parser.add_argument('-i',"--input" ,type=str, help='包含json文件的文件夹')
    parser.add_argument("-o","--output",type=str,help='输出数据库的文件夹')
    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output

    selecotor_list = []
    generator_list = []

    for file_name in os.listdir(input_dir):
        full_file_name = os.path.join(input_dir,file_name)
        if "-Selector.json" in file_name:
            with open(full_file_name,'r') as f:
                tmp_list = json.load(f)
            selecotor_list += tmp_list
        elif '-Generator.json' in file_name:
            with open(full_file_name,'r') as f:
                tmp_list = json.load(f)
            generator_list += tmp_list

    output_s_path = os.path.join(output_dir,'s.json')
    output_g_path = os.path.join(output_dir,'g.json')
    print(f"selector len is {len(selecotor_list)}")
    print(f"generator len is {len(generator_list)}")
    with open(output_s_path,'w') as f:
        json.dump(selecotor_list,f)
    with open(output_g_path,'w') as f:
        json.dump(generator_list,f)