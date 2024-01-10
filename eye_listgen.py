import random
from math import cos, sin, sqrt, pi, radians
import colorsys

# list generation
def gen_eyedot_blocks(config):
    if config.RANDOM_VALIDATION_TARGETS == True:
        dot_blocks = []
        for block in range(config.NUM_BLOCKS):
            block_store = []
            for rep in range(config.NUM_TRIALS):
                x = random.uniform(config.LOW_RANGE, config.UPPER_RANGE)
                y = random.uniform(config.LOW_RANGE, config.UPPER_RANGE)
                h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
                # r,g,b = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
                # color = (r,g,b)
                color = config.VALIDATION_COLOR
                block_store.append([x,y,color])
            dot_blocks.append(block_store)
    else:
        color = config.VALIDATION_COLOR
        targets = [[0.15, 0.5,color],
                   [0.85, 0.5,color],
                   [0.1, 0.1,color],
                   [0.9, 0.9,color],
                   [0.5, 0.1,color],
                   [0.1, 0.9,color],
                   [0.5, 0.9,color],
                   [0.9, 0.1,color],
                   [0.5, 0.5,color]]
        dot_blocks = []
        for block in range(config.NUM_BLOCKS):
            block_store = []
            for i in range(len(targets)):
                targets[i][0] = targets[i][0] + random.uniform(-0.05,0.05)
                targets[i][1] = targets[i][1] + random.uniform(-0.05,0.05)
                block_store.append(targets[i])
            dot_blocks.append(block_store)
    return dot_blocks
