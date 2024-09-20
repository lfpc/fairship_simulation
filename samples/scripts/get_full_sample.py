import uproot
import pandas as pd
import gzip
import pickle
import os

def main(file_name):
    # Define the keys you want to extract
    mc_track_keys = ['Px', 'Py', 'Pz', 'StartX', 'StartY', 'StartZ','PdgCode','W']
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
    output_name = 'full_sample_*.pkl'
    #file_name = 'pythia8_Geant4_10.0_withCharmandBeauty0_mu.root'

    start_str = 'pythia8_Geant4_10.0_withCharmandBeauty'
    end_str = '_mu.root'
    for file_name in os.listdir(input_dir):
        if not file_name.startswith(start_str) and file_name.endswith(end_str): continue
        num_file = file_name[len(start_str):-len(end_str)]
        print(f'Checking file {num_file}')
        data = main(os.path.join(input_dir,file_name))
        print('DATA SHAPE:', data.shape)
        with gzip.open(os.path.join(output_dir,output_name.replace('*',num_file)), "wb") as f:
            pickle.dump(data, f)





