import numpy as np
from pymoo.core.problem import ElementwiseProblem
import math

class SampleProblem(ElementwiseProblem):
    
    def __init__(self, N):
        self.N = N
        super().__init__(n_var=self.N, n_obj=1, n_constr=0, xl=0, xu=1)

    def _function_cost(self, x):
        x = x[0]
        return x*x - 0.5

    def _evaluate(self, x, out, *args, **kwargs):
        
        f = self._function_cost(x)
        

        out["hash"] = hash(str(x))
        out["F"] = f
        #out["pheno"] = {"values": solution}