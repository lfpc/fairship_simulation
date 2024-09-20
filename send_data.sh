cd outputs
python scripts/GetOutputs.py
python scripts/GetInputs.py
#scp outputs_fairship.pkl lprate@linux.physik.uzh.ch://home/hep/lprate/projects/MuonsAndMatter/data/outputs
scp '/afs/cern.ch/user/l/lcattela/SHIP/fairship_simulation/outputs/inputs_fairship.pkl' lprate@linux.physik.uzh.ch://home/hep/lprate/projects/MuonsAndMatter/data
cd ..
