import uproot
import pandas as pd
import gzip
import pickle
import os

def main(file_name):
    # Define the keys you want to extract
    mc_track_keys = ['PdgCode', 'Px', 'Py', 'Pz', 'StartX', 'StartY', 'StartZ', 'W']
    columns = [f'MCTrack.f{key}' for key in mc_track_keys]

    data = []
    with uproot.open(file_name) as file:
        tree = file["cbmsim"]
        print('NUM ENTRIES', tree.num_entries)

        # Iterate in chunks
        for chunk in tree.iterate(columns, library="pd", step_size=1000):
            data.append(chunk[(chunk['MCTrack.fPdgCode'] == -13) | (chunk['MCTrack.fPdgCode'] == 13)])
    data = pd.concat(data)
    print(data.head())
    return data.to_numpy()

if __name__ == '__main__':
    input_dir = '/eos/experiment/ship/data/Mbias/background-prod-2018'
    output_dir = '/eos/experiment/ship/user/lcattela/SHIP/'
    file_name = 'pythia8_Geant4_10.0_withCharmandBeauty0_mu.root'
    output_name = 'full_sample.pkl'
    data = main(os.path.join(input_dir,file_name))
    print('DATA SHAPE:', data.shape)
    with gzip.open(os.path.join(output_dir,output_name), "wb") as f:
        pickle.dump(data, f)





