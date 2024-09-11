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

class SHIPRunner(object):
    def __init__(self, tag,
                 input_file,
                 same_seed=False, 
                 output_dir = 'outputs',
                 step_geo=False,
                 shield_design = None, 
                 design = '2023',
                 MCTracksWithHitsOnly = True,  # copy particles which produced a hit and their history
                 shield_geofile = None, 
                 seed:int = 1,
                 sc_name = 'sc_v6'):

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
                                                #CaloDesign=globalDesigns[self.design]['caloDesign'], strawDesign=globalDesigns[self.design]['strawDesign'],
                                                muShieldStepGeo=self.step_geo, muShieldWithCobaltMagnet=0,
                                                SC_mag=True, scName=self.sc_name, decayVolumeMed="vacuums")

        run = ROOT.FairRunSim()
        run.SetName("TGeant4")  # Transport engine
        run.SetUserConfig('g4Config.C')
        rtdb = run.GetRuntimeDb()


        modules = shipDet_conf.configure(run, ship_geo)
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
        #exclusionList = ["Muon","Ecal","Hcal","TargetTrackers","NuTauTarget","HighPrecisionTrackers",
        #         "Veto","Magnet","TargetStation","MagneticSpectrometer","EmuMagnet"]
        for i in modules:#exclusionList:
            if i != 'MuonShield': modules.pop(i)

        run.SetGenerator(primGen)

        if display: run.SetStoreTraj(ROOT.kTRUE)
        else:run.SetStoreTraj(ROOT.kFALSE)
        run.Init()

        gMC = ROOT.TVirtualMC.GetMC()
        fStack = gMC.GetStack()
        if self.hits_only:
            fStack.SetMinPoints(1)
            fStack.SetEnergyCut(-100.*u.MeV)

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
        print('MODULE', modules)
        
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
    def run_fixed_target(self,n_events:int,storeOnlyMuons:bool = True, 
                    skipNeutrinos:bool = True,FourDP:bool = False, withEvtGen = True, boostDiMuon = 1., boostFactor = 1.,
                 phiRandom=False, 
                 fastMuon=True, 
                 first_event=0, 
                 display = False, 
                 plot_field = False,
                 remove_empty_events = True,
                 return_time = False):
        shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
        ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = globalDesigns[self.design]['dy'], tankDesign = globalDesigns[self.design]['dv'],
                                                muShieldDesign = self.shield_design, nuTauTargetDesign=globalDesigns[self.design]['nud'],
                                                muShieldGeo=self.shield_geo_file,
                                                muShieldStepGeo=self.step_geo, muShieldWithCobaltMagnet=0,
                                                SC_mag=True, scName=self.sc_name)
        outFile = 'test.root'
        Debug = False
        ecut = 0.5
        timer = ROOT.TStopwatch()
        timer.Start()
        run = ROOT.FairRunSim()
        run.SetName("TGeant4")  # Transport engine
        run.SetUserConfig('g4Config.C')
        run.SetOutputFile(outFile)  # Output file
        rtdb = run.GetRuntimeDb()
        run.SetMaterials("media.geo")
        # -----Create geometry----------------------------------------------
        cave= ROOT.ShipCave("CAVE")
        cave.SetGeometryFileName("caveWithAir.geo")
        run.AddModule(cave)
        '''TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
        slices_length   = ROOT.std.vector('float')()
        slices_material = ROOT.std.vector('std::string')()
        for i in range(1,ship_geo.targetOpt+1):
            slices_length.push_back(  eval("ship_geo.target.L"+str(i)))
            slices_material.push_back(eval("ship_geo.target.M"+str(i)))
        TargetStation.SetLayerPosMat(ship_geo.target.xy,slices_length,slices_material)

        run.AddModule(TargetStation)'''
        MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
                    ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
                    ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*4./10.,0.)
        MuonShield.SetSupports(False) # otherwise overlap with sensitive Plane
        run.AddModule(MuonShield) # needs to be added because of magn hadron shield.
        sensPlane = ROOT.exitHadronAbsorber()
        sensPlane.SetEnergyCut(ecut*u.GeV)
        if storeOnlyMuons: sensPlane.SetOnlyMuons()
        if skipNeutrinos: sensPlane.SkipNeutrinos()
        if FourDP: sensPlane.SetOpt4DP() # in case a ntuple should be filled with pi0,etas,omega
        # sensPlane.SetZposition(0.*u.cm) # if not using automatic positioning behind default magnetized hadron absorber
        run.AddModule(sensPlane)

        # -----Create PrimaryGenerator--------------------------------------
        primGen = ROOT.FairPrimaryGenerator()
        #P8gen = ROOT.FixedTargetGenerator()
        #P8gen.SetTarget("/TargetArea_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
        #P8gen.SetMom(400.*u.GeV)
        #P8gen.SetEnergyCut(ecut*u.GeV)
        #P8gen.SetDebug(Debug)
        #P8gen.SetHeartBeat(100000)
        #if G4only: P8gen.SetG4only()
        #if JpsiMainly: P8gen.SetJpsiMainly()
        #if tauOnly:    P8gen.SetTauOnly()
        #if withEvtGen: P8gen.WithEvtGen()
        #if boostDiMuon > 1:P8gen.SetBoost(boostDiMuon) # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
                                    # and later copied to Geant4
        #P8gen.SetSeed(args.seed)
        # for charm/beauty
        #        print ' for experts: p pot= number of protons on target per spill to normalize on'
        #        print '            : c chicc= ccbar over mbias cross section'
        #if charm or beauty:
        #    print("--- process heavy flavours ---")
        #    P8gen.InitForCharmOrBeauty(charmInputFile,nev,npot,nStart)
        fileType = ut.checkFileExists(self.input_file)

        if fileType == 'tree': primGen.SetTarget(ship_geo.target.z0+70.845*u.m,0.)
        else: primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)

        MuonBackgen = ROOT.MuonBackGenerator()
        MuonBackgen.Init(self.input_file, first_event, phiRandom)
        MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
        if self.same_seed: MuonBackgen.SetSameSeed(self.same_seed)

        primGen.AddGenerator(MuonBackgen)

        if not n_events: n_events = MuonBackgen.GetNevents()
        else: n_events = min(n_events, MuonBackgen.GetNevents())

        output_file = os.path.join(self.output_dir, f"ship_sim.MuonBack-TGeant4_{self.tag}.root")
        param_file = os.path.join(self.output_dir, f"params_ship.MuonBack-TGeant4_{self.tag}.root")
        geofile_output = os.path.join(self.output_dir,f"geometry_ship.MuonBack-TGeant4_{self.tag}.root")

        run.SetSink(ROOT.FairRootFileSink(output_file))
        #modules = shipDet_conf.configure(run, ship_geo)
        #modules['Veto'].SetFollowMuon()
        #if fastMuon:
        #    modules['Veto'].SetFastMuon()

        run.SetGenerator(primGen)
        #primGen.AddGenerator(P8gen)
        # -----Initialize simulation run------------------------------------
        run.Init()

        gMC = ROOT.TVirtualMC.GetMC()
        fStack = gMC.GetStack()
        fStack.SetMinPoints(1)
        fStack.SetEnergyCut(-1.)
        #
        #import AddDiMuonDecayChannelsToG4
        #AddDiMuonDecayChannelsToG4.Initialize(P8gen.GetPythia())

        # boost gamma2muon conversion
        if boostFactor > 1:
            ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
            ROOT.gROOT.ProcessLine('#include "Geant4/G4AnnihiToMuPair.hh"')
            ROOT.gROOT.ProcessLine('#include "Geant4/G4GammaConversionToMuons.hh"')
            gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
            procAnnihil = gProcessTable.FindProcess(ROOT.G4String('AnnihiToMuPair'),ROOT.G4String('e+'))
            procGMuPair = gProcessTable.FindProcess(ROOT.G4String('GammaToMuPair'),ROOT.G4String('gamma'))
            procGMuPair.SetCrossSecFactor(boostFactor)
            procAnnihil.SetCrossSecFactor(boostFactor)

        # -----Start run----------------------------------------------------
        run.Run(n_events)


        timer.Stop()
        rtime = timer.RealTime()
        ctime = timer.CpuTime()
        print(' ')
        print("Macro finished succesfully.")
        print("Output file is ",  outFile)
        print("Real time ",rtime, " s, CPU time ",ctime,"s")
        # ---post processing--- remove empty events --- save histograms
        tmpFile = outFile+"tmp"
        if ROOT.gROOT.GetListOfFiles().GetEntries()>0:
            fin   = ROOT.gROOT.GetListOfFiles()[0]
        else:
            fin = ROOT.TFile.Open(outFile)
        fHeader = fin.FileHeader
        fHeader.SetRunId(1)
        if False: pass#charm or beauty:
        # normalization for charm
        #poteq = P8gen.GetPotForCharm()
        #info = "POT equivalent = %7.3G"%(poteq)
        else: info = "POT = "+str(n_events)

        conditions = " with ecut="+str(ecut)
        #if JpsiMainly: conditions+=" J"
        #if tauOnly:    conditions+=" T"
        if withEvtGen: conditions+=" V"
        if boostDiMuon > 1: conditions+=" diMu"+str(boostDiMuon)
        if boostFactor > 1: conditions+=" X"+str(boostFactor)

        info += conditions
        fHeader.SetTitle(info)
        print("Data generated ", fHeader.GetTitle())

        nt = fin.Get('4DP')
        if nt:
            tf = ROOT.TFile('FourDP.root','recreate')
            tnt = nt.CloneTree(0)
            for i in range(nt.GetEntries()):
                rc = nt.GetEvent(i)
                rc = tnt.Fill(nt.id,nt.px,nt.py,nt.pz,nt.x,nt.y,nt.z)
            tnt.Write()
            tf.Close()

        t     = fin.cbmsim
        fout  = ROOT.TFile(tmpFile,'recreate' )
        sTree = t.CloneTree(0)
        nEvents = 0
        for n in range(t.GetEntries()):
            rc = t.GetEvent(n)
            if t.vetoPoint.GetEntries()>0:
                rc = sTree.Fill()
                nEvents+=1
            #t.Clear()
        fout.cd()
        for k in fin.GetListOfKeys():
            x = fin.Get(k.GetName())
            className = x.Class().GetName()
            if className.find('TTree')<0 and className.find('TNtuple')<0:
                xcopy = x.Clone()
                rc = xcopy.Write()
        sTree.AutoSave()
        ff   = fin.FileHeader.Clone(fout.GetName())
        fout.cd()
        ff.Write("FileHeader", ROOT.TObject.kSingleKey)
        sTree.Write()
        fout.Close()

        rc1 = os.system("rm  "+outFile)
        rc2 = os.system("mv "+tmpFile+" "+outFile)
        print("removed out file, moved tmpFile to out file",rc1,rc2)
        fin.SetWritable(False) # bpyass flush error

        print("Number of events produced with activity after hadron absorber:",nEvents)

        '''if checkOverlap:
            sGeo = ROOT.gGeoManager
            sGeo.CheckOverlaps()
            sGeo.PrintOverlaps()
            run.CreateGeometryFile("%s/geofile_full.root" % (self.output_dir))
            import saveBasicParameters
            saveBasicParameters.execute("%s/geofile_full.root" % (self.output_dir),ship_geo)'''


        
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--file", type=str, default='./samples/subsample.root')
    parser.add_argument("--shield_design", type=int, default=None)
    parser.add_argument("--tag", type=str, default='test')
    parser.add_argument("--i", type=int, default=0)
    parser.add_argument("--sameSeed", action='store_true')
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--keep_empty",dest='remove_empty', action='store_false')
    args = parser.parse_args()
    ship = SHIPRunner(args.tag,input_file = args.file,shield_design=args.shield_design,seed = args.seed, same_seed = args.sameSeed)
    _,d_time = ship.run_ship(args.n,first_event = args.i,return_time=True,plot_field=False, remove_empty_events=args.remove_empty)
    
