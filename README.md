# TSA
tree-sitter analysis, 是一个基于tree-sitter编译器和可视化工具graphviz的代码分析工具，能够生成抽象语法树AST、控制流图CFG、数据流图DFG、数据依赖图CDG、函数调用图CG等。

## 环境配置
确保已经安装了graphviz，在windows上，官网https://www.graphviz.org/ 下载graphviz之后，配置环境变量为安装路径下的bin文件夹，例如D:\graphviz\bin\，注意末尾的'\\'不能省略，如果是linux上，运行下面命令安装：
```
sudo apt-get install graphviz graphviz-doc
```
接着运行
```
pip install -r requirements.txt
```

## 生成AST树
AST/AST.py能够生成AST树以及tokens，首先构造类，参数为代码语言，目前tree-sitter能够编译的语言都能够生成。
```
ast = AST('c')
```
接着运行下面代码可以显示AST树
```
ast.see_tree(code, view=True)
```
![AST](https://github.com/rebibabo/TSA/assets/80667434/6d1aae84-3c46-4978-844e-6006e8623718)

运行完成之后，会在当前目录下生成ast_tree.pdf，为可视化的ast树，以及ast_tree.txt，为AST树的信息，每一行由当前节点id, 父节点id，以及当前节点信息组成，节点信息由节点类型type，在源代码的起始字节start_byte、终止字节end_byte、开始位置start_point，结束位置end_point，位置信息由行号和列号组成，是否是叶子节点is_leaf和内容text组成，例如下面样例所示：
```
(2, 1, {'type': 'primitive_type', 'start_byte': 5, 'end_byte': 8, 'start_point': (1, 4), 'end_point': (1, 7), 'is_leaf': True, 'text': 'int'})
```
可以通过设置参数view=False在生成pdf文件的同时不查看文件，pdf=False不生成可视化的pdf文件，设置参数filename="filename"来更改输出文件的名称。
获得代码的tokens可以运行下面的代码，返回值为token的列表。
```
ast.tokenize(code)
#['int', 'main', '(', ')', '{', 'int', 'abc', '=', '1', ';', 'int', 'b', '=', '2', ';', 'int', 'c', '=', 'a', '+', 'b', ';', 'while', '(', 'i', '<', '10', ')', '{', 'i', '++', ';', '}', '}']
```

## 生成CFG
CFG/CFG.py继承自AST类，能够生成控制流图，运行下面命令可以获得代码的CFG：
```
cfg = CFG('c')
cfg.see_cfg(code, view=True)
```
生成的CFG图样例：
![CFG](https://github.com/rebibabo/TSA/assets/80667434/d1c05e69-f1e0-4b59-82c4-1073cbaaf913)
see_cfg的参数和see_tree的参数一样，运行完后，会在当前路径下生成CFG.txt，每一行由节点属性，（入节点id，边标签）组成，节点属性由节点内容node，类型type，id，是否是分支is_branch以及行号line组成，样例如下：
```
({'node': 'return 0;', 'type': 'return_statement', 'id': 7, 'is_branch': False, 'line': 9}, [(6, ''), (5, 'N'), (4, '')])
```

## 生成CDG
CDG/CDG.py继承自CFG类，能够生成控制依赖图，生成的算法参考博客https://blog.csdn.net/Dong_HFUT/article/details/121492818，运行下面代码能够获得CDG图：
```
cdg = CDG('c')
cdg.see_cdg(code, view=True)
```
生成的CDG图样例：
![CDG](https://github.com/rebibabo/TSA/assets/80667434/cafe9bed-d65c-4d3d-b948-b8829983258a)
运行完毕后，会在当前路径生成CDG.txt，节点属性和CDG.txt一样
