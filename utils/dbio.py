import os
import numpy as np
from ase.db import connect
from ase.io import read, write


def get_keyVal(dbRows, keyVal):
    '''
    Returns 1-D list
    '''
    tmp = []
    for r in dbRows:
        tmp.append(r[keyVal])
    return tmp


def get_traj(dbRows):
    tmp = []
    for r in dbRows:
        a = r.toatoms()
        a.info = r.key_value_pairs
        tmp.append(a)
    return tmp


def get_projName():
    return os.getcwd().split('/')[-1]


def calypso2db():
    print(' --- Collecting CALYPSO results --- ')
    os.system('cd results;cak.py -n 9999 --vasp')
#    eneData = [eval(r.split()[-1]) for r in open('results/Analysis_Output.dat').readlines()[1:]]
    eneData = [r.split()[-1]
               for r in open('results/Analysis_Output.dat').readlines()[1:]]
    eneData = [0 if r == 'NULL' else eval(r) for r in eneData]
    with connect('calypso-%s.db' % get_projName(), append=False) as myDb:
        for i in range(len(eneData)):
            s = read('results/dir_origin/OCell_%i.vasp' % (i+1))
            s.wrap()
            myDb.write(
                s,
                eV=eneData[i],
                done=1,
            )
    print(' %i candidates writen to calypso-%s.db' %
          (len(eneData), get_projName()))


def vasp2db(nameKey='', excludeBAD=False):
    print(' --- Collecting VASP results ---')
    vdirs = [d.split('/')[0]
             for d in os.popen('ls *%s*/OSZICAR' % nameKey).readlines()]
    count_fin = 0
    with connect('vasp-%s.db' % get_projName(), append=False) as myDb:
        for d in vdirs:
            print('%s' % d, end='')
            if excludeBAD:
                if 'BADSTRUCTURE' in os.listdir(d):
                    print('-X', end='\t')
                    continue
            if 'E0' not in open(d+'/OSZICAR', 'r').readlines()[-1]:
                print('-X', end='\t')
                continue
            s = read(d+'/OUTCAR', index='-1')
            myDb.write(
                s,
                eV=s.get_potential_energy(),
                mag=s.get_magnetic_moment(),
                done=1,
            )
            print('-O', end='\t')
            count_fin += 1
    print('\n %i candidates writen to vasp-%s.db' %
          (count_fin, get_projName()))


def vasp2db_SC(nameKey='', u_she=0):
    print(' --- Collecting VASP results ---')
    vdirs = [d.split('/')[0]
             for d in os.popen('ls *%s*/OUTCAR' % nameKey).readlines()]
    count_fin = 0
    with connect('vaspSC-%s.db' % get_projName(), append=False) as myDb:
        for d in vdirs:
            print('%s' % d, end='')
            if 'parabola.dat' not in os.listdir(d):
                print('-X', end='\t')
                continue
            s = read(d+'/OUTCAR', index='-1')
            a, b, c = np.loadtxt(f'{d}/parabola.dat')
            try:
                mag = s.get_magnetic_moment()
            except:
                mag = 0
            myDb.write(
                s,
                a=a,
                b=b,
                c=c,
                sc_U=u_she,
                sc_eV=a*u_she**2+b*u_she+c,
                eV=s.get_potential_energy(),
                mag=mag,
                done=1,
            )
            print('-O', end='\t')
            count_fin += 1
    print('\n %i candidates writen to vasp-%s.db' %
          (count_fin, get_projName()))


def lmp2db(nameKey='', excludeBAD=False):
    import gocia.utils.lammps as lmp
    print(' --- Collecting LAMMPS results ---')
    vdirs = [d.split('/')[0]
             for d in os.popen('ls *%s*/lmp.out' % nameKey).readlines()]
    count_fin = 0
    with connect('lmp-%s.db' % get_projName(), append=False) as myDb:
        for d in vdirs:
            if excludeBAD:
                if 'BADSTRUCTURE' in os.listdir(d):
                    continue
            if 'Final' not in open(d+'/lmp.out').read():
                continue
            print('%s' % d, end='\t')
            info = ''
            mag = 0
            ene_eV = lmp.get_ene(d+'/lmp.out')
            s = lmp.get_last_frame(d+'/traj.xyz', d+'/inp.vasp')
            s.wrap()
            myDb.write(
                s,
                eV=ene_eV,
                mag=mag,
                done=1,
            )
            count_fin += 1
    print('\n %i candidates writen to lmp-%s.db' % (count_fin, get_projName()))


def db2vasp(dbName):
    traj = read(dbName, index=':')
    for i in range(len(traj)):
        curName = 's%s.vasp' % (str(i).zfill(6))
        write(curName, traj[i], vasp5=True)
        print(' > %s written!' % curName)
