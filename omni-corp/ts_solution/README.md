# Libfuzzer构造函数提取工具

## 功能

用来解析一个文件夹下的包含libfuzzer的C/C++源码功能，提取函数，并按照是否被libfuzzer调用分为两类，程序将这两类函数按照一定输出规则分别输出到指定文件夹下，构成数据集，为下一步的prompt构造提供基础。

## 环境准备

本程序是基于tree-sitter的python 工程，需要先安装tree-sitter插件。

```
pip install tree-sitter
```

然后下载对应的C++解析（C语言一样可以通过C++插件来解析）
```
git clone https://github.com/tree-sitter/tree-sitter-cpp.git
```
在文件夹内建立`build.py`
```
cd tree-sitter-cpp
touch build.py
```
在build.py中输入如下命令，编译相关脚本。
```
from tree_sitter import Language, Parser

# 加载语言库
# Language.build_library(
#   # 存放生成的库文件
#   'build/cpp.dll',
#   # 指定语言库的路径
#   ['C:/Code/tree-sitter-cpp']
# )

# 加载语言库
Language.build_library(
  # 存放生成的库文件
  'build/cpp.so',
  # 指定语言库的路径
  ['/mnt/c/Code/tree-sitter-cpp']
)
```
运行`build.py`编译tree-sitter插件。
```
python build.py
```

## 程序使用方法

运行`main.py`,需要两个参数，`-i`参数后是包含各个C/C++源码工程文件夹的文件夹，`-o`参数后是存放输出文件的文件夹。
```
python main.py -i {input_floder} -o {output_data_floder}
```
其中输入文件夹的文件结构应该如下：
```
- input
- - cxx_project_floder1
- - cxx_project_floder2
- - cxx_project_floder3
- - cxx_project_floder4
...
```
输出文件夹的文件结构如下：
```
- output
- - cxx_project1_0.txt
- - cxx_project1_1.txt
- - cxx_project2_0.txt
- - cxx_project2_1.txt
- - cxx_project3_0.txt
- - cxx_project3_1.txt
...
```

## 输出数据库结构

对于label_0和label_1的函数，每个函数按照下面格式进行输出:
```
{function body}
/*-+==+-*/
{Include path}
/*-+==+-*/
{return type}
/*-+==+-*/
{Parm 1 type}
/*-+==+-*/
{Parm 2 type}
/*-+==+-*/
...
/*-+==+-*/
```
各个主要模块用`/*-+==+-*/`符号进行分割。函数和函数之间用`/////`分割。