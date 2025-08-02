

#from numpy.core.memmap import uint8
import numpy as np

class AdaptiveWeight:
    def __init__(self, N, Max_iter, F, K):
        self.Ns = np.zeros(( Max_iter+1, N))
        self.As = np.zeros(( Max_iter+1, N))
        self.Is = np.zeros(( Max_iter+1, N))
        self.Iter = 0
        self.Max_iter = Max_iter
        self.N_track = N
        self.pobWeights = np.ones((N,))/N
        self.weights = np.ones((N,))
        self.Ns[0] = np.ones((N,))
        self.As[0] = np.ones((N,))
        self.Is[0] = np.ones((N,))
        self.F = F
        self.K = K
        self.listIndexs = list(np.arange(N, dtype=np.uint8))

    def random_tracks(self, size):
        tracksIds = np.random.choice(self.listIndexs, size, p=self.pobWeights)
        return tracksIds

    def update(self, tracks, objects, bestI):
        self.Iter += 1
        self.Is[self.Iter, bestI] = 1
        for i in range(self.N_track):
            indexs = np.where(tracks==i)[0]
            self.Ns[self.Iter, i] = len(indexs)
            self.As[self.Iter, i] = np.mean(objects[indexs])
            if len(indexs) == 0:
                self.As[self.Iter, i] = 0
            Ii = np.sum(self.Is[:self.Iter, i])

            new_weight = (self.F*self.Ns[self.Iter, i] + 
                              (1-self.F)*self.As[self.Iter, i] + self.K*Ii)
            self.weights[i] =  max(0.3*self.weights[i] + 0.7*new_weight, 0)
        total = np.sum(self.weights)
        #print(self.weights, total)
        for i in range(self.N_track):
            self.pobWeights[i] = self.weights[i]/total


