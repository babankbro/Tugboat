import numpy as np
from pymoo.core.problem import ElementwiseProblem
import math

from CodeVS.components.solution import Solution

class TugboatProblem(ElementwiseProblem):
    
    def __init__(self, data, solution, N):
        self.N = N
        self.solution = solution
        self.data_lookup = data
        print("Number Code Tugboat", N, self.data_lookup.keys())
        super().__init__(n_var=self.N, n_obj=1, n_constr=0, xl=0, xu=1)

    def _function_cost(self, x):
        x = x[0]
        return x*x - 0.5

    def _evaluate(self, x, out, *args, **kwargs):
        
        #f = self._function_cost(x)
        solution = Solution(self.data_lookup)
        tugboat_df, barge_df = solution.generate_schedule(self.data_lookup['orders'].keys(), xs=x)
        cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_cost(tugboat_df, barge_df)

        out["hash"] = hash(str(x))
        out["F"] = np.sum(tugboat_df_grouped['cost'])