def tree_to_variable_index(root_node,index_to_code):
    # 遍历树，找到所有的变量名
    if (len(root_node.children)==0 or root_node.type=='string') and root_node.type!='comment':
        index=(root_node.start_point,root_node.end_point)
        _,code=index_to_code[index]
        if root_node.type!=code:
            return [(root_node.start_point,root_node.end_point)]
        else:   # =/</>这些tree-sitter解析出来的text和type一样的，忽略
            return []
    else:
        code_tokens=[]
        for child in root_node.children:
            code_tokens+=tree_to_variable_index(child,index_to_code)
        return code_tokens    

def DFG_c(root_node,index_to_code,states):
    # 输入根节点，节点(start_point,end_point)->(index,code)的dict，以及变量名的状态，返回DFG和变量名的状态，状态指的是变量名定义的index
    assignment=['assignment_expression']
    def_statement=['init_declarator']
    increment_statement=['update_expression']
    if_statement=['if_statement','else']
    for_statement=['for_statement']
    while_statement=['while_statement']
    do_first_statement=[]    
    states=states.copy()
    if (len(root_node.children)==0 or root_node.type=='string_literal') and root_node.type!='comment':      # 变量名
        idx,code=index_to_code[(root_node.start_point,root_node.end_point)]
        if root_node.type==code or root_node.type == 'primitive_type':    # 如果类型和内容一样，例如=，那么忽略
            return [],states    
        elif code in states:        # 如果已经定义过了，则数据流为def->use
            return [(code,idx,'comesFrom',[code],states[code].copy())],states
        else:                       # 如果没有定义过
            if root_node.type=='identifier':      # 变量名定义，并设置状态
                states[code]=[idx]
            return [(code,idx,'comesFrom',[],[])],states
    elif root_node.type in def_statement:       # 变量名的申明，a=1 / a
        name=root_node.child_by_field_name('declarator')
        value=root_node.child_by_field_name('value')
        DFG=[]
        if value is None:   # 定义的时候没有赋值
            indexs=tree_to_variable_index(name,index_to_code)   
            for index in indexs:
                idx,code=index_to_code[index]
                DFG.append((code,idx,'comesFrom',[],[]))    
                states[code]=[idx]  # 将该变量名的状态设置为该变量名的index，即使原先已经定义过了，此时也要覆盖
            return sorted(DFG,key=lambda x:x[1]),states
        else:   # a = 1，变量名定义的时候赋值
            name_indexs=tree_to_variable_index(name,index_to_code)
            value_indexs=tree_to_variable_index(value,index_to_code)    # 如果有多个变量名，那么value_indexs为多个，例如a=b=1，name为a，value为b=1，此时value_indexs有两个
            temp,states=DFG_c(value,index_to_code,states)
            DFG+=temp            
            for index1 in name_indexs:
                idx1,code1=index_to_code[index1]
                for index2 in value_indexs:
                    idx2,code2=index_to_code[index2]
                    DFG.append((code1,idx1,'comesFrom',[code2],[idx2]))     # a=b=1, 数据流为1->a, 1->b
                states[code1]=[idx1]   
            return sorted(DFG,key=lambda x:x[1]),states
    elif root_node.type in assignment:  # 赋值语句，a=b
        left_nodes=root_node.child_by_field_name('left')
        right_nodes=root_node.child_by_field_name('right')
        DFG=[]
        temp,states=DFG_c(right_nodes,index_to_code,states)
        DFG+=temp            
        name_indexs=tree_to_variable_index(left_nodes,index_to_code)
        value_indexs=tree_to_variable_index(right_nodes,index_to_code)  
        for index1 in name_indexs:
            idx1,code1=index_to_code[index1]
            for index2 in value_indexs:
                idx2,code2=index_to_code[index2]
                DFG.append((code1,idx1,'computedFrom',[code2],[idx2]))
            states[code1]=[idx1]   
        return sorted(DFG,key=lambda x:x[1]),states
    elif root_node.type in increment_statement: # a++
        DFG=[]
        indexs=tree_to_variable_index(root_node,index_to_code)
        for index1 in indexs:
            idx1,code1=index_to_code[index1]
            for index2 in indexs:
                idx2,code2=index_to_code[index2]
                DFG.append((code1,idx1,'computedFrom',[code2],[idx2]))
            states[code1]=[idx1]
        return sorted(DFG,key=lambda x:x[1]),states   
    elif root_node.type in if_statement:
        DFG=[]
        current_states=states.copy()
        others_states=[]    # if嵌套或者else语句的状态
        flag=False
        tag=False
        # if condition block (else/ if_statement)
        if 'else' in root_node.type:
            tag=True
        for child in root_node.children:
            if 'else' in child.type:
                tag=True
            if child.type not in if_statement and flag is False:    # condition、block
                temp,current_states=DFG_c(child,index_to_code,current_states)    
                DFG+=temp
            else:       # if嵌套或者else语句
                flag=True
                temp,new_states=DFG_c(child,index_to_code,states)    
                DFG+=temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:    # if没有else语句或者if嵌套
            others_states.append(states)
        new_states={}
        # 合并condition、block、if嵌套或者else语句的状态，other_states的大小为状态的个数
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key]=dic[key].copy()
                else:
                    new_states[key]+=dic[key]   # if嵌套的时候，condition的状态可能会被多个if嵌套的block使用
        for key in new_states:
            new_states[key]=sorted(list(set(new_states[key])))
        return sorted(DFG,key=lambda x:x[1]),new_states
    elif root_node.type in for_statement:
        DFG=[]
        for child in root_node.children:    # for(a;b;c) block 遍历a/b/c/block
            temp,states=DFG_c(child,index_to_code,states)
            DFG+=temp
        flag=False
        for child in root_node.children:    # 如果for循环的第一个语句为定义变量，那么需要遍历两遍，例如for(int i=0;;)
            if flag:
                temp,states=DFG_c(child,index_to_code,states)
                DFG+=temp                
            elif child.type=="local_variable_declaration":
                flag=True
        # 合并状态，有些状态x[0] x[1] x[2]是重复的
        # x[0]:id1_name x[1]:index1 x[2] comesfrom/computedfrom x[3]:id2_name x[4]:index2
        dic={}
        for x in DFG:
            if (x[0],x[1],x[2]) not in dic:    # 如果没有出现过，则加入
                dic[(x[0],x[1],x[2])]=[x[3],x[4]]
            else:        # 如果出现过，则合并
                dic[(x[0],x[1],x[2])][0]=list(set(dic[(x[0],x[1],x[2])][0]+x[3]))   # 合并列表
                dic[(x[0],x[1],x[2])][1]=sorted(list(set(dic[(x[0],x[1],x[2])][1]+x[4])))   # 合并列表
        DFG=[(x[0],x[1],x[2],y[0],y[1]) for x,y in sorted(dic.items(),key=lambda t:t[0][1])]
        return sorted(DFG,key=lambda x:x[1]),states
    elif root_node.type in while_statement:  
        DFG=[]
        for i in range(2):
            for child in root_node.children:
                temp,states=DFG_c(child,index_to_code,states)
                DFG+=temp    
        dic={}
        for x in DFG:
            if (x[0],x[1],x[2]) not in dic:
                dic[(x[0],x[1],x[2])]=[x[3],x[4]]
            else:
                dic[(x[0],x[1],x[2])][0]=list(set(dic[(x[0],x[1],x[2])][0]+x[3]))
                dic[(x[0],x[1],x[2])][1]=sorted(list(set(dic[(x[0],x[1],x[2])][1]+x[4])))
        DFG=[(x[0],x[1],x[2],y[0],y[1]) for x,y in sorted(dic.items(),key=lambda t:t[0][1])]
        return sorted(DFG,key=lambda x:x[1]),states        
    else:   # 递归遍历所有子树
        DFG=[]
        for child in root_node.children:
            if child.type in do_first_statement:
                temp,states=DFG_c(child,index_to_code,states)
                DFG+=temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp,states=DFG_c(child,index_to_code,states)
                DFG+=temp    
        return sorted(DFG,key=lambda x:x[1]),states
