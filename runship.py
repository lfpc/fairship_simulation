import ROOT
ROOT.gSystem.Load('libEGPythia8')
from ShipGeoConfig import ConfigRegistry
import shipunit as u
import shipRoot_conf
import rootUtils as ut
import os
import shipDet_conf
import geomGeant4
import saveBasicParameters
import checkMagFields
import argparse
from time import time



globalDesigns = {
     '2016' : {
          'dy' : 10.,
          'dv' : 5,
          'ds' : 7,
          'nud' : 1,
          'caloDesign' : 0,
          'strawDesign' : 4
     }, '2018' : {
          'dy' : 10.,
          'dv' : 6,
          'ds' : 9,
          'nud' : 3,
          'caloDesign' : 3,
          'strawDesign' : 10
     }, '2022' : {
          'dy' : 8.,
          'dv' : 6,
          'ds' : 9,
          'nud' : 3,
          'caloDesign' : 3,
          'strawDesign' : 10
     }, '2023' : {
          'dy' : 6.,
          'dv' : 6,
          'ds' : 8,
          'nud' : 4,
          'caloDesign' : 3,
          'strawDesign' : 10
     }
}

N_CLUSTERS = 1024

class SHIPRunner(object):
    def __init__(self, tag,
                 input_file,
                 same_seed=False, 
                 output_dir = 'outputs',
                 step_geo=False,
                 shield_design = None, 
                 design = '2023',
                 MCTracksWithHitsOnly = True,  # copy particles which produced a hit and their history
                 shield_geofile = 'magnet_geo.root', 
                 seed:int = 1,
                 sc_name = 'sc_v6',
                 only_muonshield:bool = True,
                 veto = True,
                 SC_mag = True,
                 smearbeam = False):

        if shield_design is None: shield_design = globalDesigns[design]['ds']
        self.shield_design = shield_design

        self.design = design
        self.same_seed = same_seed
        self.theSeed = seed

        self.shield_geo_file = shield_geofile

        self.output_dir = output_dir
        if not os.path.exists(self.output_dir): os.makedirs(self.output_dir)

        self.input_file = input_file
        self.step_geo = step_geo

        self.hits_only = MCTracksWithHitsOnly
        self.tag = tag
        self.sc_name = sc_name

        self.only_muonshield = only_muonshield
        self.veto =veto
        self.SC_mag = SC_mag
        self.smearbeam = smearbeam


    def run_ship(self, n_events=0, 
                 phiRandom=False, 
                 fastMuon=True, 
                 first_event=0, 
                 display = False, 
                 plot_field = False,
                 remove_empty_events = True,
                 return_time = False):
        """
        phiRandom = False  # only relevant for muon background generator
        followMuon = True  # only transport muons for a fast muon only background
        """
        #r.gErrorIgnoreLevel = r.kWarning

        ROOT.gRandom.SetSeed(self.theSeed)
        shipRoot_conf.configure(0)
        ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = globalDesigns[self.design]['dy'], tankDesign = globalDesigns[self.design]['dv'],
                                                muShieldDesign = self.shield_design, nuTauTargetDesign=globalDesigns[self.design]['nud'], 
                                                muShieldGeo=self.shield_geo_file,
                                                CaloDesign=globalDesigns[self.design]['caloDesign'], strawDesign=globalDesigns[self.design]['strawDesign'],
                                                muShieldStepGeo=self.step_geo, muShieldWithCobaltMagnet=0,
                                                SC_mag=self.SC_mag, scName=self.sc_name, decayVolumeMedium="vacuums")

        run = ROOT.FairRunSim()
        run.SetName("TGeant4")  # Transport engine
        run.SetUserConfig('g4Config.C')
        run.SetMaterials("media.geo")
        #rtdb = run.GetRuntimeDb()
        #exclusion_list = shipDet_conf.LIST_WITHOUT_MUONSHIELD if self.only_muonshield else []
        #if not self.veto: exclusion_list.append('Veto')
        modules = shipDet_conf.configure(run, ship_geo)#, exclusionList = exclusion_list)
        primGen = ROOT.FairPrimaryGenerator()
        fileType = ut.checkFileExists(self.input_file)
        if fileType == 'tree': primGen.SetTarget(ship_geo.target.z0+70.845*u.m,0.)
        else: primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)

        MuonBackgen = ROOT.MuonBackGenerator()
        MuonBackgen.Init(self.input_file, first_event, phiRandom)
        if self.smearbeam:
            MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
        if self.same_seed: MuonBackgen.SetSameSeed(self.same_seed)

        primGen.AddGenerator(MuonBackgen)
        if args.id is None:
            if not n_events: n_events = MuonBackgen.GetNevents()-1
            else: n_events = min(n_events, MuonBackgen.GetNevents()-1)
        else: 
            n_events = MuonBackgen.GetNevents()/N_CLUSTERS
            first_event = args.id*n_events


        output_file = os.path.join(self.output_dir, f"ship_sim_{self.tag}.root")
        param_file = os.path.join(self.output_dir, f"params_ship_{self.tag}.root")
        geofile_output = os.path.join(self.output_dir,f"geometry_ship_{self.tag}.root")

        run.SetSink(ROOT.FairRootFileSink(output_file))

        if self.veto:
            modules['Veto'].SetFollowMuon()
            if fastMuon:
                modules['Veto'].SetFastMuon()

        run.SetGenerator(primGen)

        if display: run.SetStoreTraj(ROOT.kTRUE)
        else:run.SetStoreTraj(ROOT.kFALSE)
        run.Init()


        if self.hits_only:
            gMC = ROOT.TVirtualMC.GetMC()
            fStack = gMC.GetStack()
            fStack.SetMinPoints(1)
            fStack.SetEnergyCut(-100.*u.MeV)

        if display:
            self.display(ship_geo)
            
        if hasattr(ship_geo.Bfield, "fieldMap") and plot_field:
            fieldMaker = geomGeant4.addVMCFields(ship_geo, '', True) 
            fieldMaker.plotField(1, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-300.0, 300.0, 6.0), os.path.join(self.output_dir, 'Bzx.png'))
            fieldMaker.plotField(2, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-400.0, 400.0, 6.0), os.path.join(self.output_dir, 'Bzy.png'))

        print ('Start run of {} events.'.format(n_events))
        t1 = time()
        run.Run(n_events)
        t2 = time()
        dt = t2-t1
        print ('Finished simulation of {} events. Time = {}'.format(n_events, dt))
        print('target z0:',ship_geo.target.z0)
        
        kParameterMerged = ROOT.kTRUE
        
        #parOut = ROOT.FairParRootFileIo(kParameterMerged)
        #parOut.open(param_file)
        #rtdb.setOutput(parOut)
        #rtdb.saveOutput()
        #rtdb.printParamContexts()
        #getattr(rtdb,"print")()
        run.CreateGeometryFile(geofile_output)
        saveBasicParameters.execute(geofile_output,ship_geo)
        print("Output file is ",  output_file)
        print("Parameter file is ",param_file)

        if remove_empty_events: self.remove_empty(output_file)
        if return_time: return run,dt
        else: return run

    def run_muon_shield(self,n_events=0, 
                 phiRandom=False, 
                 fastMuon=True, 
                 first_event=0, 
                 display = False, 
                 plot_field = False,
                 remove_empty_events = True,
                 return_time = False):
        ROOT.gRandom.SetSeed(self.theSeed)
        shipRoot_conf.configure(0)
        ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = globalDesigns[self.design]['dy'], tankDesign = globalDesigns[self.design]['dv'],
                                                muShieldDesign = self.shield_design, nuTauTargetDesign=globalDesigns[self.design]['nud'], 
                                                muShieldGeo=self.shield_geo_file,
                                                CaloDesign=globalDesigns[self.design]['caloDesign'], strawDesign=globalDesigns[self.design]['strawDesign'],
                                                muShieldStepGeo=self.step_geo, muShieldWithCobaltMagnet=0,
                                                SC_mag=True, scName=self.sc_name, decayVolumeMedium="vacuums")

        run = ROOT.FairRunSim()
        run.SetName("TGeant4")  # Transport engine
        run.SetUserConfig('g4Config.C')
        #run.SetMaterials("media.geo")
        rtdb = run.GetRuntimeDb()
        exclusion_list = shipDet_conf.LIST_WITHOUT_MUONSHIELD if self.only_muonshield else []
        #exclusion_list.append('Veto')
        modules = shipDet_conf.configure(run, ship_geo, exclusionList = exclusion_list)
        primGen = ROOT.FairPrimaryGenerator()
        fileType = ut.checkFileExists(self.input_file)
        if fileType == 'tree': primGen.SetTarget(ship_geo.target.z0+70.845*u.m,0.)
        else: primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)

        MuonBackgen = ROOT.MuonBackGenerator()
        MuonBackgen.Init(self.input_file, first_event, phiRandom)
        #MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
        if self.same_seed: MuonBackgen.SetSameSeed(self.same_seed)

        primGen.AddGenerator(MuonBackgen)
        if not n_events: n_events = MuonBackgen.GetNevents()
        else: n_events = min(n_events, MuonBackgen.GetNevents())

        output_file = os.path.join(self.output_dir, f"ship_sim.MuonBack-TGeant4_{self.tag}.root")
        param_file = os.path.join(self.output_dir, f"params_ship.MuonBack-TGeant4_{self.tag}.root")
        geofile_output = os.path.join(self.output_dir,f"geometry_ship.MuonBack-TGeant4_{self.tag}.root")

        run.SetSink(ROOT.FairRootFileSink(output_file))

        modules['Veto'].SetFollowMuon()
        if fastMuon:
            modules['Veto'].SetFastMuon()

        run.SetGenerator(primGen)

        if display: run.SetStoreTraj(ROOT.kTRUE)
        else:run.SetStoreTraj(ROOT.kFALSE)
        run.Init()

        #gMC = ROOT.TVirtualMC.GetMC()
        #fStack = gMC.GetStack()
        #if self.hits_only:
        #    fStack.SetMinPoints(1)
        #    fStack.SetEnergyCut(-100.*u.MeV)

        if display:
            self.display(ship_geo)
            
        if hasattr(ship_geo.Bfield, "fieldMap"):
            fieldMaker = geomGeant4.addVMCFields(ship_geo, '', True)
        if plot_field:    
            fieldMaker.plotField(1, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-300.0, 300.0, 6.0), os.path.join(self.output_dir, 'Bzx.png'))
            fieldMaker.plotField(2, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-400.0, 400.0, 6.0), os.path.join(self.output_dir, 'Bzy.png'))

        print ('Start run of {} events.'.format(n_events))
        t1 = time()
        run.Run(n_events)
        t2 = time()
        dt = t2-t1
        print ('Finished simulation of {} events. Time = {}'.format(n_events, dt))
        
        kParameterMerged = ROOT.kTRUE
        parOut = ROOT.FairParRootFileIo(kParameterMerged)
        parOut.open(param_file)
        rtdb.setOutput(parOut)
        rtdb.saveOutput()
        rtdb.printParamContexts()
        getattr(rtdb,"print")()
        run.CreateGeometryFile(geofile_output)
        saveBasicParameters.execute(geofile_output,ship_geo)
        print("Output file is ",  output_file)
        print("Parameter file is ",param_file)

        if remove_empty_events: self.remove_empty(output_file)
        if return_time: return run,dt
        else: return run
        



        
    def display(self,ship_geo):
        trajFilter = ROOT.FairTrajFilter.Instance()
        trajFilter.SetStepSizeCut(1*u.mm)
        trajFilter.SetVertexCut(-20*u.m, -20*u.m,ship_geo.target.z0-1*u.m, 20*u.m, 20*u.m, 200.*u.m)
        trajFilter.SetMomentumCutP(0.1*u.GeV)
        trajFilter.SetEnergyCut(0., 400.*u.GeV)
        trajFilter.SetStorePrimaries(ROOT.kTRUE)
        trajFilter.SetStoreSecondaries(ROOT.kTRUE)
    @staticmethod
    def remove_empty(output_file):
        tmpFile = output_file+"tmp"
        xxx = output_file.split('/')
        check = xxx[-1]
        fin = False
        for ff in ROOT.gROOT.GetListOfFiles():
            nm = ff.GetName().split('/')
            if nm[len(nm)-1] == check: fin = ff
        if not fin: fin   = ROOT.TFile.Open(output_file)
        t     = fin.cbmsim
        fout  = ROOT.TFile(tmpFile,'recreate')
        fSink = ROOT.FairRootFileSink(fout)

        sTree = t.CloneTree(0)
        nEvents = 0
        pointContainers = []
        for x in sTree.GetListOfBranches():
            name = x.GetName()
            if not name.find('Point')<0: pointContainers.append('sTree.'+name+'.GetEntries()') 
            # makes use of convention that all sensitive detectors fill XXXPoint containers
        for n in range(t.GetEntries()):
            rc = t.GetEvent(n)
            empty = True
            for x in pointContainers:
                if eval(x)>0: empty = False
            if not empty:
                rc = sTree.Fill()
                nEvents+=1

        branches = ROOT.TList()
        branches.SetName('BranchList')
        branches.Add(ROOT.TObjString('MCTrack'))
        branches.Add(ROOT.TObjString('vetoPoint'))
        branches.Add(ROOT.TObjString('ShipRpcPoint'))
        branches.Add(ROOT.TObjString('TargetPoint'))
        branches.Add(ROOT.TObjString('TTPoint'))
        branches.Add(ROOT.TObjString('ScoringPoint'))
        branches.Add(ROOT.TObjString('strawtubesPoint'))
        branches.Add(ROOT.TObjString('EcalPoint'))
        branches.Add(ROOT.TObjString('sEcalPointLite'))
        branches.Add(ROOT.TObjString('smuonPoint'))
        branches.Add(ROOT.TObjString('TimeDetPoint'))
        branches.Add(ROOT.TObjString('MCEventHeader'))
        branches.Add(ROOT.TObjString('sGeoTracks'))

        sTree.AutoSave()
        fSink.WriteObject(branches, "BranchList", ROOT.TObject.kSingleKey)
        fSink.SetOutTree(sTree)

        fout.Close()
        print("removed empty events, left with:", nEvents)
        rc1 = os.system("rm  "+output_file)
        rc2 = os.system("mv "+tmpFile+" "+output_file)
        fin.SetWritable(False) # bpyass flush error
    @staticmethod
    def visualizeMagFields():
        checkMagFields.run()
    @staticmethod
    def checkOverlapsWithGeant4():
        mygMC = ROOT.TGeant4.GetMC()
        mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
        mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
        mygMC.ProcessGeantCommand("/geometry/test/run")

