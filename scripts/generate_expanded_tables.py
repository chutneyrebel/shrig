#!/usr/bin/env python3
"""Generate 96 historical plus 8 curated, band-limited multi-frame wavetables.
No third-party samples; run before compiling DSP.
"""
from pathlib import Path
import math
N=256
LIMITS=[96,64,48,32,24,16,8,4,1]
DEST=Path(__file__).resolve().parents[1]/'src'/'expanded_tables.h'
with DEST.open('w') as f:
    f.write('/* Generated original spectral families. Do not edit. */\n#ifndef SPRIG_EXPANDED_TABLES_H\n#define SPRIG_EXPANDED_TABLES_H\n')
    f.write('#define SPRIG_EXPANDED_WAVES 104\n#define SPRIG_EXPANDED_FRAMES 4\n')
    f.write('static const float sprig_expanded_tables[104][4][9][256]={\n')
    for wave in range(104):
        f.write('{\n')
        for frame in range(4):
            f.write('{\n')
            for lim in LIMITS:
                values=[]
                for j in range(N):
                    p=2*math.pi*j/N
                    v=0.
                    for h in range(1,lim+1):
                        # Twenty-four spectral character families, four timbre variants.
                        family=wave//4
                        variant=wave%4
                        tilt=.85+.33*variant+.22*frame
                        if family==0: weight=1/h**tilt
                        elif family==1: weight=(1 if h%2 else .01)/h**tilt
                        elif family==2: weight=(1 if h%3==1 else .01)/h**tilt
                        elif family==3: weight=(1 if h%4==1 else .01)/h**tilt
                        elif family==4: weight=(.2+ .8*abs(math.sin(h*(.55+.12*variant)+frame*.2)))/h**tilt
                        elif family==5: weight=(1 if abs(h-(3+variant*2+frame*2))<=1 else .005)/h**(.35+.1*frame)
                        elif family==6: weight=(1 if h in (1,2+variant,5+frame,9+variant*2) else .005)/h**(.4+.1*frame)
                        elif family==7: weight=(.02+.98*abs(math.cos(h*(1.2+.13*variant)+frame*.3)))/h**(.55+.15*frame)
                        elif family==8: weight=(1 if h in (1, 3+variant, 8+frame*3, 17+variant*4) else .002)/h**.3
                        elif family==9: weight=(1 if h%2==0 else .01)*abs(math.sin(h*(.3+.1*variant)+frame*.5))/h**(.5+.1*frame)
                        elif family==10: weight=(1 if h%(5+variant)==1 else .005)/h**(.3+.2*frame)
                        elif family==11: weight=(1 if h in (1, 6+variant*2, 13+frame*3, 23+variant*3) else .003)/h**(.3+.15*frame)
                        # New families 12-23: evolving formants, partial clusters,
                        # spectral notches and inharmonic-like harmonic spacing.
                        elif family==12: weight=math.exp(-((h-(4+variant*3+frame*4))/ (2+variant))**2)+.02/h
                        elif family==13: weight=.8*math.exp(-((h-(3+variant+frame*2))/2)**2)+.7*math.exp(-((h-(14+variant*4-frame))/4)**2)+.02/h
                        elif family==14: weight=(.02 if abs(h-(5+variant*2+frame*3))<3 else 1)/h**(.55+.12*variant)
                        elif family==15: weight=(1 if h in (1,4+variant,11+frame*2,22+variant*3) else .002)/h**(.18+.08*frame)
                        elif family==16: weight=(.1+.9*abs(math.sin(h*h*(.13+.02*variant)+frame*.7)))/h**(.65+.1*frame)
                        elif family==17: weight=(1 if (h+frame)%(3+variant)==0 else .015)/h**(.25+.16*frame)
                        elif family==18: weight=(.02+.98*abs(math.cos(h*(.24+.09*variant)+frame*.9))**4)/h**(.5+.1*variant)
                        elif family==19: weight=(1 if h in (1,2,3+variant*2,20+frame*5) else .003)/h**(.3+.1*frame)
                        elif family==20: weight=math.exp(-((h-(9+variant*4-frame*2))/ (3+frame))**2)+.05/h
                        elif family==21: weight=(.02 if h%(4+variant)==frame%(4+variant) else 1)/h**(.7+.1*frame)
                        elif family==22: weight=(.1+.9*abs(math.sin(h*(1.9+.2*variant)+frame*.6)))/h**(.2+.15*frame)
                        else: weight=(1 if h in (1,7+frame*3,16+variant*4,35-frame*4) else .001)/h**(.2+.1*variant)
                        # Retain every established ID 0-51 byte-for-byte.
                        # New IDs 52-99 use 12 distinct spectral architectures.
                        # Alternate families sweep smoothly or switch between
                        # sharply contrasting harmonic structures across frames.
                        phase=.13*frame*h+.07*variant*h
                        if wave>=48:
                            group=(wave-48)//4
                            t=frame/3
                            shift=variant*.37
                            smooth=(group%2==0)
                            u=t if smooth else (0.06 if frame<2 else .94)
                            def bell(center,width):
                                return math.exp(-((h-center)/width)**2)
                            if group==0: # breath / breathy harmonic haze
                                weight=(.06+.94*bell(2+u*15+shift,2+u*4))/h**.4
                                phase+=.4*math.sin(h*.31+u*3)
                            elif group==1: # glass / discrete bell partials
                                peaks=(1,4+variant,11+frame*5,29-frame*3)
                                weight=sum(bell(q,.45) for q in peaks)/h**.12
                                phase+=h*h*.17
                            elif group==2: # reed / migrating formant pairs
                                weight=(.025+bell(4+u*9+shift,1.5)+.8*bell(18-u*9,2.8))/h**.3
                                phase+=.2*math.sin(h*.5)
                            elif group==3: # hollow / fundamental to upper clusters
                                weight=(1-u)*bell(h,1.3)+u*(bell(7+variant,1.1)+bell(23-frame*2,1.7))
                                phase+=h*.43*frame
                            elif group==4: # pulse train / narrow comb teeth
                                weight=(.015+.985*(.5+.5*math.cos(h*(1.1+u*1.4+shift)))**12)/h**.4
                                phase+=h*.19
                            elif group==5: # metal / dissonant high clusters
                                weight=(.02+bell(5+variant,1)+bell(17+frame*5,1.3)+bell(39-frame*3,1.8))/h**.08
                                phase+=h*h*(.06+u*.11)
                            elif group==6: # subharmonic-style low partial bloom
                                weight=(.02+bell(1+u*7,1.1)+.6*bell(3+u*13,2))/h**.65
                                phase+=.7*math.sin(h*.17+u*5)
                            elif group==7: # fractured / odd-even inversion
                                weight=((1-u) if h%2 else u)/h**(.3+.7*u)
                                phase+=math.pi*(h%3==0)*u
                            elif group==8: # vocal / two resonant vowel peaks
                                weight=(.015+bell(3+variant+u*6,1.2)+.7*bell(12+variant*2-u*5,2))/h**.25
                                phase+=.12*h*u
                            elif group==9: # noise-like / deterministic harmonic scatter
                                seed=abs(math.sin(h*78.233+variant*12.989+frame*37.719))
                                weight=(.01+seed**(1+frame*2))/h**(.15+.15*u)
                                phase+=h*h*.21+variant
                            elif group==10: # minimal / sparse, shifting partials
                                weight=(bell(1, .7)+(.1+.7*u)*bell(2+variant+u*5,.8)+.3*bell(9+variant*3,1))/h**.3
                                phase+=.12*frame*h
                            else: # alien / spectral rotation and phase scrambling
                                weight=(.02+abs(math.sin(h*h*(.03+.015*variant)+u*4))**6)/h**.28
                                phase+=h*h*(.1+.21*u)
                        # Curated v0.2.2 tables use new IDs 100-107 (wave 96-103).
                        # Historical tables 0-99 remain bit-for-bit unchanged.
                        if wave>=96:
                            core=wave-96
                            t=frame/3
                            if core==0: # Pure: fundamental -> octave -> fifth
                                weight=(1-t)*(.98 if h==1 else .0)+t*(.75 if h==2 else .4 if h==3 else 0)
                            elif core==1: # Analog: saw -> square -> narrow pulse
                                weight=(1/h**(1.15-.65*t))*(1 if frame==0 else (1 if h%2 else .05) if frame==1 else (1 if h%3==1 else .03) if frame==2 else 1)
                            elif core==2: # Hollow: odd -> fifth-heavy -> high airy
                                weight=(1 if h%2 else .0)/h**(.9-.45*t)
                                # Hollow: strong fundamental cavity opens into upper odd partials.
                                if frame<=1 and h>=7:weight*=.12
                                if frame>=2 and h<7:weight*=.015
                            elif core==3: # Vocal: two formants move in opposing directions
                                weight=.03/h+.95*math.exp(-((h-(3+10*t))/1.6)**2)+.8*math.exp(-((h-(19-10*t))/2.4)**2)
                            elif core==4: # Glass: isolated, bell-like harmonic clusters
                                weight=sum(math.exp(-((h-k)/.42)**2)*a for k,a in ((1,.08),(7+frame*3,1),(19+frame*4,.8),(37-frame*2,.5)))
                                phase+=h*h*.17
                            elif core==5: # Metal: hard spectral shifts, phase-distorted clusters
                                weight=sum(math.exp(-((h-k)/1.2)**2)*a for k,a in ((2,.65),(8+frame*5,1),(27-frame*4,.9),(43-frame*3,.7)))
                                phase+=h*h*(.23+.12*t)
                            elif core==6: # Organic: smoothly blooming high harmonics
                                weight=(.7 if h==1 else .04/h)+(.12+.85*t)*math.exp(-((h-(4+14*t))/ (2+3*t))**2)
                                phase+=.3*math.sin(h*.3+t*3)
                            else: # Alien: radical alternating spectral geometry
                                weight=(.9 if h==1 and frame==0 else .0)
                                if frame==1:weight=(1 if h%7==1 else .005)/h**.25
                                if frame==2:weight=(1 if h in (3,11,23,41) else .002)/h**.12
                                if frame==3:weight=(1 if h%2==0 else .001)/h**.1
                                phase+=h*h*(.13+.15*t)
                        v+=weight*math.sin(h*p+phase)
                    values.append(v)
                # Preserve the 48 established expanded waves bit-for-bit.
                # For new waves, remove numerical DC and apply conservative
                # peak normalization to prevent morph-frame loudness spikes.
                if wave >= 48:
                    dc=sum(values)/N
                    values=[v-dc for v in values]
                peak=max(abs(v) for v in values) or 1.
                f.write('{'+','.join(f'{.87*v/peak:.7f}f' for v in values)+'},\n')
            f.write('},\n')
        f.write('},\n')
    f.write('};\n#endif\n')
print(f'{DEST}: {DEST.stat().st_size} bytes')
