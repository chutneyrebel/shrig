/* Stage 3A: wavetable source boundary. No runtime allocation or file I/O.
 * Bank 0 is the immutable legacy Sprig WT 4-wave, 4-frame, 9-band table.
 * Future banks must be converted and band-limited OFF the audio thread.
 * Never renumber legacy wave indices or change their sample values.
 */
#ifndef SPRIG_WAVETABLE_ENGINE_H
#define SPRIG_WAVETABLE_ENGINE_H
#include "tables.h"
#define SPRIG_LEGACY_BANK 0
#define SPRIG_LEGACY_WAVES 4
#define SPRIG_LEGACY_FRAMES 4
#define SPRIG_LEGACY_BANDS 9
#define SPRIG_LEGACY_TABLE_LEN 256
/* This boundary intentionally serves only the legacy bank until new tables
 * and compatibility tests are ready. Unsupported bank IDs are not selectable. */
static inline float sprig_table_lookup_legacy(int wave,int frame,int band,float phase){
    int i=(int)phase & 255;
    float t=phase-(float)((int)phase);
    const float *row=sprig_wavetables[wave][frame][band];
    float a=row[i],b=row[(i+1)&255];
    return a+(b-a)*t;
}
#endif
