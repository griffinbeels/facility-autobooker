#!/usr/bin/env python

from __future__ import division
import argparse
import json
import math
from os.path import dirname, realpath
from pyspark import SparkContext
import time
import os

VIRTUAL_COUNT = 10
PRIOR_CORRELATION = 0.0
THRESHOLD = 0.5

##### Metric Functions ############################################################################
def correlation(n, sum_x, sum_y, sum_xx, sum_yy, sum_xy):
    # http://en.wikipedia.org/wiki/Correlation_and_dependence
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt(n * sum_xx - sum_x * sum_x) * math.sqrt(n * sum_yy - sum_y * sum_y)
    if denominator == 0:
        return 0.0
    return numerator / denominator

def regularized_correlation(n, sum_x, sum_y, sum_xx, sum_yy, sum_xy, virtual_count, prior_correlation):
    unregularized_correlation_value = correlation(n, sum_x, sum_y, sum_xx, sum_yy, sum_xy)
    weight = n / (n + virtual_count)
    return weight * unregularized_correlation_value + (1 - weight) * prior_correlation

def cosine_similarity(sum_xx, sum_yy, sum_xy):
    # http://en.wikipedia.org/wiki/Cosine_similarity
    numerator = sum_xy
    denominator = (math.sqrt(sum_xx) * math.sqrt(sum_yy))
    if denominator == 0:
        return 0.0
    return numerator / denominator

def jaccard_similarity(n_common, n1, n2):
    # http://en.wikipedia.org/wiki/Jaccard_index
    numerator = n_common
    denominator = n1 + n2 - n_common
    if denominator == 0:
        return 0.0
    return numerator / denominator
#####################################################################################################

##### util ##########################################################################################
def combinations(iterable, r):
    # http://docs.python.org/2/library/itertools.html#itertools.combinations
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(list(range(r))):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)
#####################################################################################################


def parse_args():
    parser = argparse.ArgumentParser(description='MapReduce similarities')
    parser.add_argument('-d', help='path to data directory', default='./../data/recommendations/small/')
    parser.add_argument('-n', help='number of data slices', default=128)
    parser.add_argument('-o', help='path to output JSON', default="output")
    return parser.parse_args()

# Feel free to create more mappers and reducers.
def mapper0(record):
    return len(record)
    # Key = movie_id
    # value = values in the line
    split_data = record.split("::")
    if len(split_data) == 3: # rating -- user_id, movie_id, rating
        return (split_data[1], [split_data[0], split_data[2]])
    else: # movie -- movie_id, movie_title
        return (split_data[0], [split_data[1]])

def reducer(a, b):
    return a + b # merge everything relevant for this movie title

def mapper1(record):
    # Hint: 
    # INPUT:
    #   record: (key, values)
    #     where -
    #       key: movie_id
    #       values: a list of values in the line
    # OUTPUT:
    #   [(key, value), (key, value), ...]
    #     where -
    #       key: movie_title
    #       value: [(user_id, rating)]
    #
    values = record[1] # all info split into arrays
    name = values[0] # name of the movie is always first value
    for i in range(1, len(values), 2): # pairs of 2 after the movie name
        yield (name, [[values[i], int(values[i + 1])]]) # movie_name as key, [[2 element array user_id, int rating]]
    
# So think about how you could make a list of movies all reviewed by the same person. 
# That list could be stored in the value of a record and then you could call combinations on that value. 
def mapper2(record):
    # key = movie name
    # value = ratings array
    # flat map ... 
    movie_name = record[0]
    ratings = record[1]
    num_ratings = len(ratings)
    for rating in ratings: # rating = [user_id, rating]
        user_id = rating[0]
        val = rating[1]
        yield (user_id, [[movie_name, val, num_ratings]]) # map each user to the movies they've rated

def mapper3(record):
    # key: user_id
    # value: list of [movie_name, rating] pairs, movies rated by this person
    movie_list = record[1]
    for pair in combinations(movie_list, 2):
        movie_1_data = pair[0]
        movie_2_data = pair[1]
        # Only include movie_title2s for a movie_title1
        # when movie_title1 < movie_title2 (i.e. movie_title1 comes alphabetically before movie_title2
        movie_1_name = movie_1_data[0]
        movie_1_rating = movie_1_data[1]
        movie_1_num_ratings = movie_1_data[2]
        movie_2_name = movie_2_data[0]
        movie_2_rating = movie_2_data[1]
        movie_2_num_ratings = movie_2_data[2]
        if (movie_1_name < movie_2_name):
            yield (movie_1_name, movie_2_name), [[movie_1_rating, movie_1_num_ratings, movie_2_rating, movie_2_num_ratings]]
        else:
            yield (movie_2_name, movie_1_name), [[movie_2_rating, movie_2_num_ratings, movie_1_rating, movie_1_num_ratings]]


