parent = {7:4, 9:8, 8:5, 4:2, 5:2, 2:1, 1:0, 3:1, 6:3, 0:0}
children = {1:[2,3], 2:[4,5], 3:[6], 4:[7], 5:[8], 6:[], 7:[], 8:[9], 9:[]}

def get_nodes_depth(children, root, depth):
    for child in children[root]:
        depth[child] = depth[root] + 1
        get_nodes_depth(children, child, depth)
    return depth

def get_lca(children, parent, a, b):
    depth = get_nodes_depth(children, 1, {1:0})
    if depth[a] > depth[b]:
        diff = depth[a] - depth[b]
        while diff > 0:
            a = parent[a]
            diff -= 1
    elif depth[a] < depth[b]:
        diff = depth[b] - depth[a]
        while diff > 0:
            b = parent[b]
            diff -= 1
    while a != b:
        a = parent[a]
        b = parent[b]
    return a

print(get_lca(children, parent, 7, 6))
