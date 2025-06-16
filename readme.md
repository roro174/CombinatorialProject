# Project of Combinatorial Optimization: ISP problem

Authors : 
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI

### Required to run this program

Make sure you have **Gurobi** installed.
This project has been implemented and tested on a linux OS using **Python 3.10**.



## Building

To run the program:

1. Open the terminal at the same level as the readme


```bash
 python Code/main.py args[0] args[1] args[2]
```

Where:

- `args[0]` = path to the instance file
- `args[1]` = whether we want to add the constraints of the question 2 -> ["True", "False"]
- `args[2]` = whether we want to add the constraints of the question 3 -> ["True", "False"]


_example_: `python Code/main.py example.json False False`