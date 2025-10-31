import os
from Data import *
from Analysis import *
import networkx as nx
# source_file = "/root/fuzz_bin/exiv2/include/exiv2/xmp_exiv2.hpp"
# test_c = NormalFile(source_file,'cpp')
# # show_all_node(test_c.root_node)
# # print(test_c.is_test_file())
# test_c.get_all_functions()
# for one_func in test_c.func_list:
#     print(one_func.name)
#     print(one_func.body)
#     # show_all_node(one_func.node)
#     func_list = function_definition_get_namespaces(one_func.node)
#     print(func_list)
#     break

# def find_func_by_caller(all_funcs,one_call):
#     for one_func in all_funcs:
#         if one_call.func_name == one_func.name:
#             if not one_func.class_list and not one_call.name_space_list:
#                 return one_func
#             else:
#                 if not one_func.class_list or not one_call.name_space_list:
#                     return None
#                 else:
#                     if one_func.class_list[-1] == one_call.name_space_list[-1]:
#                         return one_func
#     return None

# target_folder = "C:/Code/exiv2"

# test_project = CXXProject(target_folder)
# test_project.process()
# G = nx.DiGraph()
# print("Gen network")
# for one_func in  test_project.all_funcs:
#     # print(one_func.name,one_func.class_list)
#     if one_func.call_list:
#         for one_call in one_func.call_list:
#             tmp_func = find_func_by_caller(test_project.all_funcs,one_call)
#             if tmp_func:
#                 G.add_edge(one_func,tmp_func)


# weakly_connected_subgraphs = list(nx.weakly_connected_components(G))
# print(f"互不相通的子图数量: {len(weakly_connected_subgraphs)}")

# for n in G.nodes():
#     ancestors = nx.ancestors(G, n)
#     if len(ancestors) == 0:
#         if len(list(G.successors(n))) > 0:
#             print(f"{n.name} {n.class_list} {len(list(G.successors(n)))}")

target_floder = "/root/test/test/j40-main"
target_floder = "D:/work/selector-test/test/j40-main"
test_project = CXXProject(target_floder)
# test_project.parse_readme_file()
test_project.process()
print(test_project.readme)


# 根据下面的readme，简要描述工程实现的核心功能：
# 根据下面描述，简要概括一下工程实现的核心功能：
# 根据下面描述，用一句话概括工程的核心功能:
# "根据下面的描述，用一句话且用尽可能少的文字总结下面文字中工程的核心功能\n"
# 如果要对实现{}功能的工程编写libfuzzer，都需要测试程序哪些功能的函数？
# 简要概括下面的文字：
# 根据下面的描述，用一段话非常概要的描述下面的文字
# 根据下面的总体要求 which
 
