class A:
    def __init__(self):
        self.name = 'A'

class B:
    def __init__(self):
        self.name = 'B'

import pickle
# 将对象序列化到文件
with open('test.pkl', 'wb') as f:
    a = A()
    pickle.dump(a, f)
    b = B()
    pickle.dump(b, f)

# 从文件中读取对象
with open('test.pkl', 'rb') as f:
    a = pickle.load(f)
    print(a.name)
    b = pickle.load(f)
    print(b.name)