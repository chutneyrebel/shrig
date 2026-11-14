#!/usr/bin/env python3
"""Generate 48 original multi-frame, band-limited wavetable families.
No third-party samples; run before compiling DSP.
"""
from pathlib import Path
import math
N=256
LIMITS=[96,64,48,32,24,16,8,4,1]
DEST=Path(__file__).resolve().parents[1]/'src'/'expanded_tables.h'
with DEST.open('w') as f:
    f.write('/* Generated original spectral families. Do not edit. */\n#ifndef SPRIG_EXPANDED_TABLES_H\n#define SPRIG_EXPANDED_TABLES_H\n')
    f.write('#define SPRIG_EXPANDED_WAVES 48\n#define SPRIG_EXPANDED_FRAMES 4\n')
    f.write('static const float sprig_expanded_tables[48][4][9][256]={\n')
    for wave in range(48):
        f.write('{\n')
        for frame in range(4):
            f.write('{\n')
            for lim in LIMITS:
                values=[]
                for j in range(N):
                    p=2*math.pi*j/N
                    v=0.
                    for h in range(1,lim+1):
                        # Eight spectral character families, four timbre variants.
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
                        else: weight=(1 if h in (1, 6+variant*2, 13+frame*3, 23+variant*3) else .003)/h**(.3+.15*frame)
                        v+=weight*math.sin(h*p+.13*frame*h+.07*variant*h)
                    values.append(v)
                peak=max(abs(v) for v in values) or 1.
                f.write('{'+','.join(f'{.87*v/peak:.7f}f' for v in values)+'},\n')
            f.write('},\n')
        f.write('},\n')
    f.write('};\n#endif\n')
print(f'{DEST}: {DEST.stat().st_size} bytes')
