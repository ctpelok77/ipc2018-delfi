#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Executed on Python3
# Requires Keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.optimizers import SGD
from keras.engine.topology import Input
from keras.engine.training import Model
from keras.layers.convolutional import Conv2D, SeparableConv2D
from keras.layers.core import Activation, Dropout, Flatten, Dense
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling2D
from keras.regularizers import l2
from keras.preprocessing.image import ImageDataGenerator

# Requires Pandas, Numpy, matplotlib etc.
import pandas as pd
import numpy as np
from PIL import Image
from sklearn.cross_validation import train_test_split
import copy
import matplotlib.pyplot as plt

import random
import os
import sys
from __builtin__ import exit

NUM_EPOCHS=20
BATCH_SIZE=256

def main(images_path, train_set, test_set):    
    if not test_set == '':
        print "Testing is not yet implemented in this version"
        exit(1)

    # Parse performance data and load images to array
    df = pd.read_csv(train_set)
    # Features (images)
    list_x = []
    # Runtimes
    list_y = []
    # Instance names
    list_instance_names = []
    # Solver names
    list_solver_names = []

    for n in range(1,len(df.columns)):
        list_solver_names.append(df.columns[n].strip())
    print(str(len(list_solver_names)) + " Solvers: ")
    print(list_solver_names)
    # Set index as filename 
    df2 = df.set_index('filename')
    # Loop over all instance names
    for name in df['filename']:
        # Solver name
        list_instance_names.append(name)
        # Feature image
        img = Image.open(os.path.join(images_path, name))
        list_x.append(np.array(img))
        # Runtimes
        list_y.append(df2.loc[name])

    print("\nNumber of total data points: " + str(len(list_x)))

    # Normalize feature image values to 0..1 range (assumes gray scale)
    data = np.array(list_x, dtype="float") / 255.0

    # Labels as runtimes
    labels = np.array(list_y)


    # Create simple train / test split
    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0, random_state=42)
    # Shape arrays
    x_train = x_train.reshape( x_train.shape[0], 128, 128, 1 )
    x_test  = x_test.reshape( x_test.shape[0], 128, 128, 1 )
    print("#Training Examples: " + str(x_train.shape[0]))
    print("#Testing Examples: " + str(x_test.shape[0]))

    # Keep copy of runtime values
    y_test_times = copy.deepcopy(y_test)

    # Setting cut-off value (timeout)
    cutoff_value = 10000
    print("Setting Cutoff-value to: " + str(cutoff_value))

    # Compute best single solver in terms of instances solved and average runtime for current fold
    list_solver_unsolved = []
    list_solver_average  = []
    for n in range(0, y_test_times.shape[1]):
        list_solver_unsolved.append(0)
        for k in range(0, y_test_times.shape[0]):
            if (y_test_times[k,n] >=cutoff_value):
                list_solver_unsolved[n] += 1
        list_solver_average.append(np.average(y_test_times[:,n]))
    print("\nSolver Average Runtimes: ")
    print(list_solver_average)
    print("\nSolver Unsolved Instances: ")
    print(list_solver_unsolved)

    best_solver_solved = np.argmin(list_solver_unsolved)
    print("\nBest Solver-ID in terms of instances solved: " + str(best_solver_solved) + " = " + list_solver_names[best_solver_solved])
    best_solver_average = np.argmin(list_solver_average)
    print("Best Solver-ID in terms of best average runtime: " + str(best_solver_average) + " = " + list_solver_names[best_solver_average])

    # Cast labels to 0/1 labels corresponding to unsolved / solved
    y_train[y_train < cutoff_value]  = 1
    y_train[y_train >= cutoff_value] = 0
    # For test apply the same
    y_test[y_test < cutoff_value]  = 1
    y_test[y_test >= cutoff_value] = 0

    # Set input shape for NN
    shape = x_train.shape[1:]
    # Create a simple CNN
    model = Sequential()
    model.add(Conv2D(128, kernel_size=(5, 5), strides=(1, 1),
                 activation='relu',
                 input_shape=shape))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
    #model.add(Conv2D(64, (5, 5), activation='relu'))
    #model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(0.2))
    #model.add(Dense(500, activation='relu'))
    model.add(Flatten())
    model.add(Dropout(0.1))
    model.add(Dense(y_train.shape[1], activation='sigmoid'))

    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='binary_crossentropy', optimizer=sgd)

    model.fit(x_train, y_train, epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, verbose=1, validation_split=0.15)

    # For each test data point compute predictions for each of the solvers
    preds = model.predict(x_test)
    print(preds)

    # serialize model to JSON
    model_json = model.to_json()
    with open("model.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights("model.h5")
    print("Saved model to disk")
 
if __name__ == "__main__":
    
    if len(sys.argv) == 3:
        print "Training only"
        test_set = ""
    elif len(sys.argv) == 4:
        test_set = sys.argv[3] 
    else:
        print "Invalid number of parameters, should be either 2 or 3."
        print "The first parameter is the path to images."
        print "The second parameter is the path to the training set."
        print "The third parameter (optional) is the path to the test set."
        exit(1)
    main(sys.argv[1], sys.argv[2], test_set) 
