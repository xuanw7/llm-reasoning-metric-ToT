import argparse
from tot.methods.bfs import solve
from tot.tasks.game24 import Game24Task

import pickle 
import numpy as np

import re


with open('result_0_5.txt','rb') as f:
   results = pickle.load(f)

for each in results:

   print("----------------------------------------------------------------------")
   print("All terminal nodes:", len(each[0]) + len(each[2]))
   print("Cleaned terminal nodes:", len(each[0]))
   print("Number of terminal nodes that reached 24: ", each[1])
   print("Result of this problem: " , each[3])


    

        
        

    

   
   