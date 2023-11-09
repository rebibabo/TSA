def get_node_info_ast(node, is_leaf=False):
    if node.type == ':':
        info = 'colon' + str(node.start_byte) + ',' + str(node.end_byte)
    elif is_leaf:
        info = node.text.decode('utf-8').replace(':', 'colon') + str(node.start_byte) + ',' + str(node.end_byte)
    else:
        info = str(node.type).replace(':', 'colon') + str(node.start_byte) + ',' + str(node.end_byte)
    return info

def create_ast_tree(dot, node):
    node_info = get_node_info_ast(node)
    dot.node(node_info, shape='rectangle', label=node.type)
    if not node.child_count:
        leaf_info = get_node_info_ast(node, is_leaf=True)
        dot.node(leaf_info, shape='ellipse', label=node.text.decode('utf-8'))
        if node.text.decode('utf-8') != node.type:
            dot.edge(node_info, leaf_info)
        return
    for child in node.children:
        create_ast_tree(dot, child)
        child_info = get_node_info_ast(child)
        dot.edge(node_info, child_info)
    return id

def get_tree_root(root_node, index_to_code):
    # 遍历节点，保存节点的start_point和end_point以及节点到dict中
    if root_node.child_count == 0:
        return 
    for child in root_node.children:
        index = (child.start_point, child.end_point)
        index_to_code[index] = child
        get_tree_root(child, index_to_code)

python_id_type = ['identifier', 'string', 'integer', 'true', 'false', 'null', 'none', 'float', 'list', 'tuple']
java_id_type = ['identifier', 'decimal_integer_literal', 'hex_integer_literal', 'octal_integer_literal', 'binary_integer_literal', \
    'decimal_floating_point_literal', 'hex_floating_point_literal', 'true', 'false', 'null', 'character_literal', 'string_literal', \
    'text_block_literal', 'list_literal', 'tuple_literal']
c_id_type = ['identifier', 'number_literal', 'true', 'false', 'null']
def tree_to_index_node(root_node):
    # 遍历树，返回dict，key为节点的index，value为节点的index以及text
    index_to_code = {}
    get_tree_root(root_node, index_to_code)
    index = 0
    for key in index_to_code:   # 每遇到一个变量或者常量，index加一
        if index_to_code[key].type in python_id_type + java_id_type + c_id_type:
            index += 1
        index_to_code[key] = (index, index_to_code[key].text.decode('utf-8'))
    return index_to_code