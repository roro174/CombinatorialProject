from itertools import combinations
import gurobipy as gp
from gurobipy import GRB

class ISPModel:
    """A class to create the ISP model with all the variables and the constraints."""
    def __init__(self, json_handler, question2=False, bridge=False):
        self.data = json_handler
        self.model = gp.Model("ISP_Model")
        self.all_pairs_in_session = {}
        self.x = None  # x[i,s]: interpreter i assigned to session s
        self.y = None  # y[i,s,(l1,l2)]: interpreter i covers (l1,l2) in session s
        self.z = None  # z[s,(l1,l2)]: (l1,l2) is covered in session s
        self.c = None  # c[s]: 1 if all language pairs in session s are covered
        self.w = None  # w[i,b]: interpreter i assigned to block b (for question 2)
        self._build_variables(question2)
        self._add_constraints()
        if question2:
            self._constraints_question2()

    def _build_variables(self, question2):
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_lang = self.data.get_sessions_lang()

        if question2:
            self.w = self.model.addVars(interpreters, blocks, vtype=GRB.BINARY, name="w")

        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")

        self.y = {}
        self.z = {}

        for s in sessions:
            langs = sessions_lang[s]
            # Tri des paires pour éviter (l1,l2) ≠ (l2,l1)
            self.all_pairs_in_session[s] = [(min(l1, l2), max(l1, l2)) for l1, l2 in combinations(langs, 2)]

        self.y = self.model.addVars(
            [(i, s, l1, l2) for s in sessions
                            for (l1, l2) in self.all_pairs_in_session[s]
                            for i in interpreters],
            vtype=GRB.BINARY, name="y"
        )

        self.z = self.model.addVars(
            [(s, l1, l2) for s in sessions
                         for (l1, l2) in self.all_pairs_in_session[s]],
            vtype=GRB.BINARY, name="z"
        )

    def _add_constraints(self):
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

        for i in interpreters:
            for s in sessions:
                eligible_pairs = [(l1, l2) for (l1, l2) in self.all_pairs_in_session[s]
                                  if l1 in interpreters_lang[i] and l2 in interpreters_lang[i]]
                # Max one pair per session
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2] for (l1, l2) in eligible_pairs) <= 1,
                    name=f"one_pair_per_interpreter_{i}_{s}"
                )

                # y[i,s,l1,l2] <= x[i,s] and y[i,s,l1,l2] == 0 if langs not known
                for (l1, l2) in self.all_pairs_in_session[s]:
                    if l1 in interpreters_lang[i] and l2 in interpreters_lang[i]:
                        self.model.addConstr(
                            self.y[i, s, l1, l2] <= self.x[i, s],
                            name=f"y_leq_x_{i}_{s}_{l1}_{l2}"
                        )
                    else:
                        self.model.addConstr(
                            self.y[i, s, l1, l2] == 0,
                            name=f"y_zero_if_unknown_langs_{i}_{s}_{l1}_{l2}"
                        )

                # 🔥 Ajout essentiel : x[i,s] ⇒ au moins un y[i,s,l1,l2]
                if eligible_pairs:
                    self.model.addConstr(
                        self.x[i, s] <= gp.quicksum(self.y[i, s, l1, l2] for (l1, l2) in eligible_pairs),
                        name=f"x_implies_y_exists_{i}_{s}"
                    )
                else:
                    self.model.addConstr(
                        self.x[i, s] == 0,
                        name=f"x_forbidden_if_no_pairs_{i}_{s}"
                    )

        # One interpreter per pair per session
        for s in sessions:
            for (l1, l2) in self.all_pairs_in_session[s]:
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2] for i in interpreters) <= 1,
                    name=f"one_interpreter_per_pair_{s}_{l1}_{l2}"
                )

        # z == sum y[i,s,l1,l2]
        for s in sessions:
            for (l1, l2) in self.all_pairs_in_session[s]:
                self.model.addConstr(
                    self.z[s, l1, l2] == gp.quicksum(self.y[i, s, l1, l2] for i in interpreters),
                    name=f"z_equals_y_sum_{s}_{l1}_{l2}"
                )

        # c[s] = 1 ⇔ all pairs are covered
        for s in sessions:
            nb_pairs = len(self.all_pairs_in_session[s])
            self.model.addConstr(
                gp.quicksum(self.z[s, l1, l2] for (l1, l2) in self.all_pairs_in_session[s]) >=
                nb_pairs * self.c[s],
                name=f"c_active_if_all_z_{s}"
            )

    def _constraints_question2(self):
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()

        for i in interpreters:
            self.model.addConstr(
                gp.quicksum(self.x[i, s] for s in sessions) <= 15,
                name=f"max_sessions_{i}"
            )

        for b in blocks:
            for i in interpreters:
                for s in sessions_b[b]:
                    self.model.addConstr(
                        self.w[i, b] >= self.x[i, s],
                        name=f"w_lower_{i}_{b}_{s}"
                    )
                self.model.addConstr(
                    self.w[i, b] <= gp.quicksum(self.x[i, s] for s in sessions_b[b]),
                    name=f"w_upper_{i}_{b}"
                )

        for i in interpreters:
            for j in range(len(blocks) - 3):
                self.model.addConstr(
                    self.w[i, blocks[j]] + self.w[i, blocks[j+1]] +
                    self.w[i, blocks[j+2]] + self.w[i, blocks[j+3]] <= 3,
                    name=f"no_4_consecutive_blocks_{i}_{j}"
                )

    def _set_objective_of1(self):
        """Maximize number of covered language pairs (y variables)."""
        self.model.setObjective(gp.quicksum(self.y.values()), GRB.MAXIMIZE)

    def _set_objective_of2(self):
        """Maximize number of fully covered sessions."""
        self.model.setObjective(gp.quicksum(self.c.values()), GRB.MAXIMIZE)

    def solve_of(self, verbose=True, use_of1=True):
        if use_of1:
            self._set_objective_of1()
        else:
            self._set_objective_of2()

        self.model.optimize()

        if verbose:
            print("\nSelected assignments:")
            for (i, s), var in self.x.items():
                if var.X > 0.5:
                    print(f"Interpreter {i} assigned to Session {s}")

            print("\nCovered language pairs:")
            for (i, s, l1, l2), var in self.y.items():
                if var.X > 0.5:
                    print(f"Session {s}: Interpreter {i} covers pair ({l1}, {l2})")

            if use_of1:
                print("\nTotal pairs covered (OF1):", self.model.ObjVal)
            else:
                print("\nSessions fully covered:")
                for s, var in self.c.items():
                    if var.X > 0.5:
                        print(f"Session {s} is fully covered")
                print("\nTotal sessions fully covered (OF2):", self.model.ObjVal)

        return self.model.ObjVal
