
import math
import ROOT
from pandas import DataFrame

def process_file(filename, tracker_ends=None, epsilon=1e-9, debug=False,
                 apply_acceptance_cut=False):
    file = ROOT.TFile(filename)

    tree = file.Get("cbmsim")
    print("Total events:{}".format(tree.GetEntries()))

    muons = []
    for index, event in enumerate(tree):
        for index, hit in enumerate(event.MCTrack):
            muons.append([
                hit.GetPx(),
                hit.GetPy(),
                hit.GetPz(),
                hit.GetStartX(),
                hit.GetStartY(),
                hit.GetStartZ()
            ])
    return DataFrame(muons,columns = ['Px','Py','Pz','x','y','z'])


if __name__ == '__main__':
    filename = './ship_sim.MuonBack-TGeant4_test.root'
    muons = process_file(filename,(-math.inf,math.inf))
    print(muons)
