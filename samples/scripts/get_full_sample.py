import uproot
import pandas as pd

file_name = '/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_10.0_withCharmandBeauty0_mu.root'

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
print(data)





