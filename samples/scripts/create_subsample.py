import uproot
import numpy as np
import argparse
import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--N", type=int,default = 50000)
parser.add_argument("--f", type=str, default = "~/projects/fairship_simulation/samples/full_sample.root")
parser.add_argument("--o", type=str, default = "~/projects/fairship_simulation/samples/subsample.root")
parser.add_argument("--x", type=float,default = None)
parser.add_argument("--y", type=float,default = None)
parser.add_argument("--z", type=float,default = None)
args = parser.parse_args()

def main(input, N:int, output):
    root_file = uproot.open(input)
    ntuple = root_file["pythia8-Geant4"]
    ntuple_df = ntuple.arrays(library="pd")
    #with gzip.open('../oliver_data_enriched.pkl', 'rb') as f:
    #    px,py,pz = pickle.load(f)[:N].T
    ntuple_sample = ntuple_df.sample(n=N, random_state=42).reset_index(drop=True)
    #ntuple_sample['px'] = px
    #ntuple_sample['py'] = py
    #ntuple_sample['pz'] = pz
    #ntuple_sample['opx'] = px
    #ntuple_sample['opy'] = py
    #ntuple_sample['opz'] = pz
    new_root_file = ROOT.TFile(output, "RECREATE")
    new_ntuple = ROOT.TTree("pythia8-Geant4", "Updated Ntuple")
    branches = {}
    for column in ntuple_sample.columns:
        branches[column] = np.zeros(1, dtype=ntuple_sample[column].dtype)
        new_ntuple.Branch(column, branches[column], f"{column}/{branches[column].dtype.char.upper()}")
    for i in range(len(ntuple_sample)):
        for column in ntuple_sample.columns:
            if column in ['z','oz'] and args.z is not None:
                value = args.z #-48.5
            elif column in ['x','ox',] and args.x is not None:
                value = args.x
            elif column in ['y','oy'] and args.y is not None:
                value = args.y
            else: value = ntuple_sample[column].iloc[i]
            branches[column][0] = value
        new_ntuple.Fill()
    new_ntuple.Write()
    new_root_file.Close()
    return ntuple_sample

if __name__ == '__main__':
    df = main(args.f,args.N,args.o)
    print(df.head())