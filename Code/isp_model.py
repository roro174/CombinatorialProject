"""
Project of Combinatorial Optimization: ISP problem
Main of the project
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
    def __init__(self, json_handler, use_operational_constraints=False, use_bridging=False):
        self.data = json_handler
        self.model = gp.Model("ISP_Model")
        self.all_pairs_in_session = {}
        self.x = None
        self.y = None
        self.c = None
        self.w = None
        self.z = None
        self.u = None
        self._build_variables(use_operational_constraints, use_bridging)
        self._add_constraints(use_bridging)
        if use_operational_constraints:
            self._constraints_operational()
        if use_bridging:
            self._bridge_constraints()

    def _build_variables(self, use_operational_constraints, use_bridging):
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_lang = self.data.get_sessions_lang()
        languages = self.data.get_languages()

        if use_operational_constraints:
            self.w = self.model.addVars(interpreters, blocks, vtype=GRB.BINARY, name="w")
        if use_bridging:
            self.z = {}
            for s in sessions:
                langs = sessions_lang[s]
                for l1, l2 in combinations(langs, 2):
                    for l0 in languages:
                        if l0 != l1 and l0 != l2:
                            self.z[s, l0, l1, l2] = self.model.addVar(vtype=GRB.BINARY, name=f"z_{s}_{l0}_{l1}_{l2}")

        self.u = self.model.addVars(sessions, languages, vtype=GRB.BINARY, name="u")
        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")
        self.c = self.model.addVars(sessions, vtype=GRB.BINARY, name="c")

        self.all_pairs_in_session = {
            s: list(combinations(sessions_lang[s], 2)) for s in sessions
        }

        self.y = self.model.addVars(
            [(i, s, l1, l2) for s in sessions
                            for (l1, l2) in self.all_pairs_in_session[s]
                            for i in interpreters],
            vtype=GRB.BINARY, name="y"
        )

    def _add_constraints(self, use_bridging):
        interpreters = self.data.get_interpreters()
        interpreters_lang = self.data.get_interpreters_lang()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()
        sessions = self.data.get_sessions()
        sessions_lang = self.data.get_sessions_lang()
        languages = self.data.get_languages()

        for b in blocks:
            for i in interpreters:
                self.model.addConstr(
                    gp.quicksum(self.x[i, s] for s in sessions_b[b]) <= 1,
                    name=f"one_session_per_block_{i}_{b}"
                )

        for i in interpreters:
            for s in sessions:
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2] for (l1, l2) in self.all_pairs_in_session[s]) <= 1,
                    name=f"one_pair_per_interpreter_{i}_{s}")
                for (l1, l2) in self.all_pairs_in_session[s]:
                    self.model.addConstr(self.y[i, s, l1, l2] <= self.x[i, s], name=f"coverage_if_assigned_{i}_{s}_{l1}_{l2}")
                    if l1 not in interpreters_lang[i] or l2 not in interpreters_lang[i]:
                        self.model.addConstr(self.y[i, s, l1, l2] == 0, name=f"valid_languages_{i}_{s}_{l1}_{l2}")

        for s in sessions:
            for l1, l2 in self.all_pairs_in_session[s]:
                bridging_term = gp.quicksum(self.z[s, l0, l1, l2] for l0 in languages if self.z and (s, l0, l1, l2) in self.z)
                self.model.addConstr(
                    gp.quicksum(self.y[i, s, l1, l2] for i in interpreters) + bridging_term <= 1,
                    name=f"unique_coverage_{s}_{l1}_{l2}"
                )

        for s in sessions:
            for lang in sessions_lang[s]:
                y_term = gp.quicksum(self.y[i, s, l1, l2] for i in interpreters for (l1, l2) in self.all_pairs_in_session[s] if l1 == lang or l2 == lang)
                z_term = gp.quicksum(self.z[s, l0, l1, l2] for (l1, l2) in self.all_pairs_in_session[s] for l0 in languages if (l1 == lang or l2 == lang) and l0 != l1 and l0 != l2 and (s, l0, l1, l2) in self.z)
                self.model.addConstr(y_term + z_term >= self.u[s, lang], name=f"language_covered_{s}_{lang}")
                self.model.addConstr(self.u[s, lang] >= self.c[s], name=f"c_implies_u_{s}_{lang}")

            self.model.addConstr(
                gp.quicksum(self.u[s, lang] for lang in sessions_lang[s]) >= len(sessions_lang[s]) * self.c[s],
                name=f"all_langs_for_c_{s}"
            )

    def _constraints_operational(self):
        interpreters = self.data.get_interpreters()
        sessions = self.data.get_sessions()
        blocks = self.data.get_blocks()
        sessions_b = self.data.get_sessions_blocks()

        for i in interpreters:
            self.model.addConstr(
                gp.quicksum(self.x[i, s] for s in sessions) <= 15,
                name=f"max_15_sessions_{i}"
            )

        for b in blocks:
            for i in interpreters:
                for s in sessions_b[b]:
                    self.model.addConstr(self.w[i, b] >= self.x[i, s], name=f"link_x_w_lower_{i}_{b}_{s}")
                self.model.addConstr(
                    self.w[i, b] <= gp.quicksum(self.x[i, s] for s in sessions_b[b]),
                    name=f"link_x_w_upper_{i}_{b}"
                )

        for i in interpreters:
            for j in range(len(blocks) - 3):
                self.model.addConstr(
                    self.w[i, blocks[j]] + self.w[i, blocks[j+1]] + self.w[i, blocks[j+2]] + self.w[i, blocks[j+3]] <= 3,
                    name=f"no_4_consecutive_blocks_{i}_{j}"
                )

    def _bridge_constraints(self):
        interpreters = self.data.get_interpreters()
        interpreters_lang = self.data.get_interpreters_lang()

        for (s, l0, l1, l2), var in self.z.items():
            eligible_i1 = [i for i in interpreters if l1 in interpreters_lang[i] and l0 in interpreters_lang[i]]
            eligible_i2 = [i for i in interpreters if l2 in interpreters_lang[i] and l0 in interpreters_lang[i]]

            self.model.addConstr(var <= gp.quicksum(self.x[i, s] for i in eligible_i1), name=f"z_cover_1_{s}_{l0}_{l1}_{l2}")
            self.model.addConstr(var <= gp.quicksum(self.x[i, s] for i in eligible_i2), name=f"z_cover_2_{s}_{l0}_{l1}_{l2}")

            for i in interpreters:
                if l0 in interpreters_lang[i] and l1 in interpreters_lang[i] and l2 in interpreters_lang[i]:
                    self.model.addConstr(self.x[i, s] <= 1 - var, name=f"no_self_bridge_{i}_{s}_{l0}_{l1}_{l2}")

    def _set_objective_of1(self):
        self.model.setObjective(
            gp.quicksum(self.y.values()) + (gp.quicksum(self.z.values()) if self.z else 0), GRB.MAXIMIZE
        )

    def _set_objective_of2(self):
        self.model.setObjective(gp.quicksum(self.c.values()), GRB.MAXIMIZE)

    def solve_of(self, use_of1=True, verbose=True):
        if use_of1:
            self._set_objective_of1()
        else:
            self._set_objective_of2()

        self.model.optimize()

        if self.model.Status not in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
            print("No solution found.")
            return None

        if verbose:
            print("\nSelected assignments:")
            for (i, s), var in self.x.items():
                if var.X > 0.5:
                    print(f"Interpreter {i} assigned to Session {s}")

            if use_of1:
                print("\nCovered language pairs:")
                for (i, s, l1, l2), var in self.y.items():
                    if var.X > 0.5:
                        print(f"Session {s} covers pair ({l1}, {l2})")
                if self.z:
                    print("\nBridged language pairs:")
                    for (s, l0, l1, l2), var in self.z.items():
                        if var.X > 0.5:
                            print(f"Session {s} bridges pair ({l1}, {l2}) via {l0}")
                print("\nTotal pairs covered (OF1):", self.model.ObjVal)
            else:
                print("\nSessions fully covered:")
                for s, var in self.c.items():
                    if var.X > 0.5:
                        print(f"Session {s} is fully covered")
                print("\nTotal sessions fully covered (OF2):", self.model.ObjVal)

        return self.model.ObjVal