class AMIS:
    def __init__(self, problem, pop_size,  max_iter, CR=0.3, CRT=0.2, F1=0.6, F2=0.4, lo=0.5):
        self.pop_size = pop_size
        self.CR = CR
        self.problem = problem
        self.max_iter = max_iter
        self.Xs = None
        self.fitnessXs = None
        self.bestX = None
        self.best2X = None
        self.CRT = CRT
        self.bestFitness = 0
        self.F1 = F1
        self.F2 = F2
        self.lo = lo
        self.data = np.zeros((3*max_iter, self.problem.n_var))
        self.out = {}
        self.initialize()
        self.N_blackboxs = 8
        self.adaptiveWeight = AdaptiveWeight(self.N_blackboxs, max_iter, 0.05, 1)

    def initialize(self):
        self.Xs = np.random.rand( self.pop_size, self.problem.n_var)
        self.fitnessXs = np.zeros((self.pop_size,))
        self.cal_fitness()
        min_index = np.argmin(self.fitnessXs)
        self.bestX = np.copy(self.Xs[min_index])
        self.best2X = np.copy(self.bestX)
        self.bestFitness = self.fitnessXs[min_index]
        for t in range(1):
            print("Initial best",min_index, self.bestFitness)
            self.problem._evaluate(self.bestX, self.out)
            print("Initial best", self.out['F'])
            self.problem._evaluate(self.Xs[min_index], self.out)
            z = np.sum(self.bestX-self.Xs[min_index])
            print("Initial xs", min_index, self.out['F'], z)

    def cal_fitness(self):
        for i in range(self.pop_size):
            self.problem._evaluate(self.Xs[i], self.out)
            self.fitnessXs[i] = self.out['F']
            #print("Test",i, self.out['F'])
            
    def IB1_best(self, xs):
        N = len(xs)
        indexs = np.arange(0, self.pop_size, 1).astype(dtype=np.uint8)
        index_r1s = list(np.copy(indexs))
        index_r2s = list(np.copy(indexs))
        index_r3s = list(np.copy(indexs))
        np.random.shuffle(index_r1s)
        np.random.shuffle(index_r2s)
        np.random.shuffle(index_r3s)
        Vs = self.lo*self.Xs[index_r1s[:N]] + self.F1*(self.bestX - self.Xs[index_r1s[:N]]) +\
                                              self.F2*(self.Xs[index_r2s[:N]] - self.Xs[index_r3s[:N]])
        
        vmin = np.min(Vs)
        vmax = np.max(Vs)
        if vmin != vmax:
            Vs = (Vs-vmin)/(vmax-vmin)
        return Vs


    def IB2_best2(self, xs):
        N = len(xs)
        indexs = np.arange(0, self.pop_size, 1).astype(dtype=np.uint8)
        index_r1s = list(np.copy(indexs))
        index_r2s = list(np.copy(indexs))
        index_r3s = list(np.copy(indexs))
        np.random.shuffle(index_r1s)
        np.random.shuffle(index_r2s)
        np.random.shuffle(index_r3s)
        Vs = self.Xs[index_r1s[:N]] + self.F1*(self.bestX - self.Xs[index_r1s[:N]]) +\
                                              self.F2*(self.best2X - self.Xs[index_r1s[:N]])
        
        vmin = np.min(Vs)
        vmax = np.max(Vs)
        if vmin != vmax:
            Vs = (Vs-vmin)/(vmax-vmin)
        return Vs

    def IB3_DE(self, xs):
        N = len(xs)
        indexs = np.arange(0, self.pop_size, 1).astype(dtype=np.uint8)
        index_r1s = list(np.copy(indexs))
        index_r2s = list(np.copy(indexs))
        index_r3s = list(np.copy(indexs))
        np.random.shuffle(index_r1s)
        np.random.shuffle(index_r2s)
        np.random.shuffle(index_r3s)
        Vs = self.Xs[index_r1s[:N]] + self.F1*(self.best2X - self.Xs[index_r1s[:N]])
        
        vmin = np.min(Vs)
        vmax = np.max(Vs)
        if vmin != vmax:
            Vs = (Vs-vmin)/(vmax-vmin)
        return Vs

    def IB4_DER(self, xs):
        N = len(xs)
        indexs = np.arange(0, self.pop_size, 1).astype(dtype=np.uint8)
        index_r1s = list(np.copy(indexs))
        index_r2s = list(np.copy(indexs))
        index_r3s = list(np.copy(indexs))
        np.random.shuffle(index_r1s)
        np.random.shuffle(index_r2s)
        np.random.shuffle(index_r3s)
        Vs = self.Xs[index_r1s[:N]] + np.random.rand()*(self.best2X - self.Xs[index_r1s[:N]])
        
        vmin = np.min(Vs)
        vmax = np.max(Vs)
        if vmin != vmax:
            Vs = (Vs-vmin)/(vmax-vmin)
        return Vs

    def IB5_random(self, xs):
        N = len(xs)
        rs = np.random.rand(xs.shape[0], xs.shape[1])
        cross_select = np.random.choice(a=[0, 1], size=xs.shape, p=[self.CRT, 1-self.CRT])  
        Vs = rs
        return Vs
    
    
    def IB6_random_transit(self, xs):
        N = len(xs)
        rs = np.random.rand(xs.shape[0], xs.shape[1])
        cross_select = np.random.choice(a=[0, 1], size=xs.shape, p=[self.CRT, 1-self.CRT])  
        Vs = (1-cross_select)*xs + cross_select*rs
        return Vs
    
    def IB7_best_transit(self, xs):
        N = len(xs)
        rs = np.random.rand(xs.shape[0], xs.shape[1])
        cross_select = np.random.choice(a=[0, 1], size=xs.shape, p=[self.CRT, 1-self.CRT])  
        Vs = (1-cross_select)*xs + cross_select*self.bestX
        return Vs

    def IB8_scale(self, xs):
        N = len(xs)
        rs = np.random.rand(xs.shape[0], xs.shape[1])
        cross_select = np.random.choice(a=[0, 1], size=xs.shape, p=[self.CRT, 1-self.CRT])  
        Vs =  ((1 - cross_select)*rs)*xs +   cross_select*xs
        return Vs

    def select_blocks(self):
        self.Vs = np.copy(self.Xs)
        for i in range(self.N_blackboxs):
            indexI = list(np.where(self.currentTracks == i)[0])
            if len(indexI) == 0:
                continue
            if i == 0:
                self.Vs[indexI] = self.IB1_best(self.Xs[indexI])
            elif i==1:
                self.Vs[indexI] = self.IB2_best2(self.Xs[indexI])
            elif i==2:
                self.Vs[indexI] = self.IB3_DE(self.Xs[indexI])
            elif i==3:
                self.Vs[indexI] = self.IB4_DER(self.Xs[indexI])
            elif i==4:
                self.Vs[indexI] = self.IB5_random(self.Xs[indexI])
            elif i == 5:
                self.Vs[indexI] = self.IB6_random_transit(self.Xs[indexI])
            elif i==6:
                self.Vs[indexI] = self.IB7_best_transit(self.Xs[indexI])
            elif i==7:
                self.Vs[indexI] = self.IB8_scale(self.Xs[indexI])
            
            

    def recombination(self):
        cross_select = np.copy( np.random.choice(a=[0, 1], size=self.Xs.shape, p=[self.CR, 1-self.CR]))  
        self.Us = (1-cross_select)*self.Xs + cross_select*self.Vs
        
    def accept_all(self):
        fitnessUs = np.zeros((self.pop_size,))
        select_mask = np.zeros((self.pop_size,))
        for i in range(self.pop_size):
            self.problem._evaluate(self.Us[i], self.out)
            fitnessUs[i] = self.out['F']
            self.fitnessXs[i] = fitnessUs[i]
            self.Xs[i] = np.copy(self.Us[i])
            if fitnessUs[i] < self.bestFitness:
                self.bestFitness = fitnessUs[i]
                self.best2X = np.copy(self.bestX)
                self.bestX = np.copy(self.Us[i])

    def selection(self):
        fitnessUs = np.zeros((self.pop_size,))
        select_mask = np.zeros((self.pop_size,))
        for i in range(self.pop_size):
            self.problem._evaluate(self.Us[i], self.out)
            fitnessUs[i] = self.out['F']
            
            #self.problem._evaluate(self.Xs[i], self.out)
            #temp = self.out['F']
            #self.fitnessXs[i] = temp
            delta = fitnessUs[i] - self.fitnessXs[i]
            #print("u", i, fitnessUs[i], temp, self.fitnessXs[i], delta)
            
            if (delta < 0 
                #or np.random.rand() + 5 < np.exp(-delta*100) 
                #or np.random.rand()  < 0.00001
                ):
                self.fitnessXs[i] = fitnessUs[i]
                self.Xs[i] = np.copy(self.Us[i])
                if fitnessUs[i] < self.bestFitness:
                    self.bestFitness = fitnessUs[i] 
                    self.best2X = np.copy(self.bestX)
                    self.bestX = np.copy(self.Us[i])
                    



    def iterate(self):
        for it in range(self.max_iter):
            #print("000000000000000000000000000000000")
            self.currentTracks = self.adaptiveWeight.random_tracks(self.pop_size)
            self.select_blocks()
            arg_min = np.argmin(self.fitnessXs)
            self.adaptiveWeight.update(self.currentTracks, self.fitnessXs, self.currentTracks[arg_min])
            self.recombination()
            self.selection()

            idx= np.argsort(self.bestX)

            print(it, round(np.mean(self.fitnessXs), 4), round(self.bestFitness, 4), self.adaptiveWeight.pobWeights)
            arg_maxs = np.argsort(self.fitnessXs)
            self.data[it*3:3*(it+1)] = np.copy(self.Xs[arg_maxs[:3]])
            self.problem._evaluate(self.bestX, self.out)
            #print("Inner Test", self.out['F'], self.fitnessXs[arg_min])
            self.cal_fitness()