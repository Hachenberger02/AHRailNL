from .hill_climber import Hill_climber
from math import tanh
import random
import copy


class Plant_Propagation(Hill_climber):

    def __init__(self, state: object, valid_states: bool, population_size: int, max_generations: int, max_nr_runners: int):
        super().__init__(state, valid_states)

        self.population_size = population_size
        self.population: list[object] = []

        self.scores: list[float] = []
        self.fitness_values: list[list[float, object]] = []

        self.max_generations = max_generations

        self.max_nr_runners = max_nr_runners
        self.runner_population: list[object] = []

        # choose: valid, random, hill_climber
        self.initial_population_type = 'random'

        # saves overall highest achieved score
        self.high_score: float = 0

        # tournament size (potentially) affects population_filter method
        self.tournament_size = 3

        # choose: best, sequential or random
        self.filter_type = 'sequential'

    ### GENERAL FUNCTIONS ###

    def run(self):
        self.reset()

        # create initial population
        self.initial_population()

        for generation in range(self.max_generations):
            # get all scores of the current population
            self.get_scores()

            print(f"Generation {generation + 1}: {self.high_score}")

            # determine fitness of current population
            converge_status = self.fitness_function()

            # check if population has converged to a certain local optimum
            if converge_status == 'converged':
                return generation

            # create runner
            self.make_runners()

            # update population
            self.filter_population(self.filter_type)

    def reset(self) -> None:
        """
        resets class by clearing all (relevant) variables
        """
        self.scores = []
        self.sorted_fitness_values = []
        self.population = []
        self.runner_population = []
        self.high_score = 0

    def initial_population(self) -> None:
        """
        set the initial population by running a certain amount of hill-climber algorithms  
        """
        type = self.initial_population_type

        if type == 'valid':
            # create population
            for i in range(self.population_size):
                self.state.reset()
                self.create_valid_state()
                self.population.append(copy.deepcopy(self.state))
        elif type == 'random':
            # create population
            for i in range(self.population_size):
                self.state.reset()
                self.create_random_state()
                self.population.append(copy.deepcopy(self.state))

        elif type == 'hill_climber':
            pass

    ### SCORE FUNCTIONS ###

    def get_scores(self) -> None:
        """
        fills self.score with the current population_scores
        """
        for i in range(len(self.population)):
            self.scores.append([self.get_mutated_score(
                self.population[i]), self.population[i]])

    def fitness_function(self):  # None or str
        """
        calulate and the fitness (=normalized score) of the whole population  
        """
        # Extract just the scores from self.scores
        scores_only = [score_state_pair[0] for score_state_pair in self.scores]

        # Now find the max and min scores
        max_score = max(scores_only)
        min_score = min(scores_only)

        # if scores are equal end algorithm by returning exit-statement
        if max_score == min_score:
            print(f'Algorithm converged to a score of: {self.high_score}')
            return 'converged'

        for i in range(len(self.population)):
            score = self.scores[i][0]
            value = (score - min_score) / (max_score - min_score)
            self.fitness_values.append([value, self.scores[i][1]])

    def update_high_score(self, score) -> None:
        """
        updates high-score if applicable
        """
        if score > self.high_score:
            self.high_score = score

    ### POPULATION FUNCTIONS ###

    def filter_population(self, filter_type: str) -> None:
        """
        filters the population and creates the next generation 
        """
        # add runners to population
        self.merge_population()

        # calculate all scores
        self.get_scores()

        # clear population
        self.population = []

        if filter_type == 'best':
            self.filter_population_best_only()

        elif filter_type == 'sequential' or filter_type == 'random':

            tournament_size = self.tournament_size

            if filter_type == 'sequential':
                self.filter_population_sequential(tournament_size)
            else:
                self.filter_population_random(tournament_size)

        self.scores = []
        self.sorted_fitness_values = []

    def filter_population_best_only(self) -> None:
        """
        filters the population based 
        on score
        """
        # sort self.scores
        sorted_scores = sorted(
            self.scores, key=lambda item: item[0], reverse=True)

        # get the highest scoring states
        for state in sorted_scores[:self.population_size]:
            self.population.append(state[1])

        self.update_high_score(sorted_scores[0][0])

    def filter_population_sequential(self, tournament_size: int) -> None:
        """
        sequentially filters the population. 

        TIP: making population_size to be dividable by tournament_size ensures that the whole population will be looked at
        """
        # shuffle the scores list to ensure randomness
        random.shuffle(self.scores)

        # index variable to keep track
        tournament_index = 0

        # loop until population_size is reached or too little scores are left
        while len(self.population) < self.population_size and tournament_index < len(self.scores):

            # select a group
            tournament = self.scores[tournament_index:
                                     tournament_index + tournament_size]

            # pick highest score as winner
            winner = max(tournament, key=lambda x: x[0])

            # update tournament_index
            tournament_index += tournament_size

            # update high-score
            self.update_high_score(winner[0])

            # add winner to population of the next generation
            self.population.append(winner[1])

    def filter_population_random(self, tournament_size: int) -> None:
        """
        filter the best of the original and runner population 
        """
        while len(self.population) < self.population_size:
            # ensure tournament_size doesn't exceed number of remaining states
            current_tournament_size = min(tournament_size, len(self.scores))

            # pick winner of randomly chosen states
            tournament = random.sample(self.scores, current_tournament_size)
            winner = max(tournament, key=lambda x: x[0])

            # update high-score
            self.update_high_score(winner[0])

            # add winner to population of the next generation
            self.population.append(winner[1])

            # remove from scores (so that it is not chosen anymore)
            self.scores.remove(winner)

    def merge_population(self) -> None:
        """
        merge runner and original population
        """
        for runner in self.runner_population:
            self.population.append(runner)

    ### RUNNER METHODS ###

    def make_runners(self):
        """
        creates runner population
        """
        distance_dict = self.generate_runner_distances()

        # loop over population
        for state_index in range(len(self.population)):
            # loop over all runners
            current_state = self.population[state_index]

            for runner_index in range(len(distance_dict[state_index])):
                distance_goal = distance_dict[state_index][runner_index]
                current_runner = copy.deepcopy(current_state)

                self.state = current_runner

                counter = 0

                # TODO: Experimenteren
                while distance_goal > self.likeness(current_state, self.state) or counter < 100:
                    for i in range(distance_goal):
                        if distance_goal > 3:
                            self.make_change_heavy()
                        else:
                            self.make_change_light()
                        counter += 1

                self.runner_population.append(self.state)

    def generate_runner_distances(self):
        """
        Generate all runners distances
        """
        distance_dict = {}

        # loop over the population
        for i in range(len(self.fitness_values)):
            state = self.fitness_values[i][1]
            value = self.fitness_values[i][0]
            amount_of_runners = max(self.calculate_number_of_runners(value), 1)
            distance_dict[i] = []

            # loop over all runners
            for j in range(amount_of_runners):
                distance = self.calculate_distance(value)
                distance_dict[i].append(distance)

        return distance_dict

    def calculate_number_of_runners(self, fitness_value: float) -> int:
        """
        determines the amount of runners per state based on the fitness value
        """
        n_max = self.max_nr_runners
        n_runners = int(n_max * fitness_value)

        return n_runners

    def calculate_distance(self, fitness_value: float) -> float:
        """
        determines a distance (semi-random) based on a fitness-value  
        """
        # TODO: Experimenteren
        scale_factor = 8
        variability = 1
        r = random.random()

        distance = max(int((1 - fitness_value) *
                       scale_factor + int(r * variability)), 1)

        return distance

    def count_route_difference(self, original_state: object, new_state: object):
        """
        counts the route differences between two states
        """
        connections_overlapping = 0
        connections_different = 0

        routes_used = []
        connection_counter = 0

        for original_route in original_state.routes:

            max_overlap = -1
            best_match = None
            original_connections = set(original_route.connection_ids)

            connection_counter += len(original_connections)

            for new_route in new_state.routes:
                if new_route not in routes_used:
                    new_connections = set(new_route.connection_ids)

                    overlap = len(
                        original_connections.intersection(new_connections))

                    if overlap > max_overlap:
                        max_overlap = overlap
                        difference = len(original_connections.symmetric_difference(
                            new_connections))
                        best_match = new_route

            if best_match:
                routes_used.append(best_match)
                connections_different += difference
                connections_overlapping += max_overlap

        proportion = connections_overlapping / connection_counter

        return connections_different, connections_overlapping, proportion

    def likeness(self, original_state: object, new_state: object):
        """
        quantifies the difference between two states
        """
        connections_different, connections_overlapping, proportion = self.count_route_difference(
            original_state, new_state)

        return connections_different
