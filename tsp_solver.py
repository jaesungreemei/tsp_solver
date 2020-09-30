import random
import math
import argparse
import csv

#######################################################################################
# PARAMETERS
#######################################################################################

POPULATION_SIZE = 100
GENERATIONS = 10
CROSSOVER_OPERATOR = 'CX1'
MUTATION_OPERATOR = 'swapMutate'

SELECTION_PRESSURE = 50
MUTATION_RATE = 0.5
ELITISM_PROPORTION = 0.2


#######################################################################################
# INITIALIZE DATA
#######################################################################################

# Location is represented by dictionary: key = int index, value = tuple(float x, float y)
def preProcess(fileName):
    with open(fileName, 'r') as f:
        coordinates = f.readlines()

        locations = list(map(
            lambda x: [l for l in x.strip().split()],
            coordinates
        ))

        start = locations.index(['NODE_COORD_SECTION'])
        end = locations.index(['EOF'])
        
        locations = list(map(
            lambda x: (int(x[0]), (float(x[1]), float(x[2]))),
            locations[start+1:end]
        ))

        locations_dict = dict(zip(
            [x[0] for x in locations],
            [y[1] for y in locations]
        ))
        
        return locations_dict

# Create Random Population
def initPopulation(locations):
    inOrder = list(locations.keys())
    POPULATION = []

    for i in range(POPULATION_SIZE):
        random.shuffle(inOrder)
        POPULATION.append(inOrder[:])
    
    return POPULATION


#######################################################################################
# FITNESS EVALUATION, INDIVIDUAL SAMPLING
#######################################################################################

# Calculate Total Distance of Path
def calcDistance(locations, order):
    totalDist = 0
    for i in range(len(order)-1):
        locationA = locations[order[i]]
        locationB = locations[order[i+1]]

        dist = math.sqrt((locationA[0] - locationB[0])**2 + (locationA[1] - locationB[1])**2)
        totalDist += dist
    return totalDist

# Tournament Selection: Sample individuals according to selection probabilities
def tournament_selection(locations, POPULATION):
    global SELECTION_PRESSURE
    mating_pool = random.sample(POPULATION, SELECTION_PRESSURE)
    mating_pool = sorted(
        mating_pool,
        key = lambda x: calcDistance(locations, x)
    )
    return mating_pool[0]


#######################################################################################
# CROSSOVER
#######################################################################################

# Crossover: Cycle Crossover Algorithm (CX1)
def CX1(parent1, parent2):
    offspring1 = [x for x in parent2]
    offspring2 = [x for x in parent1]

    i = 0
    nextIndex = -1

    offspring1[i] = parent1[i]
    offspring2[i] = parent2[i]

    while(nextIndex != 0):
        nextIndex = parent1.index(parent2[i])
        offspring1[nextIndex] = parent1[nextIndex]
        offspring2[nextIndex] = parent2[nextIndex]
        i = nextIndex

    return offspring1, offspring2

# Crossover: Modified Cycle Crossover Algorithm (CX2)
def CX2(parent1, parent2):
    offspring1 = []
    offspring2 = []

    O1_index = 0
    O2_index = 0

    while(True):
        offspring1.append(parent2[O1_index])
        O2_index = parent1.index(
            parent2[
                parent1.index(parent2[O1_index])
            ]
        )
        offspring2.append(parent2[O2_index])
        O1_index = parent1.index(parent2[O2_index])

        if(parent1[0] in offspring2):
            break

    if(len(offspring1) != len(parent1)):
        sub_parent1 = list(filter(
            lambda x: (x not in offspring1),
            parent1
        ))
        sub_parent2 = list(filter(
            lambda x: (x not in offspring2),
            parent2
        ))

        if(set(sub_parent1) == set(sub_parent2)):
            nextSection1, nextSection2 = CX2(sub_parent1, sub_parent2)
        else:
            nextSection1, nextSection2 = sub_parent1, sub_parent2
    
        offspring1 += nextSection1
        offspring2 += nextSection2
  
    return offspring1, offspring2

# CROSSOVER OPERATOR
def crossover(parent1, parent2):
    if(CROSSOVER_OPERATOR == 'CX1'):
        return CX1(parent1, parent2)
    elif(CROSSOVER_OPERATOR == 'CX2'):
        return CX2(parent1, parent2)


#######################################################################################
# MUTATION
#######################################################################################

# Mutation: Swap
def swapMutate(path):
    num = len(path) - 1
    if(random.random() < MUTATION_RATE):
        a = random.randint(0, num)
        b = random.randint(0, num)
        while(a == b):
            b = random.choice(path)

        path[a], path[b] = path[b], path[a]
    return path

