"""
Project of Combinatorial Optimization: ISP problem
Class for the ISP problem model
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""

from itertools import combinations

import gurobipy as gp
from gurobipy import GRB

class ISPModel:
    """A class to create the ISP model with all the variables and the constraints."""
    def __init__(self, json_handler, question2=False, bridge=False):
        self.data = json_handler
        self.model = gp.Model("ISP_Model")
        self.x = None  # x[i,s]: interpreter i assigned to session s
        self.y = None  # y[s,(l1,l2)]: pair (l1,l2) covered in session s
        self.c =  None  # c[s]: 1 if all pairs covered in session s
        self.w = None  # w[i,b]: interpreter i assigned to block b (only for question 2)
        self._build_variables(question2)
        self._add_constraints()
        if question2:
            self._constraints_question2()
        if bridge:
            self._add_bridge()


    def _add_bridge(self):
        ...

    def _build_variables(self, question2):
        """Build the variables for the model."""
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_lang = self.data.get_sessions_lang()

        if question2:
            self.w = self.model.addVars(interpreters, blocks, vtype=GRB.BINARY, name="w")
        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.y = {}
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")


        for s in sessions:
            langs = sessions_lang[s]
            for l1, l2 in combinations(langs, 2):
                self.y[s, l1, l2] = self.model.addVar(vtype=GRB.BINARY, name=f"y_{s}_{l1}_{l2}")

    def _add_constraints(self):
        """Add the constraints to the model."""
        interpreters = self.data.get_interpreters()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()
        interpreters_lang = self.data.get_interpreters_lang()

        # One session per block per interpreter
        for b in blocks:
            for i in interpreters:
                self.model.addConstr(
                    gp.quicksum(self.x[i, s] for s in sessions_b[b]) <= 1,
                    name=f"one_session_per_block_{i}_{b}"
                )

        # Pair covered only if assigned interpreter knows both languages
        for (s, l1, l2), var in self.y.items():
            eligible_i = [i for i in interpreters if l1 in interpreters_lang[i] and
                          l2 in interpreters_lang[i]]
            self.model.addConstr(
            var <= gp.quicksum(self.x[i, s] for i in eligible_i),
            name=f"pair_covering_{s}_{l1}_{l2}"
            )

        # Constraint: c_s = 1 if all pairs are covered
        for (s, l1, l2), var in self.y.items():
            self.model.addConstr(
                    var >= self.c[s],
                    name=f"session_complete_{s}_{l1}_{l2}"
                )


    def _constraints_question2(self):
        """Add the constraints for question 2."""
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()

        # Each interpreter can be assigned to at most Mi = 15 sessions
        for i in interpreters:
            self.model.addConstr(
                gp.quicksum(self.x[i, s] for s in sessions) <= 15,
                name=f"interpreter_one_session_{i}"
            )

     # if interpreter i is assigned to session s
     # then it must be assigned to the block b of that session
        for b in blocks:
            for i in interpreters:
                for s in sessions_b[b]:
                    self.model.addConstr(
                        self.w[i, b] >= self.x[i, s],
                        name=f"lower_bound_{i}_{b}_{s}"
                    )
                self.model.addConstr(
                    self.w[i, b] <= gp.quicksum(self.x[i, s] for s in sessions_b[b]),
                    name=f"w_link_upper_{i}_{b}"
                )

        # each interpreter cannot work during more than CBi = 3 consecutive blocks
        for i in interpreters:
            for j in range(len(blocks) - 3):
                self.model.addConstr(
                    self.w[i, blocks[j]] + self.w[i, blocks[j+1]]
                    + self.w[i, blocks[j+2]] + self.w[i, blocks[j+3]] <= 3,
                    name=f"no_three_consecutive_blocks_{i}_{j}"
                )



    def _set_objective_of1(self):
        """Set the objective function OF1: maximize the number of covered language pairs."""
        self.model.setObjective(gp.quicksum(self.y.values()), GRB.MAXIMIZE)

    def _set_objective_of2(self):
        """Set the objective function OF2: maximize the number of sessions fully covered."""
        self.model.setObjective(gp.quicksum(self.c.values()), GRB.MAXIMIZE)

    def solve_of(self, verbose=True, use_of1=True):
        """Solve the model using OF1 or OF2.
        :param verbose: If True, print the results.
        :param use_of1: If True, use objective function OF1, otherwise use OF2."""
        if use_of1:
            self._set_objective_of1()
        else: self._set_objective_of2()
        self.model.optimize()

        if verbose:
            print("\nSelected assignments:")
            for (i, s), var in self.x.items():
                if var.X > 0.5:
                    print(f"Interpreter {i} assigned to Session {s}")

            if use_of1:
                print("\nCovered language pairs:")
                for (s, l1, l2), var in self.y.items():
                    if var.X > 0.5:
                        print(f"Session {s} covers pair ({l1}, {l2})")

                print("\nTotal pairs covered (OF1):", self.model.ObjVal)
            else:
                print("\nSessions fully covered:")
                for s, var in self.c.items():
                    if var.X > 0.5:
                        print(f"Session {s} is fully covered")

                print("\nTotal sessions fully covered (OF2):", self.model.ObjVal)

        return self.model.ObjVal
