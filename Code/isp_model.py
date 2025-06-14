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
        self.all_pairs_in_session = {}
        self.u = None # u[s, l]: 1 if language l is covered in session s
        self.x = None  # x[i,s]: interpreter i assigned to session s
        self.y = None  # y[i,s,(l1,l2)]: pair (l1,l2) covered in session s
        self.c =  None  # c[s]: 1 if all pairs covered in session s
        self.w = None  # w[i,b]: interpreter i assigned to block b (only for question 2)
        self.z = None # Z[s,(l0, l1,l2)]: bridge betwwen l1 and l2 by l0 in session s (only for question 3)
        self._build_variables(question2, bridge)
        self._add_constraints()
        if question2:
            self._constraints_question2()
        if bridge:
            self._bridge_constraints()


    def _bridge_constraints(self):
        """Add the constraints for the bridge between languages."""
        interpreters = self.data.get_interpreters()
        interpreters_lang = self.data.get_interpreters_lang()

        # Pair covered only if assigned interpreters know both l0 and interpreter 1 knows l1
        # interpreter knows l2
        for (s, l0, l1, l2), var in self.z.items():
            eligible_i1 = [i for i in interpreters if l1 in interpreters_lang[i] and
                          l0 in interpreters_lang[i]]
            eligible_i2 = [i for i in interpreters if l2 in interpreters_lang[i] and
                            l0 in interpreters_lang[i]]
            self.model.addConstr(
            var <= gp.quicksum(self.x[i, s] for i in eligible_i1),
            name=f"first_pair_covering_{s}_{l0}_{l1}_{l2}"
            )
            self.model.addConstr(
            var <= gp.quicksum(self.x[i, s] for i in eligible_i2),
            name=f"second_pair_covering_{s}_{l0}_{l1}_{l2}"
            )

        
        # an interpreter cannot take both side of the same bridge

        

    def _build_variables(self, question2, bridge):
        """Build the variables for the model."""
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_lang = self.data.get_sessions_lang()
        languages = self.data.get_languages()

        if question2:
            self.w = self.model.addVars(interpreters, blocks, vtype=GRB.BINARY, name="w")
        if bridge:
            self.z = {}
        self.u = self.model.addVars(sessions, languages, vtype=GRB.BINARY, name="u")
        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.y = {}
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")
        for s in sessions:
            langs = sessions_lang[s]
            self.all_pairs_in_session[s] = list(combinations(langs, 2))
    
        self.y = self.model.addVars(
            [(i, s, l1, l2) for s in sessions
                            for (l1, l2) in self.all_pairs_in_session[s]
                            for i in interpreters],
            vtype=GRB.BINARY, name="y"
        )

    def _add_constraints(self):
        """Add the constraints to the model."""
        interpreters = self.data.get_interpreters()
        interpreters_lang = self.data.get_interpreters_lang()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()
        sessions = self.data.get_sessions()
        sessions_lang = self.data.get_sessions_lang()

        # One session per block per interpreter
        for b in blocks:
            for i in interpreters:
                self.model.addConstr(
                    gp.quicksum(self.x[i, s] for s in sessions_b[b]) <= 1,
                    name=f"one_session_per_block_{i}_{b}"
                )

        # Each interpreter can only cover a pair in a session if assigned to that session
        for i in interpreters:
            for s in sessions:
                # An interpreter can cover at most one pair per session
                self.model.addConstr(
                gp.quicksum(self.y[i, s, l1, l2] for (l1, l2) in self.all_pairs_in_session[s]) <= 1,
                name=f"one_pair_per_interpreter_{i}_{s}")
                for (l1, l2) in self.all_pairs_in_session[s]:
                    self.model.addConstr(
                        self.y[i, s, l1, l2] <= self.x[i, s],
                        name=f"coverage_only_if_assigned_{i}_{s}_{l1}_{l2}"
                    )
                # Each interpreter can only cover a pair if they know both languages
                    if l1 not in interpreters_lang[i] or l2 not in interpreters_lang[i]:
                        self.model.addConstr(
                            self.y[i, s, l1, l2] == 0,
                        name=f"coverage_only_if_langs_{i}_{s}_{l1}_{l2}")
               
        # Each interpreter to be in a session must be assigned to one pair of the session
        """for i in interpreters:
            for s in sessions:
                self.model.addConstr(
                    self.x[i, s] <= gp.quicksum(self.y[i, s, l1, l2] for (l1, l2) in self.all_pairs_in_session[s]),
                    name=f"assignment_requires_pair_{i}_{s}"
                )"""

        # Each pair can only be covered by one interpreter in a session
        for s in sessions:
            for l1, l2 in self.all_pairs_in_session[s]:
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2] for i in interpreters) <= 1,
                    name=f"one_interpreter_per_pair_{s}_{l1}_{l2}"
                )

        for s in sessions:
            for lang in sessions_lang[s]:
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2]
                                for i in interpreters
                                for (l1, l2) in self.all_pairs_in_session[s]
                                if l1 == lang or l2 == lang) >= self.u[s, lang],
                    name=f"lang_covered_{s}_{lang}"
                )

            self.model.addConstr(
                gp.quicksum(self.u[s, lang] for lang in sessions_lang[s]) >= len(sessions_lang[s]) * self.c[s],
                name=f"session_covered_{s}"
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
        self.model.setParam('TimeLimit', 600) # Set a time limit of 10 minutes
        self.model.optimize()

        if verbose:
            print("\nSelected assignments:")

            if use_of1:
                print("\nCovered language pairs:")
                for (_,s, l1, l2), var in self.y.items():
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