from array import array
def extract_l_and_w(magnet_geofile, full_geometry_file, run=None):
        run.CreateGeometryFile('outputs/geometry_out.root')
        sGeo = ROOT.gGeoManager
        muonShield = sGeo.GetVolume('MuonShieldArea')
        g = ROOT.TFile.Open(os.path.join(self.geometry_dir, magnet_geofile), 'read')
        params = g.Get("params")
        f = ROOT.TFile.Open(os.path.join(self.geometry_dir, full_geometry_file), 'update')
        f.cd()
        length = ROOT.TVectorD(1, array('d', [L]))
        length.Write('length')
        weight = ROOT.TVectorD(1, array('d', [W]))
        weight.Write('weight')
        params.Write("params")

        # Extract coordinates of senstive plane
        nav = ROOT.gGeoManager.GetCurrentNavigator()
        nav.cd("sentsitive_tracker_1")
        tmp = nav.GetCurrentNode().GetVolume().GetShape()
        o = [tmp.GetOrigin()[0], tmp.GetOrigin()[1], tmp.GetOrigin()[2]]
        local = array('d', o)
        globOrigin = array('d', [0, 0, 0])
        nav.LocalToMaster(local, globOrigin)

        sensitive_plane = sGeo.GetVolume('sentsitive_tracker')

        left_end, right_end = globOrigin[2] - sensitive_plane.GetShape().GetDZ(),\
                              globOrigin[2] + sensitive_plane.GetShape().GetDZ()
        return L, W, (left_end, right_end)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--n", type=int, default=0)
    parser.add_argument("--tag", type=str, default='test')
    parser.add_argument("--i", type=int, default=0)
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--file", type=str, default='./samples/subsample.root')
    parser.add_argument("--shield_design", type=int, default=None)
    parser.add_argument("--sameSeed", action='store_true')
    parser.add_argument("--full_geometry", dest = 'only_muonshield',action='store_false')
    parser.add_argument("--remove_veto", dest = 'veto',action='store_false')
    parser.add_argument("--hits_only",action='store_true')
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--keep_empty",dest='remove_empty', action='store_false')
    parser.add_argument("--warm",dest='SC_mag', action='store_false')
    parser.add_argument("--smear",action='store_true')
    args = parser.parse_args()

    ship = SHIPRunner(args.tag,SC_mag=args.SC_mag,input_file = args.file,shield_design=args.shield_design,
                      seed = args.seed, same_seed = args.sameSeed, only_muonshield= args.only_muonshield, veto = args.veto,
                      MCTracksWithHitsOnly=args.hits_only, smearbeam= args.smear)
    _,d_time = ship.run_ship(args.n,first_event = args.i,return_time=True,plot_field=False, remove_empty_events=args.remove_empty)
    
