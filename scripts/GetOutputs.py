import numpy as np
from collections import defaultdict
import ROOT
import gzip
import pickle
import shipunit as u

def process_file(filename, tracker_ends=None, epsilon=1e-9, debug=False,
                 apply_acceptance_cut=False):
    file = ROOT.TFile(filename)

    tree = file.Get("cbmsim")
    print("Total events:{}".format(tree.GetEntries()))

    MUON = 13
    muons_stats = []
    events_with_more_than_two_hits_per_mc = 0
    empty_hits = "Not implemented"

    for index, event in enumerate(tree):
        if index % 5000 == 0:
            print("N events processed: {}".format(index))
        mc_pdgs = []
        for hit in event.MCTrack:
            mc_pdgs.append(hit.GetPdgCode())
       
        muon_veto_points = defaultdict(list)
        for hit in event.vetoPoint:
            if hit.GetTrackID() >= 0 and\
                abs(mc_pdgs[hit.GetTrackID()]) == MUON and\
                tracker_ends[0] - epsilon <= hit.GetZ() <= tracker_ends[1] + epsilon:
                pos_begin = ROOT.TVector3()
                hit.Position(pos_begin)
                muon_veto_points[hit.GetTrackID()].append([pos_begin.X(), pos_begin.Y(),pos_begin.Z(),hit.GetPx(),hit.GetPy(),hit.GetPz()])
        for index, hit in enumerate(event.MCTrack):
            if index in muon_veto_points:
                if debug:
                    print("PDG: {}, mID: {}".format(hit.GetPdgCode(), hit.GetMotherId()))
                    assert abs(hit.GetPdgCode()) == MUON
                muon = [
                    hit.GetPx(),
                    hit.GetPy(),
                    hit.GetPz(),
                    hit.GetStartX(),
                    hit.GetStartY(),
                    hit.GetStartZ(),
                    hit.GetPdgCode()
                ]
                muons_stats.append(muon + muon_veto_points[index][0])
                if len(muon_veto_points[index]) > 1:
                    events_with_more_than_two_hits_per_mc += 1
                    continue
   
    print("events_with_more_than_two_hits_per_mc: {}".format(events_with_more_than_two_hits_per_mc))
    print("Stopped muons: {}".format(empty_hits))
    print("Total events returned: {}".format(len(muons_stats)))
    return np.array(muons_stats)



import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracker", nargs=2,default = (-3170.0000,-3168.0000))
    args = parser.parse_args()
    tag = 'test'
    filename = f'/afs/cern.ch/user/l/lcattela/SHIP/fairship_simulation/outputs/ship_sim_{tag}.root'
    tracker = (float(args.tracker[0]),float(args.tracker[1]))
    muons = process_file(filename,tracker)
    with gzip.open(f'/afs/cern.ch/user/l/lcattela/SHIP/fairship_simulation/outputs/outputs_fairship.pkl', "wb") as f:
        pickle.dump(muons, f)