def mapper4(record):
    # key: (movie1, movie2)
    # value: (array of [movie1rating, movie1_num, movie2_rating, movie_2_num_ratings] tuples)
    movie_1_name = record[0][0]
    movie_2_name = record[0][1]
    ratings = record[1]

    n = len(ratings) # number of shared
    n1 = -1
    n2 = -1

    sum_x = 0 # sum of all movie 1 ratings
    sum_y = 0 # sum of all movie 2 ratings
    sum_xx = 0 # sum of (m1 * m1) ratings
    sum_yy = 0 # sum of (m2 * m2) ratings
    sum_xy = 0 # sum of (m1 * m2) ratings

    # Go through all ratings & hydrate above values
    for rating_pair in ratings:
        movie_1_rating = rating_pair[0]
        if (n1 == -1):
            n1 = rating_pair[1]
        movie_2_rating = rating_pair[2]
        if (n2 == -1):
            n2 = rating_pair[3]

        sum_x = movie_1_rating
        sum_y = movie_2_rating
        sum_xx = (movie_1_rating * movie_1_rating)
        sum_yy = (movie_2_rating * movie_2_rating)
        sum_xy = (movie_1_rating * movie_2_rating)
        yield ((movie_1_name, movie_2_name, n, n1, n2), (sum_x, sum_y, sum_xx, sum_yy, sum_xy))

def filterer(record):
    return record[1][0][2] >= THRESHOLD # record[1] = vals, record[1][0] = first val, record[1][0][2] = the regularized_correlation

def mapper5(record):
    movie_1_name = record[0][0]
    movie_2_name = record[0][1]
    n = record[0][2] # number of shared
    n1 = record[0][3]
    n2 = record[0][4]

    sum_x = record[1][0] # sum of all movie 1 ratings
    sum_y = record[1][1] # sum of all movie 2 ratings
    sum_xx = record[1][2] # sum of (m1 * m1) ratings
    sum_yy = record[1][3] # sum of (m2 * m2) ratings
    sum_xy = record[1][4] # sum of (m1 * m2) ratings

    # I could create an individual mapping step for each of these, but I don't really want to.
    # I feel like there would be marginal gains that would be nice, but it would be 4 additional
    # map + reduce steps. So, instead, I do each stat calculation in one map step.
    regularized_correlation_value = regularized_correlation(n, sum_x, sum_y, sum_xx, sum_yy, sum_xy, VIRTUAL_COUNT, PRIOR_CORRELATION)
    correlation_value = correlation(n, sum_x, sum_y, sum_xx, sum_yy, sum_xy)
    cosine_similarity_value = cosine_similarity(sum_xx, sum_yy, sum_xy)
    jaccard_similarity_value = jaccard_similarity(n, n1, n2)
    return movie_1_name, [[movie_2_name, correlation_value, regularized_correlation_value, cosine_similarity_value, jaccard_similarity_value, n, n1, n2]]

def adder(a, b):
    # a and b in form of (sum_x, sum_y, sum_xx, sum_yy, sum_xy)
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3], a[4] + b[4])

def mapper6(record):
    # key: movie1
    # value: [movie_2_name, correlation_value, regularized_correlation_value, cosine_similarity_value, jaccard_similarity_value, n, n1, n2]
    movie_1_name = record[0]
    
    for movie_2_data in record[1]:
        movie_2_name = movie_2_data[0]
        correlation_value = movie_2_data[1]
        regularized_correlation_value = movie_2_data[2]
        cosine_similarity_value = movie_2_data[3]
        jaccard_similarity_value = movie_2_data[4]
        n = movie_2_data[5]
        n1 = movie_2_data[6]
        n2 = movie_2_data[7]
        yield ((movie_1_name, movie_2_name), [correlation_value, regularized_correlation_value, cosine_similarity_value, jaccard_similarity_value, n, n1, n2])

def main():
    args = parse_args()
    sc = SparkContext()

    with open(args.d + '/movies.dat', 'r') as mlines:
        data = [line.rstrip() for line in mlines]
    with open(args.d + '/ratings.dat', 'r') as rlines:
        data += [line.rstrip() for line in rlines]

    # Implement your mapper and reducer function according to the following query.
    # stage1_result represents the data after it has been processed at the second
    # step of map reduce, which is after mapper1.
    stage1_result = sc.parallelize(data, args.n).flatMap(mapper0)

    print(stage1_result.collect())

    if not os.path.exists(args.o):
        os.makedirs(args.o)

    # Store the stage1_output
    with open(args.o  + '/netflix_stage1_output.json', 'w') as outfile:
        json.dump(stage1_result.collect(), outfile, separators=(',', ':'))

    # # TODO: continue to build the pipeline
    # # Pay attention to the required format of stage2_result 
    # stage2_result = stage1_result.flatMap(mapper2) \
    #                              .reduceByKey(reducer) \
    #                              .flatMap(mapper3) \
    #                              .reduceByKey(reducer) \
    #                              .flatMap(mapper4) \
    #                              .reduceByKey(adder) \
    #                              .map(mapper5) \
    #                              .filter(filterer) \
    #                              .reduceByKey(reducer)

    # # Store the stage2_output
    # with open(args.o  + '/netflix_stage2_output.json', 'w') as outfile:
    #     json.dump(stage2_result.collect(), outfile, separators=(',', ':'))

    # # # TODO: continue to build the pipeline
    # final_result = stage2_result.flatMap(mapper6).collect()

    # with open(args.o + '/netflix_final_output.json', 'w') as outfile:
    #     json.dump(final_result, outfile, separators=(',', ':'))

    sc.stop()

if __name__ == '__main__':
    main()
