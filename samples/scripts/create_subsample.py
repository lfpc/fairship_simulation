import uproot
import pandas as pd
import numpy as np

# Load the pkl file with gzip
import gzip
import pickle

# ROOT output file creation
import ROOT
N = 50000
root_file = uproot.open("../full_sample.root")
ntuple = root_file["pythia8-Geant4"]
ntuple_df = ntuple.arrays(library="pd")
#with gzip.open('../oliver_data_enriched.pkl', 'rb') as f:
#    px,py,pz = pickle.load(f)[:N].T
ntuple_sample = ntuple_df.sample(n=N, random_state=42).reset_index(drop=True)
print(ntuple_sample.head())
#ntuple_sample['px'] = px
#ntuple_sample['py'] = py
#ntuple_sample['pz'] = pz
#ntuple_sample['opx'] = px
#ntuple_sample['opy'] = py
#ntuple_sample['opz'] = pz
print(ntuple_sample.head())
new_root_file = ROOT.TFile("../subsample.root", "RECREATE")
new_ntuple = ROOT.TTree("pythia8-Geant4", "Updated Ntuple")
branches = {}
for column in ntuple_sample.columns:
    branches[column] = np.zeros(1, dtype=ntuple_sample[column].dtype)
    new_ntuple.Branch(column, branches[column], f"{column}/{branches[column].dtype.char.upper()}")
for i in range(len(ntuple_sample)):
    for column in ntuple_sample.columns:
        if column in ['z','oz']:
                value = -48.5
        elif column in ['x','y','ox','oy']:
                value = 0.0
        else: value = ntuple_sample[column].iloc[i]
        branches[column][0] = value
    new_ntuple.Fill()
new_ntuple.Write()
new_root_file.Close()
