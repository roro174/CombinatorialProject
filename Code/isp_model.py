import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

class ISPModel:
    def __init__(self, json_handler):
        self.data = json_handler
        self.model = gp.Model("ISP_Model")
        self.x = None  # x[i,s]: interpreter i assigned to session s
        self.y = None  # y[s,(l1,l2)]: pair (l1,l2) covered in session s
        self.c = None  # c[s]: 1 if all pairs covered in session s

    def build_variables(self):
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        sessions_lang = self.data.get_sessions_lang()

        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.y = {}
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")

        for s in sessions:
            langs = sessions_lang[s]
            for l1, l2 in combinations(langs, 2):
                self.y[s, l1, l2] = self.model.addVar(vtype=GRB.BINARY, name=f"y_{s}_{l1}_{l2}")

    def add_constraints(self):
        interpreters = self.data.get_interpreters()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()
        sessions = self.data.get_sessions()
        sessions_lang = self.data.get_sessions_lang()
        interpreters_lang = self.data.get_interpreters_lang()

        # One session per block per interpreter
        for b in blocks:
            for i in interpreters:
                self.model.addConstr(
                    gp.quicksum(self.x[i, s] for s in sessions_b[b]) <= 1,
                    name=f"one_session_per_block_{i}_{b}"
                )

        # Pair covered only if assigned interpreter knows both languages
        for s in sessions:
            langs = sessions_lang[s]
            for l1, l2 in combinations(langs, 2):
                eligible_i = [i for i in interpreters if l1 in interpreters_lang[i] and l2 in interpreters_lang[i]]
                self.model.addConstr(
                    self.y[s, l1, l2] <= gp.quicksum(self.x[i, s] for i in eligible_i),
                    name=f"pair_covering_{s}_{l1}_{l2}"
                )

        # Constraint: c_s = 1 if all pairs are covered
        for s in sessions:
            langs = sessions_lang[s]
            for l1, l2 in combinations(langs, 2):
                self.model.addConstr(
                    self.y[s, l1, l2] >= self.c[s],
                    name=f"session_complete_{s}_{l1}_{l2}"
                )

    def set_objective_OF1(self):
        self.model.setObjective(gp.quicksum(self.y.values()), GRB.MAXIMIZE)

    def set_objective_OF2(self):
        self.model.setObjective(gp.quicksum(self.c.values()), GRB.MAXIMIZE)

    def solve_OF1(self, verbose=True):
        self.build_variables()
        self.add_constraints()
        self.set_objective_OF1()
        self.model.optimize()

        if verbose:
            print("\nSelected assignments:")
            for (i, s), var in self.x.items():
                if var.X > 0.5:
                    print(f"Interpreter {i} assigned to Session {s}")

            print("\nCovered language pairs:")
            for (s, l1, l2), var in self.y.items():
                if var.X > 0.5:
                    print(f"Session {s} covers pair ({l1}, {l2})")

            print("\nTotal pairs covered (OF1):", self.model.ObjVal)

        return self.model.ObjVal

    def solve_OF2(self, verbose=True):
        self.build_variables()
        self.add_constraints()
        self.set_objective_OF2()
        self.model.optimize()

        if verbose:
            print("\nSelected assignments:")
            for (i, s), var in self.x.items():
                if var.X > 0.5:
                    print(f"Interpreter {i} assigned to Session {s}")

            print("\nSessions fully covered:")
            for s, var in self.c.items():
                if var.X > 0.5:
                    print(f"Session {s} is fully covered")

            print("\nTotal sessions fully covered (OF2):", self.model.ObjVal)

        return self.model.ObjVal
