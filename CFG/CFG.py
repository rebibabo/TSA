import sys
sys.path.append('../AST')
from AST import *
import html

node_set = {}
def get_node_type(node):
    node_type = [node.type]
    if node.child_count == 0:
        return node_type
    for child in node.children:
        node_type.extend(get_node_type(child))
    return node_type

def get_node_info(node, leaf_type=False):
    # 返回节点的信息，包括节点内容node，属性type，唯一标志id和是否是分支is_branch
    if leaf_type == True:
        node_types = get_node_type(node)
    else:
        node_types = ""
    # return {"type": node.type, "start_byte": node.start_byte, "end_byte": node.end_byte, "start_point": node.start_point, "end_point": node.end_point, "text": text(node), "node_types": node_types}
    node_info = (node.start_byte, node.end_byte)
    if node_info in node_set:
        id = node_set[node_info]
    else:
        id = len(node_set)
        node_set[node_info] = id
    if node.type == 'function_definition':
        return {"node": text(node.children[1].children[0]), "type": node.type, "id": id, "is_branch": False, "line": node.start_point[0]}
    elif node.type in ['while_statement', 'for_statement', 'switch_statement']:
        body = node.child_by_field_name('body')
        node_text = ''
        for child in node.children:
            if child == body:
                break
            node_text += text(child)
        return {"node": node_text, "type": node.type, "id": id, "is_branch": False if node.type == 'switch_statement' else True, "line": node.start_point[0]}
    elif node.type == 'if_statement':
        consequence = node.child_by_field_name('consequence')
        node_text = ''
        for child in node.children:
            if child == consequence:
                break
            node_text += text(child)
        return {"node": node_text, "type": node.type, "id": id, "is_branch": True, "line": node.start_point[0]}
    elif node.type == 'case_statement':
        node_text = ''
        for child in node.children:
            if child.type == ':':
                break
            node_text += ' ' + text(child)
        return {"node": node_text, "type": node.type, "id": id, "is_branch": True, "line": node.start_point[0]}
    else:
        return {"node": text(node), "type": node.type, "id": id, "is_branch": False, "line": node.start_point[0]}

def get_break_continue_node(node):
    # 找到node节点循环中的所有break和continue节点并返回
    break_nodes, continue_nodes = [], []
    for child in node.children:
        if child.type == 'break_statement':
            break_nodes.append(child)
        elif child.type == 'continue_statement':
            continue_nodes.append(child)
        elif child.type not in ['for_statement', 'while_statement']:
            b_node, c_nodes = get_break_continue_node(child)
            break_nodes.extend(b_node)
            continue_nodes.extend(c_nodes)
    return break_nodes, continue_nodes

def get_edge(in_nodes):
    # 输入入节点，返回入边的列表，边为(parent_id, label)
    edge = []     
    for in_node in in_nodes:    
        parent, label = in_node
        parent_id = parent['id']
        edge.append((parent_id, label))
    return edge

