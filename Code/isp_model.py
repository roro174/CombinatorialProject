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
        self.y = None  # y[i,s,l1,l2]: pair (l1,l2) covered in session s and interpreter by i
        self.c =  None  # c[s]: 1 if all pairs covered in session s
        self.w = None  # w[i,b]: interpreter i assigned to block b (only for question 2)
        self.z = None # Z[i, j,  s,l0, l1,l2]:
                        #bridge betwwen l1 and l2 by l0 in session s where
                        # i covered l0 and l1 and j covered l0 and l2(only for question 3)
        self.compatible_pairs = dict() # contains all the pairs of languages
                                        #that can be covered by an interpreter in a session
        self.interpreters_per_pair = dict() # contains all the interpreters
                                            #that can cover a pair of languages in a session
        self.all_pairs_in_session = dict() # contains all the combinations of languages in a session
        self._build_variables(question2, bridge)
        self._add_constraints(question2, bridge)


    def _build_variables(self, question2, bridge):
        """Build the variables for the model."""
        interpreters = self.data.get_interpreters()
        interpreters_lang = self.data.get_interpreters_lang()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_lang = self.data.get_sessions_lang()

        if question2:
            self.w = self.model.addVars(interpreters, blocks, vtype=GRB.BINARY, name="w")
        self.u = self.model.addVars(
            [(s, lang) for s in sessions for lang in sessions_lang[s]],
            vtype=GRB.BINARY,
            name="u"
        )
        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.y = {}
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")
        self._build_languages_variables(sessions, sessions_lang, interpreters, interpreters_lang)
        if bridge:
            self._build_bridges_variables(sessions, interpreters, interpreters_lang)



    def _build_languages_variables(self, sessions, sessions_lang, interpreters, interpreters_lang):
        """Build the variables for y."""
        # Build all pairs per session
        for s in sessions:
            langs = sessions_lang[s]
            self.all_pairs_in_session[s] = list(combinations(langs, 2))
            # Build compatible pairs per interpreter and session
            for i in interpreters:
                compatible = [
                    (l1, l2)
                    for (l1, l2) in self.all_pairs_in_session[s]
                    if l1 in interpreters_lang[i] and l2 in interpreters_lang[i]
                ]
                if compatible:
                    self.compatible_pairs[i, s] = compatible
            for l1, l2 in self.all_pairs_in_session[s]:
                self.interpreters_per_pair[s, l1, l2] = [
                    i for i in interpreters if (i, s)
                    in self.compatible_pairs and (l1, l2) in self.compatible_pairs[i, s]
                ]

        self.y = self.model.addVars(
            [(i, s, l1, l2)
            for (i, s), pairs in self.compatible_pairs.items()
            for (l1, l2) in pairs],
            vtype=GRB.BINARY, name="y"
        )


    def _build_bridges_variables(self, sessions, interpreters, interpreters_lang):
        """Build the variables for the bridges between languages."""
        self.z = {}
        for s in sessions:
            for l1, l2 in self.all_pairs_in_session[s]:
                for i in interpreters:
                    for j in interpreters:
                        if i != j:
                            # intesection betwwen interpreters languages
                            common_langs = set(
                                interpreters_lang[i]).intersection(interpreters_lang[j])
                            for l0 in common_langs:
                                self.z[i, j, s, l0, l1, l2] = self.model.addVar(
                                    vtype=GRB.BINARY,
                                    name=f"z_{i}_{j}_{s}_{l0}_{l1}_{l2}")


    def _add_constraints(self,question2, bridge):
        """Add the constraints to the model."""
        interpreters = self.data.get_interpreters()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()
        sessions = self.data.get_sessions()
        sessions_lang = self.data.get_sessions_lang()
        self._constraints_interpreter(blocks, interpreters, sessions_b, sessions)
        self._constraints_session(sessions)
        self._constraints_session_coverage(sessions, sessions_lang)
        if question2:
            self._constraints_question2()
        if bridge:
            self._bridge_constraints()



    def _constraints_interpreter(self, blocks, interpreters, sessions_b, sessions):
        """Add the constraints for the interpreters."""
        # One session per block per interpreter
        for b in blocks:
            for i in interpreters:
                self.model.addConstr(
                    gp.quicksum(self.x[i, s] for s in sessions_b[b]) <= 1,
                    name=f"one_session_per_block_{i}_{b}"
                )

        # Each interpreter can be assigned to at most a single pair in a session
        for i in interpreters:
            for s in sessions:
                expr = gp.quicksum(
                    self.y[i, s, l1, l2]
                    for (l1, l2) in self.all_pairs_in_session[s]
                    if (i, s) in self.compatible_pairs and (l1, l2) in self.compatible_pairs[(i, s)]
                )

                if self.z is not None:
                    # Ajouter tous les z où l'interprète i intervient dans la session s
                    expr += gp.quicksum(
                        var for key, var in self.z.items()
                        if (key[0] == i or key[1] == i) and key[2] == s
                    )

                self.model.addConstr(expr == self.x[i, s],
                                     name=f"one_assignment_per_interpreter_{i}_{s}")

    def _constraints_session(self, sessions):
        """Add the constraints for the sessions."""

        #Each pair of language can be covered by at most one interpreter in a session
        for s in sessions:
            for l1, l2 in self.all_pairs_in_session[s]:
                if self.z is not None:  # Si on est en mode bridge
                    sum_y = gp.quicksum(
                        self.y[i, s, l1, l2] for i in self.interpreters_per_pair[s, l1, l2]
                    )
                    sum_z = gp.quicksum(
                        var for key, var in self.z.items()
                        if key[2] == s and key[4] == l1 and key[5] == l2
                    )

                    self.model.addConstr(
                        sum_y + sum_z <= 1,
                        name=f"one_interpreter_or_bridge_per_pair_{s}_{l1}_{l2}"
                    )
                else:
                    self.model.addConstr(
                        gp.quicksum(self.y[i, s, l1, l2]
                                    for i in self.interpreters_per_pair[s, l1, l2]) <= 1,
                        name=f"one_interpreter_per_pair_{s}_{l1}_{l2}"
                    )


    def _constraints_session_coverage(self, sessions, sessions_lang):
        """Add the constraints for the session coverage."""

        for s in sessions:
            for lang in sessions_lang[s]:
                sum_y = gp.quicksum(
                    self.y[i, s, l1, l2]
                    for (l1, l2) in self.all_pairs_in_session[s]
                    if l1 == lang or l2 == lang
                    for i in self.interpreters_per_pair[s, l1, l2]
                )
                
                if self.z is not None:
                    sum_z = gp.quicksum(
                        var
                        for (i, j, s2, l0, l1, l2), var in self.z.items()
                        if s2 == s and (l1 == lang or l2 == lang)
                    )
                    self.model.addConstr(
                        sum_y + sum_z >= self.u[s, lang],
                        name=f"lang_covered_with_bridges_{s}_{lang}"
                    )
                else:
                    self.model.addConstr(
                        sum_y >= self.u[s, lang],
                        name=f"lang_covered_{s}_{lang}"
                    )

            # Contrainte de couverture complète de la session
            self.model.addConstr(
                gp.quicksum(self.u[s, lang] for lang in sessions_lang[s])
                >= len(sessions_lang[s]) * self.c[s],
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

    def _bridge_constraints(self):
        """Add the constraints for the bridge between languages."""
        # Pair covered only if assigned interpreters know both l0 and interpreter 1 knows l1
        for (i, j, s, l0, l1, l2), var in self.z.items():
            # i doit être assigné à s et connaître l1 et l0
            self.model.addConstr(var <= self.x[i, s],
                                 name=f"bridge_assign_i_{i}_{j}_{s}_{l0}_{l1}_{l2}")
            self.model.addConstr(var <= self.x[j, s],
                                 name=f"bridge_assign_j_{i}_{j}_{s}_{l0}_{l1}_{l2}")



    def _set_objective_of1(self):
        """Set the objective function OF1: maximize the number of covered language pairs."""
        if self.z is not None:
            self.model.setObjective(gp.quicksum(self.y.values())
                                     + gp.quicksum(self.z.values()), GRB.MAXIMIZE)
        else:
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
                for (i,s, l1, l2), var in self.y.items():
                    if var.X > 0.5:
                        print(f"{i} on  {s} covers pair ({l1}, {l2})")
                if self.z is not None:
                    for(i, j, s, l0, l1, l2), var in self.z.items():
                        if var.X > 0.5:
                            print(f"{i} on {s} covers bridge ({l1}, {l2}) with {j} using {l0}")
                print("\nTotal pairs covered (OF1):", self.model.ObjVal)
            else:
                print("\nSessions fully covered:")
                for s, var in self.c.items():
                    if var.X > 0.5:
                        print(f"Session {s} is fully covered")

                print("\nTotal sessions fully covered (OF2):", self.model.ObjVal)

        return self.model.ObjVal
