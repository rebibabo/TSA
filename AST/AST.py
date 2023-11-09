from tree_sitter import Parser, Language
from graphviz import Digraph
import os

text = lambda node: node.text.decode('utf-8')

# 递归遍历AST树，输入root_node以及i,i初始值为0，每当遍历到一个节点，i就加一， 返回列表，列表的每一个元素为(node, i)
def traverse_tree(node, i=[0], parent_i=[0]):     # python递归函数想要修改函数参数的值，只能通过列表等方式
    node_info = {"type": node.type, "start_byte": node.start_byte, "end_byte": node.end_byte, "start_point": node.start_point, "end_point": node.end_point, 'is_leaf': False, "text": text(node)}
    result = [(i[0], parent_i[0], node_info)]
    if not node.children: 
        i[0] += 1
        node_info['is_leaf'] = True
        return result
    parent_i = i.copy()
    for child in node.children:
        i[0] += 1
        result += traverse_tree(child, i, parent_i)
    return result

def tokenize_help(node, tokens):
    # 遍历整个AST树，返回符合func的节点列表results
    if not node.children:
        tokens.append(text(node))
        return
    for n in node.children:
        tokenize_help(n, tokens)

class AST:
    def __init__(self, language):
        self.language = language
        if not os.path.exists(f'./build/{language}-languages.so'):
            if not os.path.exists(f'./tree-sitter-{language}'):
                os.system(f'git clone https://github.com/tree-sitter/tree-sitter-{language}')
            Language.build_library(
                f'./build/{language}-languages.so',
                [
                    f'./tree-sitter-{language}',
                ]
            )
        LANGUAGE = Language(f'./build/{language}-languages.so', language)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser

    def see_tree(self, code, filename='ast_tree', pdf=True, view=False):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='AST Tree', strict=True)
        nodes = traverse_tree(root_node)
        with open(filename + '.txt', 'w') as f:
            for node in nodes:
                dot.node(str(node[0]), shape='rectangle', label=node[2]['type'])
                if node[0] != 0:
                    dot.edge(str(node[1]), str(node[0]))
                if node[2]['is_leaf']:
                    dot.node(str(-node[0]), shape='ellipse', label=node[2]['text'])
                    dot.edge(str(node[0]), str(-node[0]))
                f.write(str(node) + '\n')
        if pdf:
            dot.render(filename, view=view, cleanup=True)

    def tokenize(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        tokens = []
        tokenize_help(root_node, tokens)
        return tokens

if __name__ == '__main__':
    code = '''
    int main(){
        int abc = 1;
        int b = 2;
        int c = a + b;
        while(i<10){
            i++;
        }
    }
    '''
    ast = AST('c')
    print(ast.tokenize(code))
    ast.see_tree(code, view=True)