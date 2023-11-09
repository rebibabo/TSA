from tree_sitter import Language, Parser
from DFG_python import DFG_python
from DFG_java import DFG_java
from DFG_c import DFG_c
from graphviz import Digraph
from utils import *
import os
    
class SCTS:
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
            os.system(f'rm -rf ./tree-sitter-{language}')
        LANGUAGE = Language(f'./build/{language}-languages.so', language)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser

    def DFG(self, code):
        root_node = self.parser.parse(bytes(code, encoding='utf-8')).root_node
        index_to_code = tree_to_index_node(root_node)
        if self.language == 'python':
            DFG, _ = DFG_python(root_node, index_to_code, {})
        elif self.language == 'java':
            DFG, _ = DFG_java(root_node, index_to_code, {})
        elif self.language == 'c':
            DFG, _ = DFG_c(root_node, index_to_code, {})
        dot = Digraph(comment='DFG', strict=True) 
        for each in DFG:
            dot.node(str(each[1]), shape='rectangle', label=f"<{str(each[0])}<SUB>{each[1]}</SUB>>")
            if len(each[4]) > 0:
                for i in range(len(each[4])):
                    if each[4][i] != each[1]:
                        dot.edge(str(each[4][i]), str(each[1]), label=each[2])
        dot.render('DFG', view=True)
        return DFG

    def see_tree(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='AST Tree', strict=True)
        create_ast_tree(dot, root_node)
        dot.render('ast_tree', view=True)

if __name__ == '__main__':
    code = '''
    int main(){
        int a = 1;
        int b = 2;
        int c = a + b;
        while(i<10){
            i++;
        }
        return c;
    }
    '''
    scts = SCTS('c')
    # scts.see_tree(code)
    scts.DFG(code)