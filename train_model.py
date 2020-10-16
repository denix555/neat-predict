#!/usr/bin/env python3

from __future__ import print_function
import os
import neat
import pickle


import pandas as pd
import numpy as np
from math import floor


def d_scale(data):
    return (data - data.mean()) / (data.max() - data.min())


def d_split(data, train_size):
    train_data = data.iloc[0:floor(train_size * len(data))]
    test_data = data.iloc[floor(train_size * len(data)):]

    return train_data, test_data


def d_strip(data):
    if len(data) % 30 != 0:
        n = len(data) + (30 - len(data) % 30)
        n -= 30
    else:
        n = len(data) - 30
    return data.iloc[:n + 1, :]


train = test = data = x_train = y_train = x_test = y_test = None


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        cost = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        for index in range(len(y_train)):
            predicted_output = net.activate(x_train[index])
            cost += (predicted_output[0] - y_train[index]) ** 2
        genome.fitness = -cost


def run(config_file):

    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)


    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)


    p.add_reporter(neat.StdOutReporter(False))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)


    # Run for up to 300 generations.
    winner = p.run(eval_genomes, 300)

    # Save model
    with open(os.path.join(local_dir,'model-feedforward'),'wb') as f:
        pickle.dump(winner,f)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)


    predicted = []
    for xi, xo in zip(x_test, y_test):
        output = winner_net.activate(xi)
        predicted.append(output)    
    


################################################################################

 
if __name__ == '__main__':

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward')
    data = pd.read_csv(os.path.join(local_dir,'ALTBTC.csv'))


    # Preprocess data
    data = d_scale(data)  # scale
    train, test = d_split(data, train_size=.9)  # split into training and testing data
    train = d_strip(train)
    test = d_strip(test)

    x_train = [[train.iloc[i]['Close'] for i in range(index, index + 30)] for index in range(0, len(train) - 30)]
    y_train = [train.iloc[i]['Close'] for i in range(30, len(train))]
    x_test = [[test.iloc[i]['Close'] for i in range(index, index + 30)] for index in range(0, len(test) - 30)]
    y_test = [test.iloc[i]['Close'] for i in range(30, len(test))]
   
    run(config_path)