def create_cfg_tree(node, in_nodes=[()]):
    # 输入当前节点，以及入节点，入节点为(node_info, edge_label)的列表，node_info['id']唯一确定一个节点，edge_label为边的标签
    if node.type == text(node) or in_nodes == []:   # 如果in_nodes为空，说明没有入节点，跳过
        return [], in_nodes
    if node.type == 'function_definition':      # 如果节点是函数，则创建函数节点，并且递归遍历函数的compound_statement
        body = node.child_by_field_name('body')
        node_info = get_node_info(node)
        CFG, _ = create_cfg_tree(body, [(node_info, '')])
        return CFG + [(node_info, [])], []
    elif node.type == 'compound_statement':     # 如果是复合语句，则递归遍历复合语句的每一条statement
        CFG = []
        for child in node.children:
            cfg, out_nodes = create_cfg_tree(child, in_nodes)
            CFG.extend(cfg)
            in_nodes = out_nodes
        return CFG, in_nodes
    elif node.type not in ['if_statement', 'while_statement', 'for_statement', 'switch_statement', 'case_statement', 'translation_unit']:  # 如果是普通的语句
        edge = get_edge(in_nodes)
        node_info = get_node_info(node)
        in_nodes = [(node_info, '')]
        if node.type in ['return_statement', 'break_statement', 'continue_statement']:  # return，break，continue语句没有出节点
            return [(node_info, edge)], []
        else:
            return [(node_info, edge)], in_nodes
    elif node.type == 'if_statement':   # if语句
        CFG = []
        edge = get_edge(in_nodes)
        node_info = get_node_info(node)
        CFG.append((node_info, edge))
        body = node.child_by_field_name('consequence')  # 获取if的主体部分
        cfg, out_nodes = create_cfg_tree(body, [(node_info, 'Y')])
        CFG.extend(cfg)
        alternate = node.child_by_field_name('alternative') # 获取else的主体部分，可能是else，也可能是else if
        if alternate:       # if else 或者 if else if
            body = alternate.children[1]
            cfg, al_out_nodes = create_cfg_tree(body, [(node_info, 'N')])
            CFG.extend(cfg)
            return CFG, out_nodes + al_out_nodes
        else:               # 只有if
            return CFG, out_nodes + [(node_info, 'N')]
    elif node.type in ['for_statement', 'while_statement']:     # for和while循环
        CFG = []
        edge = get_edge(in_nodes)
        node_info = get_node_info(node)
        CFG.append((node_info, edge))
        body = node.child_by_field_name('body')     # 获取循环主体
        cfg, out_nodes = create_cfg_tree(body, [(node_info, 'Y')])
        CFG.extend(cfg)
        for out_node in out_nodes:  # 将循环主体的出节点与循环的开始节点相连
            parent, label = out_node
            parent_id = parent['id']
            CFG.append((node_info, [(parent_id, label)]))
        break_nodes, continue_nodes = get_break_continue_node(node)     # 求得循环内的break和continue节点
        out_nodes = [(node_info, 'N')]      # 循环体的出节点开始节点，条件为N
        for break_node in break_nodes:      
            out_nodes.append((get_node_info(break_node), ''))   # 将break节点添加到out_nodes中
        for continue_node in continue_nodes:
            CFG.append((node_info, [(get_node_info(continue_node)['id'], '')]))     # 将continue节点连接到循环的开始节点
        return CFG, out_nodes
    elif node.type == 'switch_statement':   # switch语句
        CFG = []
        edge = get_edge(in_nodes)
        node_info = get_node_info(node)
        CFG.append((node_info, edge))
        body = node.child_by_field_name('body')     # 获取switch的主体部分
        cfg, out_nodes = create_cfg_tree(body, [(node_info, '')])   # 递归遍历case语句
        CFG.extend(cfg)
        break_nodes, _ = get_break_continue_node(node)      # 将break语句添加到out_nodes当中
        for break_node in break_nodes:
            out_nodes.append((get_node_info(break_node), ''))
        return CFG, out_nodes
    elif node.type == 'case_statement':     # case语句
        CFG = []
        edge = get_edge(in_nodes)
        node_info = get_node_info(node)
        CFG.append((node_info, edge))
        if node.children[0].type == 'case':     # 如果是case语句
            in_nodes = [(node_info, 'Y')]
            for child in node.children[3:]:
                cfg, out_nodes = create_cfg_tree(child, in_nodes)
                CFG.extend(cfg)
                in_nodes = out_nodes
            return CFG, in_nodes + [(node_info, 'N')]
        else:   # default
            in_nodes = [(node_info, '')]
            for child in node.children[2:]:
                cfg, out_nodes = create_cfg_tree(child, in_nodes)
                CFG.extend(cfg)
                in_nodes = out_nodes
            return CFG, in_nodes
    else:
        CFG = []
        for child in node.children:
            if child.type == 'function_definition': # 获得每一个函数的CFG图
                cfg, out_nodes = create_cfg_tree(child, in_nodes)
                CFG.append(cfg)
        return CFG, in_nodes

class CFG(AST):
    def see_cfg(self, code, filename='CFG', pdf=True, view=False):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        cfg, _ = create_cfg_tree(root_node)
        dot = Digraph(comment=filename, strict=True)
        with open(filename + '.txt', 'w') as f:
            for func_cfg in cfg:
                for node in func_cfg:
                    label = f"<({node[0]['type']}, {html.escape(node[0]['node'])})<SUB>{node[0]['line']}</SUB>>"
                    if node[0]['is_branch']:
                        dot.node(str(node[0]['id']), shape='diamond', label=label)
                    elif node[0]['type'] == 'function_definition':
                        dot.node(str(node[0]['id']), label=label)
                    else:
                        dot.node(str(node[0]['id']), shape='rectangle', label=label)
                    for edge in node[1]:
                        dot.edge(str(edge[0]), str(node[0]['id']), label=edge[1])
                    f.write(str(node) + '\n')
        if pdf:
            dot.render(filename, view=view, cleanup=True)
        return cfg

    def init_graph(self, cfg):
        # 输入CFG，返回反向CFG图，由节点V，边E和头节点r组成，其中添加了一条exit节点，将return语句和函数定义节点连接到exit节点
        Graph = []
        func_num = 0
        for func_cfg in cfg:
            func_num += 1
            V = set([-func_num])     # 添加一条exit边，为-1, -2, ...
            E = {}
            for node, prevs in func_cfg:
                V.add(node['id'])
                if node['type'] == 'function_definition':
                    E[-func_num].append(node['id'])
                elif node['type'] == 'return_statement':
                    E.setdefault(-func_num, [])
                    E[-func_num].append(node['id'])
                for prev in prevs:
                    E.setdefault(node['id'], [])
                    E[node['id']].append(prev[0])
            Graph.append((V, E, -func_num))
        return Graph

if __name__ == '__main__':
    code = '''
    int main(){
        switch (a){
            case 1:
                a+=1;
                break;
            case 2:
                a+=2;
        }
        return 0;
    }

    int cmp(int a, int b){
        if (a>b)
            return a;
        else
            return b;
    }
    '''
    cfg = CFG('c')
    # cfg.see_tree(code, view=True)
    cfg.see_cfg(code, view=True)