# Mutation: Reverse Sequence Mutation (RSM)
def RSM(path):
    num = len(path) - 1
    if(random.random() < MUTATION_RATE):
        a = random.randint(0, num)
        b = random.randint(0, num)

        while(a == b):
            b = random.choice(path)
        if (b < a):
            a, b = b, a

        reverse = list(reversed(path[a:b]))
        path = path[:a] + reverse + path[b:]
    return path

# MUTATION OPERATOR
def mutate(path):
    if(MUTATION_OPERATOR == 'swapMutate'):
        return swapMutate(path)
    if(MUTATION_OPERATOR == 'RSM'):
        return RSM(path)


#######################################################################################
# GENERATIONAL SELECTION
#######################################################################################

# Picking the Next Generation: Elitism
def nextGen(POPULATION, OFFSPRING, locations):
    eliteNum = int(len(POPULATION)*ELITISM_PROPORTION)
    bestPopulation = sorted(
        POPULATION,
        key = lambda individual: calcDistance(locations, individual)
    )[:eliteNum]

    bestOffspring = sorted(
        OFFSPRING,
        key = lambda individual: calcDistance(locations,individual)
    )[:(POPULATION_SIZE - eliteNum)]

    newPOPULATION = sorted(
        bestPopulation + bestOffspring,
        key = lambda individual: calcDistance(locations,individual)
    )

    return newPOPULATION, bestPopulation[0], bestOffspring[0]


#######################################################################################
# GENETIC ALGORITHM IMPLEMENTATION
#######################################################################################

def _readFlags():
    parser = argparse.ArgumentParser()
    parser.add_argument('fileName')
    parser.add_argument("-p", "--population", dest='population', default=100, help='POPULATION SIZE', type=int)
    parser.add_argument("-f", "--fitness", dest='generations', default=100, help='FITNESS EVALUATIONS', type=int)
    parser.add_argument("-m", "--mutate", dest='mutate', default='swapMutate', help='MUTATION OPERATOR')
    parser.add_argument("-x", "--crossover", dest='crossover', default='CX1', help='CROSSOVER OPERATOR')

    args = parser.parse_args()
    return args

def saveFile(BEST_PATH):
    BEST_PATH = [[x] for x in BEST_PATH]
    with open('solution.csv', 'w', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerows(BEST_PATH)

def ga():
    global POPULATION_SIZE
    global GENERATIONS
    global MUTATION_OPERATOR
    global CROSSOVER_OPERATOR

    args = _readFlags()
    POPULATION_SIZE = args.population
    GENERATIONS = args.generations
    MUTATION_OPERATOR = args.mutate
    CROSSOVER_OPERATOR = args.crossover

    BEST_PATH = None

    # Data Pre-Processing
    locations = preProcess(args.fileName)

    # [Initialisation] Create initial random population
    POPULATION = initPopulation(locations)

    # [Generations] Run through evolution multiple times
    for g in range(GENERATIONS):
        print(g+1)
        OFFSPRING = []
        while(len(OFFSPRING) < POPULATION_SIZE):
            # [Sample Individuals] Tournament Selection
            parent1 = tournament_selection(locations, POPULATION)
            parent2 = tournament_selection(locations, POPULATION)

            # [Crossover Operator] CX1 or CX2
            offspring1, offspring2 = crossover(parent1, parent2)

            # [Mutation Operator] Swap or RSM
            offspring1 = mutate(offspring1)
            offspring2 = mutate(offspring2)

            OFFSPRING.append(offspring1)
            OFFSPRING.append(offspring2)

        newPOPULATION, bestPOPULATION, bestOFFSPRING = nextGen(POPULATION, OFFSPRING, locations)
        bestPOPULATION = calcDistance(locations, bestPOPULATION)
        bestOFFSPRING = calcDistance(locations, bestOFFSPRING)
        BEST_PATH = newPOPULATION[0]

        print("Generation: %d, OFFSPRING size: %d, Best Population Fitness: %f, Best Offspring Fitness: %f, Offspring Better?: %s" %(g+1, len(OFFSPRING), bestPOPULATION, bestOFFSPRING, str(bestOFFSPRING < bestPOPULATION)))
        print("Generation %d Best Path Length: %f" %(g, calcDistance(locations, BEST_PATH)))
        print("Next Generation Size: %d" %(len(newPOPULATION)))
        POPULATION = newPOPULATION
    
    saveFile(BEST_PATH)
    
if __name__ == '__main__':
    ga()