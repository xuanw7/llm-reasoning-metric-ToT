import argparse
from tot.methods.bfs import solve
from tot.tasks.game24 import Game24Task

import pickle 
import numpy as np
import re
pattern = r"\b\d+\.?\d*\b"

def clean_deadend(all_set, x):
    good_set = set()
    count_24 = 0

    for steps in all_set:
        if (len(steps) <3):
            continue
        if (len(steps) > 3):
            steps = (steps[0], steps[1], steps[2])
        tmp = x.copy()
        step0 = steps[0]
        numbers0 = re.findall(pattern, step0)
        if (len(numbers0) != 3):
            continue
        first0, second0 = numbers0[0], numbers0[1]

        if (first0 in tmp):
            tmp.remove(first0)
        if (second0 in tmp):
            tmp.remove(second0)

        step1 = steps[1]
        numbers1 = re.findall(pattern, step1)
        if (len(numbers1) != 3):
            continue

        step2 = steps[2]
        numbers2 = re.findall(pattern, step2)
        if (len(numbers2) != 3):
            continue
        numbers_left = [numbers1[0], numbers1[1], numbers2[0], numbers2[1]]
        numbers_left_copy = numbers_left.copy()

        for each in numbers_left:
            if each in tmp and tmp != []:
                tmp.remove(each)
                numbers_left_copy.remove(each)

        if (numbers0[2] not in numbers_left_copy):
            continue
        numbers_left_copy.remove(numbers0[2])
        if (numbers1[2] not in numbers_left_copy):
            continue

        if (tmp == []):
            good_set.add(steps)
            if(numbers2[2] == '24'):
                count_24+=1

    return good_set, count_24



args = argparse.Namespace(backend='gpt-3.5-turbo-0613', temperature=0.7, task='game24', naive_run=False, prompt_sample=None, method_generate='propose', method_evaluate='value', method_select='greedy', n_generate_sample=1, n_evaluate_sample=3, n_select_sample=5)

task = Game24Task()
num_deadend  = []
correctness = []
results = []
for i in range(905, 910):
    ys, info = solve(args, task, i)
    x = task.get_input(i)
    x = x.split(' ')
    deadend_set = task.deadend_set_useful.union(task.deadend_set_useless)
    cleaned_deadend_set, count_24 = clean_deadend(deadend_set, x)

    infos = [task.test_output(i, y) for y in ys]
    info.update({'idx': i, 'ys': ys, 'infos': infos})
    # log main metric
    accs = [info['r'] for info in infos]


    print("----------------------------------------------------------------------")
    print("Cleaned terminal nodes:", cleaned_deadend_set)
    print("Number of terminal nodes that reached 24: ", count_24)
    bad_deadend_set =deadend_set.difference(cleaned_deadend_set)
    print("Bad terminal nodes: ", bad_deadend_set)

    find = False
    for each in accs:
        if (each == '1' or each == 1):
            print("Result of this problem: correct"  )
            find = True
            break
    if not find:
        print("Result of this problem: incorrect"  )
    print("----------------------------------------------------------------------")

    results.append((cleaned_deadend_set, count_24, bad_deadend_set, find))

    task.deadend_set_useful = set()
    task.deadend_set_useless = set()

with open('result_5_10.txt','wb') as f:
   pickle.dump(results, f)

with open('result_5_10.txt','rb') as f:
   results = pickle.load(f)
 
print(results)
