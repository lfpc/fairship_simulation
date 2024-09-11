file_name = '../subsample.root'
import uproot
import pandas as pd
import gzip
import pickle
file = uproot.open(file_name)
keys = file.keys()
ntuple_name = keys[0]
ntuple = file[ntuple_name]
df = ntuple.arrays(library="pd")
charge = df['id']/13.
df.drop(['opx','opy','opz','ox','oy','oz','id','pythiaid','parentid','w','ecut'],axis=1,inplace = True)
df['charge'] = charge
np_matrix = df.to_numpy()
pkl_file_path = "../subsample.pkl"
with gzip.open(pkl_file_path, "wb") as f:
    pickle.dump(np_matrix, f)
print(df.head())
