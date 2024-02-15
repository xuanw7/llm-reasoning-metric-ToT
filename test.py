import argparse
from tot.methods.bfs import solve
from tot.tasks.game24 import Game24Task

import pickle 
import numpy as np

args = argparse.Namespace(backend='gpt-4-0613', temperature=0.7, task='game24', naive_run=False, prompt_sample=None, method_generate='propose', method_evaluate='value', method_select='greedy', n_generate_sample=1, n_evaluate_sample=3, n_select_sample=5)

task = Game24Task()
num_deadend  = []
correctness = []
print(task.test)

for i in range (900, 910):

    ys, info = solve(args, task, i)
    num_deadend.append(task.efficiency_count)

    correct = 0
    infos = [task.test_output(i, y) for y in ys]
    accs = [info['r'] for info in infos]
    print(accs)
    for each in accs:
        if (each == 1 or each == '1'):
            correct = 1
            break

    correctness.append(correct)


    task.efficiency_count = 0
    task.value_cache = {}
   

print(num_deadend)
print(correctness)



score = np.array(correctness) / np.log2(np.array(num_deadend) + 1)

print(score)
print(np.average(score))




with open('result.npy', 'wb') as f:
    np.save(f, num_deadend)
    np.save(f, correctness)
    np.save(f, score)
    
with open('result.npy', 'rb') as f:
    a = np.load(f)
    b = np.load(f)
    c = np.load(f)


print(np.average(c))