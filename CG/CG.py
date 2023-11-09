import sys
sys.path.append('../AST')
from AST import *

def get_node_type(node):
    node_type = [node.type]
    if node.child_count == 0:
        return node_type
    for child in node.children:
        node_type.extend(get_node_type(child))
    return node_type

def get_call_nodes(node):
    # 找到node节点中的所有函数调用节点并返回
    call_nodes = []
    if node.child_count == 0:
        return call_nodes
    for child in node.children:
        if child.type == 'call_expression':
            call_nodes.append(child)
        else:
            call_nodes.extend(get_call_nodes(child))
    return call_nodes

func_set = {}
def get_func_info(node):
    func_name = text(node.child_by_field_name('declarator').child_by_field_name('declarator'))
    func_type = text(node.child_by_field_name('type'))
    func_parametre = text(node.child_by_field_name('declarator').child_by_field_name('parameters'))
    if func_name in func_set:
        func_id = func_set[func_name]
    else:
        func_id = len(func_set)
        func_set[func_name] = func_id
    return {"name": func_name, "type": func_type, "parametre": func_parametre, "id": func_id}

def create_cg(root_node):
    CG = []
    func_def_nodes = {}     # func_name -> {node, type, parametre}
    for child in root_node.children:
        if child.type == 'function_definition':
            func_info = get_func_info(child)
            func_def_nodes[func_info['name']] = child
    for node in func_def_nodes:
        func_node = func_def_nodes[node]
        call_nodes = get_call_nodes(func_node)
        cg_call_nodes = []
        for call_node in call_nodes:
            call_name = text(call_node.child_by_field_name('function'))
            if call_name in func_def_nodes:
                cg_call_nodes.append(get_func_info(func_def_nodes[call_name])['id'])
        CG.append((get_func_info(func_node), cg_call_nodes))
    return CG

class CG(AST):
    def see_cg(self, code, filename='CG', pdf=True, view=False):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        CG = create_cg(root_node)
        input(CG)
        dot = Digraph(comment=filename)
        with open(filename+'.txt', 'w') as f:
            for node in CG:
                dot.node(str(node[0]['id']), shape='rectangle', label=node[0]['name'])
                for call_node in node[1]:
                    dot.edge(str(node[0]['id']), str(call_node))
                f.write(str(node) + '\n')
        if pdf:
            dot.render(filename, view=view, cleanup=True)
            

if __name__ == '__main__':
    code = '''
    int foo(int a);
    int foo(int a){
        return a;
    }
    int bar(int b){
        foo(b);
        for (int i=0;i<2;i++)
            bar(b);
        return b;
    }
    int main(){
        foo(a);
        bar(b);
    }
    '''
    cg = CG('c')
    # cg.see_tree(code, view=True)
    cg.see_cg(code, view=True)
