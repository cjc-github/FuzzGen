import os
import argparse
from Analysis import *
import sys
import Data


cpp_lib_path = "C:/Code/tree-sitter-cpp/build/my-cpp-language.dll"
# lib_path = "C:/Code/tree-sitter-cpp/build/cpp.dll"
cpp_lang = "cpp"


c_lib_path = "C:/Code/tree-sitter-c/build/my-c-language.dll"
# lib_path = "C:/Code/tree-sitter-cpp/build/cpp.dll"
c_lang = "c"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='脚本的用法')

    parser.add_argument('-i',"--input" ,type=str, help='包含所有工程文件夹的文件夹')
    parser.add_argument("-o","--output",type=str,help='输出数据库的文件夹')
    parser.add_argument("-c","--config",type=str,help= "对该工程的文件夹读取配置文件")
    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output