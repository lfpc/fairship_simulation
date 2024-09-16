import argparse
import uproot
#import pandas as pd
import gzip
import pickle
from os import getenv

PROJECTS_DIR = getenv("PROJECTS_DIR")
parser = argparse.ArgumentParser()
parser.add_argument("--f", type=str, default = f"{PROJECTS_DIR}/fairship_simulation/samples/subsample.root")
parser.add_argument("--o", type=str, default = f"{PROJECTS_DIR}/fairship_simulation/samples/subsample.pkl")
args = parser.parse_args()
file_name = '../subsample.root'

def main(file,pkl_file_path):
    file = uproot.open(file_name)
    keys = file.keys()
    ntuple_name = keys[0]
    ntuple = file[ntuple_name]
    df = ntuple.arrays(library="pd")
    charge = df['id']/13.
    df.drop(['opx','opy','opz','ox','oy','oz','id','pythiaid','parentid','w','ecut'],axis=1,inplace = True)
    df['charge'] = charge
    np_matrix = df.to_numpy()
    with gzip.open(pkl_file_path, "wb") as f:
        pickle.dump(np_matrix, f)
    return df

if __name__ == '__main__':
    df = main(args.f, args.o)
    print(df.head())
