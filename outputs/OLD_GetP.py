import ROOT as r
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import csv
import pandas as pd


FROM_CSV = 0
#print("Total events:{}".format(tree.GetEntries())) 
FILE = 'ship_sim.MuonBack-TGeant4_test.root'

if FROM_CSV:
    df = pd.read_csv('momentum.csv')
    P_t = df['Pt'].to_numpy()
    P = df['P'].to_numpy()
    z_start = df['z_start'].to_numpy()
    df = pd.read_csv('momentum_2.csv')
    P_t_2 = df['Pt_2'].to_numpy()
    P_2 = df['P_2'].to_numpy()
    z = df['z'].to_numpy()
    

else:
    file = r.TFile.Open(FILE,'r')
    tree = file.Get("cbmsim")
    P_t = []
    P = []
    P_x = []
    P_x_2 = []
    P_y_2 = []
    P_z_2 = []
    P_y = []
    P_z = []
    x_start = []
    y_start = []
    z_start = []
    x = []
    y = []
    z = []
    particle = []
    particle_2 = []
    for event in tree: 
        mc_pdgs = []
        for hit in event.MCTrack: 
            mc_pdgs.append(hit.GetPdgCode())
            if abs(hit.GetPdgCode()) == 13: 
                P_x.append(hit.GetPx())
                P_y.append(hit.GetPy())
                P_z.append(hit.GetPz())
                x_start.append(hit.GetStartX())
                y_start.append(hit.GetStartY())
                z_start.append(hit.GetStartZ())
                particle.append(hit.GetPdgCode())
        for hit in event.vetoPoint:
            if hit.GetTrackID() >= 0 and abs(mc_pdgs[hit.GetTrackID()]) == 13: 
                x.append(hit.GetX())
                y.append(hit.GetY())
                z.append(hit.GetZ())
                P_x_2.append(hit.GetPx())
                P_y_2.append(hit.GetPy())
                P_z_2.append(hit.GetPz())
                particle_2.append(mc_pdgs[hit.GetTrackID()])
    x = np.array(x)
    y = np.array(y)
    z = np.array(z)
    particle = np.array(particle)
    particle_2 = np.array(particle_2)
    x_start = np.array(x_start)
    y_start = np.array(y_start)
    z_start = np.array(z_start)
    P_x = np.array(P_x)
    P_y = np.array(P_y)
    P_z = np.array(P_z)
    P_x_2 = np.array(P_x_2)
    P_y_2 = np.array(P_y_2)
    P_z_2 = np.array(P_z_2)
    P_t = np.sqrt(P_x**2+P_y**2)
    P = np.sqrt(P_x**2+P_y**2+P_z**2)
    P_t_2 = np.sqrt(P_x_2**2+P_y_2**2)
    P_2 = np.sqrt(P_x_2**2+P_y_2**2+P_z_2**2)
    d = {'Px': P_x, 'Py':P_y, 'Pz':P_z,'x_start':x_start,'y_start':y_start,'z_start':z_start, 'particle':particle}
    d_2 = {'Px_2': P_x_2, 'Py_2':P_y_2, 'Pz_2':P_z_2,'x':x,'y':y,'z':z, 'particle_2':particle_2}
    with open('momentum.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(d.keys())
        for row in zip(*d.values()):
            writer.writerow(row)
    with open('momentum_2.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(d_2.keys())
        for row in zip(*d_2.values()):
            writer.writerow(row)

print('len',len(P_t))
print('Pt:',np.mean(P_t))
print('len2',len(P_t_2))
print('Pt2:',np.mean(P_t_2))
# Create a 2D histogram
plt.figure(figsize=(10, 7))
from matplotlib.colors import LogNorm
plt.hist2d(P, P_t, bins=50, cmap='viridis', norm=LogNorm())

# Add color bar
plt.colorbar(label='Counts')

# Add labels and title
plt.xlabel('$|P|$ [GeV]')
plt.ylabel('$P_t$ [GeV]')
plt.title('2D Histogram of Magnitude vs Transverse Momentum')

# Show plot
plt.savefig('momentum.png')
plt.close()


z_mask = z>0
print('z_mask_len', np.sum(z_mask))
plt.figure(figsize=(10, 7))
plt.hist2d(P_2[z_mask], P_t_2[z_mask], bins=50, cmap='viridis', norm=LogNorm())

# Add color bar
plt.colorbar(label='Counts')

# Add labels and title
plt.xlabel('$|P|$ [GeV]')
plt.ylabel('$P_t$ [GeV]')
plt.title('2D Histogram of Magnitude vs Transverse Momentum')

# Show plot
plt.show()
plt.savefig('momentum_2.png')
plt.close()
plt.scatter(z,P_t_2)
plt.savefig('z_P_2.png')
plt.close()
plt.hist(z,bins = 'auto')
plt.savefig('z_hist.png')
plt.close()
plt.scatter(z_start,P_t)
plt.savefig('zstart_P.png')
plt.close()



