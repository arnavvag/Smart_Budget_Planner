import numpy as np
import pandas as pd


class GeneticBudgetOptimizer:
    def __init__(self, categories: pd.DataFrame, budget: float,
                 pop_size: int = 150, crossover_prob: float = 0.9,
                 mutation_prob: float = 0.2, random_state: int = None):

        self.categories = categories.reset_index(drop=True).copy()
        self.budget = float(budget)
        self.n = len(self.categories)
        self.pop_size = pop_size
        self.crossover_prob = crossover_prob
        self.base_mutation_prob = mutation_prob
        self.rng = np.random.default_rng(random_state)

        # Normalize category constraints
        self.categories['min_frac'] = (self.categories['min'] / self.budget).clip(0, 1)
        self.categories['max_frac'] = (self.categories['max'] / self.budget).replace([np.nan, 0], 1.0).clip(0, 1)

    # --------------------------
    # Population Initialization
    # --------------------------
    def _init_population(self):
        pop = []
        min_fracs = self.categories['min_frac'].values
        free_budget = 1.0 - min_fracs.sum()
        if free_budget < 0:
            raise ValueError("Sum of minimum category requirements exceed the budget.")

        for _ in range(self.pop_size):
            x = self.rng.random(self.n)
            x = x / x.sum() * free_budget
            alloc = np.minimum(min_fracs + x, self.categories['max_frac'].values)
            alloc = alloc / alloc.sum()
            pop.append(alloc)

        return np.array(pop)

    # --------------------------
    # Fitness Calculation
    # --------------------------
    def _utility(self, frac_alloc):
        amounts = frac_alloc * self.budget
        alpha = self.categories['alpha'].values
        priority = self.categories['priority'].values
        util = priority * (1 - np.exp(-alpha * amounts))
        return util.sum()

    def _penalty(self, frac_alloc):
        min_f = self.categories['min_frac'].values
        max_f = self.categories['max_frac'].values
        below = np.maximum(0.0, min_f - frac_alloc)
        above = np.maximum(0.0, frac_alloc - max_f)
        penalty = (np.sum(below) + np.sum(above)) * 100.0
        penalty += abs(frac_alloc.sum() - 1.0) * 100.0
        return penalty

    def _fitness(self, frac_alloc):
        return self._utility(frac_alloc) - self._penalty(frac_alloc)

    # --------------------------
    # Genetic Operations
    # --------------------------
    def _tournament_selection(self, pop, fitnesses, k=3):
        idx = self.rng.integers(0, len(pop), size=k)
        return pop[idx[np.argmax(fitnesses[idx])]].copy()

    def _crossover(self, parent1, parent2):
        if self.rng.random() < self.crossover_prob:
            beta = self.rng.uniform(0.3, 0.7)
            child1 = beta * parent1 + (1 - beta) * parent2
            child2 = beta * parent2 + (1 - beta) * parent1
        else:
            child1, child2 = parent1.copy(), parent2.copy()

        # Normalize
        child1 = np.clip(child1, 0, None)
        child2 = np.clip(child2, 0, None)
        child1 /= child1.sum()
        child2 /= child2.sum()
        return child1, child2

    def _mutate(self, individual, generation, total_generations):
        # Adaptive mutation: stronger early, weaker later
        adaptive_prob = self.base_mutation_prob * (1 - generation / total_generations)
        if self.rng.random() < adaptive_prob:
            noise = self.rng.normal(0, 0.05, size=self.n)
            individual += noise
            individual = np.clip(individual, 0, None)
            individual /= individual.sum()
        return individual

    # --------------------------
    # Main GA Loop
    # --------------------------
    def run(self, generations=300, verbose=False, elitism=3):
        pop = self._init_population()
        fitnesses = np.array([self._fitness(ind) for ind in pop])
        best_idx = np.argmax(fitnesses)
        best_fit = fitnesses[best_idx]
        best_overall = pop[best_idx].copy()
        best_history = []

        for gen in range(generations):
            # Normalize fitness to avoid domination by one high value
            fitness_norm = (fitnesses - np.min(fitnesses)) / (np.ptp(fitnesses) + 1e-9)
            new_pop = []

            # Elitism: dynamically adjust count based on convergence
            elite_count = max(1, int(elitism * (1 - gen / generations)))
            elites = pop[fitnesses.argsort()[-elite_count:]]
            new_pop.extend(elites)

            while len(new_pop) < self.pop_size:
                p1 = self._tournament_selection(pop, fitness_norm)
                p2 = self._tournament_selection(pop, fitness_norm)
                c1, c2 = self._crossover(p1, p2)
                c1 = self._mutate(c1, gen, generations)
                c2 = self._mutate(c2, gen, generations)
                new_pop.extend([c1, c2])

            pop = np.array(new_pop[:self.pop_size])
            fitnesses = np.array([self._fitness(ind) for ind in pop])

            gen_best_idx = np.argmax(fitnesses)
            gen_best_fit = fitnesses[gen_best_idx]
            if gen_best_fit > best_fit:
                best_fit = gen_best_fit
                best_overall = pop[gen_best_idx].copy()
            best_history.append(best_fit)

            if verbose and (gen % max(1, generations // 10) == 0 or gen == generations - 1):
                print(f"Generation {gen+1}/{generations} | Best fitness: {best_fit:.4f}")

        allocation_amounts = (best_overall * self.budget).round(2)
        alloc_series = pd.Series(data=allocation_amounts, index=self.categories['name'].values)

        return {
            'allocation': alloc_series.to_dict(),
            'fitness': float(best_fit),
            'history': best_history
        }
