import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser



def iterate_tree(root_node):
    stack = [root_node]
    return_list = []
    while stack:
        node = stack.pop()
        return_list.append(node)
        # 在这里处理节点的逻辑，比如打印节点的类型、内容等
        # print("Node Type:", node.type)
        # print("Node Content:", node.utf8_content)
        # 将子节点添加到堆栈中，以便迭代处理
        for child in node.children:
            stack.append(child)
    return return_list
if __name__ == "__main__":
    CPP_LANGUAGE = Language(tscpp.language())
    parser = Parser(CPP_LANGUAGE)
    C_LANGUAGE = Language(tsc.language())
    parser = Parser(C_LANGUAGE)

    code = '''
    const A::B::C d = QQQ->d();

    extern A::B::C d = QQQ->d();

    A::B::C *d = QQQ->d();
    A *bcd(a,b);

    const static extern A::B::C *d = QQQ->d();
    const static extern A *bcd(a,b);

    Value(cde()->w()).Count(abc()->d);

    auto const g = cista::deserialize<graph, cista::mode::DEEP_CHECK>(b);

    auto const g = bcd.abc->deserialize<graph, cista::mode::DEEP_CHECK>(b);
    '''
    code = bytearray(code,encoding='utf-8')
    tree = parser.parse(code)


    root_node = tree.root_node
    ele_list = iterate_tree(root_node)
    for node in ele_list:
        print(f"{node.type},{node.text}")