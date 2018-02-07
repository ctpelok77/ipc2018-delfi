#! /usr/bin/env python
# -*- coding: utf-8 -*-


import sys
stdout = sys.stdout
sys.stdout = open('/dev/null', 'w')
stderr = sys.stderr
sys.stderr = open('/dev/null', 'w')
from keras.models import model_from_json
sys.stdout = stdout
sys.stderr = stderr

import numpy as np
from PIL import Image
import sys, os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# load json and create model
json_file = open(os.path.join(sys.path[0],'model.json'), 'r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)
# load weights into new model
model.load_weights(os.path.join(sys.path[0],"model.h5"))
#print("Loaded model from disk")

list_solver_names = ['31d1eefdbeca-h2-simpless-dks-lmcountlmmergedlmrhwlmhm1', '31d1eefdbeca-h2-simpless-dks-masb50ksccdfp', '31d1eefdbeca-h2-simpless-dks-lmcountlmrhw', '31d1eefdbeca-h2-simpless-dks-blind', '31d1eefdbeca-h2-simpless-dks-celmcut', '31d1eefdbeca-h2-simpless-dks-zopdbsgenetic', '31d1eefdbeca-h2-simpless-dks-masb50ksbmiasm', '31d1eefdbeca-h2-simpless-dks-masginfsccdfp', '31d1eefdbeca-simpless-dks-masb50kmiasmdfp', '31d1eefdbeca-h2-simpless-dks-cpdbshc900', '31d1eefdbeca-h2-simpless-oss-blind', '31d1eefdbeca-h2-simpless-oss-celmcut', '31d1eefdbeca-h2-simpless-oss-lmcountlmrhw', '31d1eefdbeca-h2-simpless-oss-masb50ksccdfp', '31d1eefdbeca-h2-simpless-oss-lmcountlmmergedlmrhwlmhm1', '31d1eefdbeca-h2-simpless-oss-zopdbsgenetic', '31d1eefdbeca-h2-simpless-oss-cpdbshc900', '31d1eefdbeca-simpless-oss-masb50kmiasmdfp', '31d1eefdbeca-h2-simpless-oss-masb50ksbmiasm', '31d1eefdbeca-h2-simpless-oss-masginfsccdfp', 'seq-opt-symba-1']

#print(str(len(list_solver_names)) + " Solvers: ")
#print(list_solver_names)

list_x = []

img = Image.open(sys.argv[1])
list_x.append(np.array(img))

#print("\nNumber of total data points: " + str(len(list_x)))
# Normalize feature image values to 0..1 range (assumes gray scale)
data = np.array(list_x, dtype="float") / 255.0
data  = data.reshape( data.shape[0], 128, 128, 1 )

# For each test data point compute predictions for each of the solvers
preds = model.predict(data)
#print(preds)
print(list_solver_names[np.argmax(preds[0])])
