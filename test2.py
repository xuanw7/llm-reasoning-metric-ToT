import numpy as np
with open('result.npy', 'rb') as f:
    a = np.load(f)
    b = np.load(f)
    c = np.load(f)

print(a)
print(b)
print(c)