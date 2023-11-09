import sys
import copy
sys.path.append('../CFG')
from CFG import *
from graphviz import Graph

class Tree:
    def __init__(self, V, children, root):  # 输入节点集合，children为字典，key为节点，value为子节点列表，根节点
        self.vertex = V
        self.children = children
        self.root = root
        self.parent = {}
        for node in children:   # 初始化parent字典
            for each in children[node]:
                self.parent[each] = node
        self.parent[root] = root
        for v in V:
            if v not in self.children:
                self.children[v] = []
        self.depth = self.get_nodes_depth(root, {root:0})    

    def get_nodes_depth(self, root, depth):
        # 递归计算每个节点的深度
        for child in self.children[root]:
            depth[child] = depth[root] + 1
            depth = self.get_nodes_depth(child, depth)
        return depth

    def get_lca(self, a, b):
        # 计算a,b的最近公共祖先
        if self.depth[a] > self.depth[b]:
            diff = self.depth[a] - self.depth[b]
            while diff > 0:
                a = self.parent[a]
                diff -= 1
        elif self.depth[a] < self.depth[b]:
            diff = self.depth[b] - self.depth[a]
            while diff > 0:
                b = self.parent[b]
                diff -= 1
        while a != b:
            a = self.parent[a]
            b = self.parent[b]
        return a

    def reset_by_parent(self):
        # 根据parent字典重置children字典
        self.children = {v:[] for v in self.vertex}
        for node in self.parent:
            if node != self.parent[node]:
                self.children[self.parent[node]].append(node)

    def see_tree(self):
        dot = Graph(comment='Tree')
        for node in self.vertex:
            if node == self.root:
                dot.node(str(node), shape='rectangle', label='r')
            else:
                dot.node(str(node), shape='rectangle', label=str(node))
        for node in self.children:
            for child in self.children[node]:
                dot.edge(str(node), str(child))
        dot.view()


class CDG(CFG):
    def see_graph(self, code):
        # 可视化逆向CFG
        cfg = self.see_cfg(code)
        graphs = self.init_graph(cfg)
        dot = Digraph(comment='Graph')
        for graph in graphs:
            V, E, r = graph
            for v in V:
                if v == r:
                    dot.node(str(v), shape='rectangle', label='r')
                elif v < 0:
                    dot.node(str(v), shape='rectangle', label='exit')
                else:
                    dot.node(str(v), shape='rectangle', label=str(v))
            for e in E:
                for v in E[e]:
                    dot.edge(str(e), str(v))
        dot.view()

    def get_subTree(self, graph):
        # 按照广度优先遍历，找出一个子树
        V, E, r = graph
        visited = {v:False for v in V}
        queue = [r]
        visited[r] = True
        subTree = {}
        while queue:
            node = queue.pop()
            if node not in E:
                continue
            for v in E[node]:
                if not visited[v]:
                    queue.append(v)
                    visited[v] = True
                    subTree.setdefault(node, [])
                    subTree[node].append(v)
        return subTree
        
    def get_prev(self, graphs):
        # 计算每个节点的前驱节点
        prev = {}
        for graph in graphs:
            V, E, r = graph
            for e in E:
                for v in E[e]:
                    prev.setdefault(v, [])
                    prev[v].append(e)
            prev[r] = []
        return prev

    def post_dominator_tree(self, graphs, prev):
        # 生成后支配树
        PDT = []
        for graph in graphs:    # 遍历每一个函数的CFG
            V, E, r = graph
            subTree = self.get_subTree(graph)   # 找出一个子树
            tree = Tree(V, subTree, r)
            changed = True
            while changed:
                changed = False
                for v in V: # dominator tree算法
                    if v != r:
                        for u in prev[v]:
                            parent_v = tree.parent[v]
                            if u != parent_v and parent_v != tree.get_lca(u, parent_v):
                                tree.parent[v] = tree.get_lca(u, parent_v)
                                changed = True
            tree.reset_by_parent()  # 根据parent字典重置children字典
            tree.see_tree()
            PDT.append(tree)
        return PDT

    def dominance_frontier(self, code):
        # 代码，返回CFG、后支配树和支配边界
        cfg = self.see_cfg(code)
        graphs = self.init_graph(cfg)  # 将CFG转换为更抽象的图
        prev = self.get_prev(graphs)  # 计算每个节点的前驱节点
        PDT = self.post_dominator_tree(graphs, prev)  # 输入CFG，输出后支配树
        DF = []
        for graph, tree in zip(graphs, PDT):
            V, E, r = graph
            DF.append({v:[] for v in V})
            for v in V:
                if len(prev[v]) > 1:
                    for p in prev[v]:
                        runner = p
                        while runner != tree.parent[v]:
                            DF[-1][runner].append(v)
                            runner = tree.parent[runner]
        return cfg, DF

    def see_cdg(self, code, filename='CDG', pdf=True, view=False):
        # 输出CDG
        cfg, DF = self.dominance_frontier(code)
        vertex = {}
        CDG = []
        for func_cfg in cfg:
            for node, _ in func_cfg:
                vertex[node['id']] = node
        dot = Digraph(comment=filename)
        with open(filename+'.txt', 'w') as f:
            for df in DF:
                for v in df:
                    if v >= 0:
                        node = vertex[v]
                        edges = []
                        label = f"<({node['type']}, {html.escape(node['node'])})<SUB>{node['line']}</SUB>>"
                        if node['is_branch']:
                            dot.node(str(node['id']), shape='diamond', label=label)
                        elif node['type'] == 'function_definition':
                            dot.node(str(node['id']), label=label)
                        else:
                            dot.node(str(node['id']), shape='rectangle', label=label)
                        for u in df[v]:
                            dot.edge(str(u), str(v))
                            edges.append(u)
                        f.write(f"({node}, {edges})\n")
                        CDG.append((node, edges))
        if pdf:
            dot.render(filename, view=view, cleanup=True)
        return CDG

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
    cdg = CDG('c')
    # cdg.see_cfg(code, view=True)
    cdg.see_cdg(code, view=True)
