/* Sprig WT: independently authored wavetable sound generator for Schwung.
 * Freestanding C11, no libc dependencies, no file I/O or allocations in DSP.
 * API layout matches src/host/plugin_api_v1.h from charlesvestal/schwung.
 * All parameters are integer display values, eliminating RT parsing costs.
 */
#include <stdint.h>
#include <stddef.h>
#include "tables.h"
#include "wavetable_engine.h"
#include "expanded_tables.h"

#define SPRIG_VOICES 8
#define SPRIG_INSTANCES 8
#define SR 44100.0f
#define TABLE_MASK 255
#define ATTACK 1
#define DECAY 2
#define SUSTAIN 3
#define RELEASE 4

/* Reproduced ABI v2 layout, from Schwung's public plugin_api_v1.h. */
typedef struct plugin_api_v2 {
    uint32_t api_version;
    void *(*create_instance)(const char *, const char *);
    void (*destroy_instance)(void *);
    void (*on_midi)(void *, const uint8_t *, int, int);
    void (*set_param)(void *, const char *, const char *);
    int (*get_param)(void *, const char *, char *, int);
    int (*get_error)(void *, char *, int);
    void (*render_block)(void *, int16_t *, int);
} plugin_api_v2_t;

typedef struct {
    float phase, phase2, increment, env, vel, release_step;
    float ic1, ic2, ic1_r, ic2_r, filter_env, smooth_cut;
    uint8_t filter_stage;
    unsigned age;
    uint8_t note, band, stage, down;
} Voice;

typedef struct {
    int wavetable, shape, wave, wt_bank, wt_table, spectral_shape, legacy_shape, position, cutoff, resonance, attack, decay, sustain, release, level;
    int osc1_warp_type, osc1_warp, osc1_detune, osc1_octave, osc1_pan, osc1_volume;
    int osc2_wavetable, osc2_position, osc2_warp_type, osc2_warp, osc2_detune, osc2_octave, osc2_pan, osc2_volume;
    int osc2_level, detune, lfo_rate, lfo_depth, lfo_wt_depth, drive;
    int filter_env_amt, filter_env_attack, filter_env_decay, lfo_filter;
    float lfo_phase;
    float smooth_wave, smooth_position, smooth_bank, smooth_table, smooth_shape, smooth_g, smooth_res, smooth_level;
    unsigned age;
    Voice voices[SPRIG_VOICES];
} Synth;

typedef struct { volatile int allocated; Synth synth; } Slot;
static Slot slots[SPRIG_INSTANCES];

static int eq(const char *a,const char *b){
    if(!a||!b)return 0;
    while(*a && *a==*b){a++;b++;}
    return *a==*b;
}
static float clampf(float x,float lo,float hi){ return x<lo?lo:x>hi?hi:x; }
static int clampi(int x,int lo,int hi){ return x<lo?lo:x>hi?hi:x; }
static int integer(const char *p){
    if(!p)return 0;
    int sign=1,val=0;
    if(*p=='-'){sign=-1;p++;}
    for(int i=0;i<9 && *p>='0' && *p<='9';++i,++p)val=val*10+(*p-'0');
    return sign*val;
}
static void wipe(void *ptr,size_t n){ volatile unsigned char *p=ptr; while(n--)*p++=0; }
static int write_str(char *out,int capacity,const char *s){
    int i=0;
    if(!out||capacity<=0)return -1;
    while(s[i]){ if(i>=capacity-1){out[0]=0;return -1;} out[i]=s[i];i++; }
    out[i]=0;return i;
}
static int append(char *s,int cap,int at,const char *part){
    if(at<0)return -1;
    for(int j=0;part[j];j++){if(at>=cap-1)return -1;s[at++]=part[j];}
    s[at]=0;return at;
}
static int append_int(char *s,int cap,int at,int v){
    char rev[16];int j=0;
    if(v<0){at=append(s,cap,at,"-");v=-v;}
    do{rev[j++]=(char)('0'+v%10);v/=10;}while(v && j<15);
    while(j--){if(at>=cap-1)return -1;s[at++]=rev[j];}
    s[at]=0;return at;
}
static void defaults(Synth *s){
    wipe(s,sizeof(*s));
    s->wavetable=1;s->shape=50;s->wave=1;s->spectral_shape=50;s->legacy_shape=50;s->position=50;s->cutoff=78;s->resonance=15;
    s->attack=10;s->decay=230;s->sustain=72;s->release=240;s->level=65;
    s->osc1_warp_type=0;s->osc1_warp=0;s->osc1_detune=50;s->osc1_octave=2;s->osc1_pan=50;s->osc1_volume=100;
    s->osc2_wavetable=1;s->osc2_position=50;s->osc2_warp_type=0;s->osc2_warp=0;s->osc2_detune=50;s->osc2_octave=2;s->osc2_pan=50;s->osc2_volume=0;
    s->osc2_level=0;s->detune=50;s->lfo_rate=22;s->lfo_depth=0;s->lfo_wt_depth=0;s->drive=0;
    s->filter_env_amt=0;s->filter_env_attack=5;s->filter_env_decay=400;s->lfo_filter=0;
    s->smooth_wave=1;s->smooth_position=1.5f;s->smooth_bank=0;s->smooth_table=1;s->smooth_shape=50;
    s->smooth_g=sprig_cutoff_g[s->cutoff];
    s->smooth_res=0.15f;s->smooth_level=.65f;
}
static void *create_instance(const char *module_dir,const char *json_defaults){
    (void)module_dir;(void)json_defaults;
    for(int i=0;i<SPRIG_INSTANCES;i++){
        int expected=0;
        if(__atomic_compare_exchange_n(&slots[i].allocated,&expected,1,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE)){
            defaults(&slots[i].synth);return &slots[i].synth;
        }
    }
    return 0;
}
static void destroy_instance(void *instance){
    if(!instance)return;
    for(int i=0;i<SPRIG_INSTANCES;i++)if(instance==&slots[i].synth){
        __atomic_store_n(&slots[i].allocated,0,__ATOMIC_RELEASE);return;
    }
}
static void note_on(Synth *s,unsigned note,unsigned vel){
    int chosen=-1;unsigned oldest=0;
    for(int i=0;i<SPRIG_VOICES;i++)if(s->voices[i].stage==0){chosen=i;break;}
    if(chosen<0)for(int i=0;i<SPRIG_VOICES;i++)if(s->voices[i].stage==RELEASE){chosen=i;break;}
    if(chosen<0){for(int i=0;i<SPRIG_VOICES;i++){
        if(i==0 || s->voices[i].age<oldest){oldest=s->voices[i].age;chosen=i;}
    }}
    Voice *v=&s->voices[chosen];wipe(v,sizeof(*v));
    v->note=note;v->band=sprig_note_band[note];v->increment=sprig_note_phase_inc[note];
    v->vel=(float)vel/127.0f;v->stage=ATTACK;v->down=1;v->age=++s->age;
    v->filter_stage=1;v->smooth_cut=(float)s->cutoff;
}
static void note_off(Synth *s,unsigned note){
    for(int i=0;i<SPRIG_VOICES;i++){
        Voice *v=&s->voices[i];
        if(v->stage && v->down && v->note==note){
            v->down=0;v->stage=RELEASE;
            v->release_step=v->env/(clampf((float)s->release,1.f,2000.f)*.001f*SR);
        }
    }
}
static void on_midi(void *instance,const uint8_t *msg,int len,int source){
    if(!instance||!msg||len<1 || source==5)return;
    Synth *s=instance;uint8_t kind=msg[0]&0xf0;
    if((kind==0x90 || kind==0x80) && len>=3 && msg[1]<128){
        if(kind==0x90 && msg[2])note_on(s,msg[1],msg[2]);
        else note_off(s,msg[1]);
    }else if(kind==0xb0 && len>=3 && (msg[1]==123 || msg[1]==120)){
        for(int i=0;i<SPRIG_VOICES;i++){
            Voice *v=&s->voices[i];v->down=0;v->stage=RELEASE;
            v->release_step=v->env/(SR*.015f);
        }
    }
}

typedef struct { const char *name; int min,max; size_t offset; } Param;
#define P(key,hi) {#key,0,hi,offsetof(Synth,key)}
static const Param params[]={
    P(wavetable,107),P(shape,100),P(wave,3),P(wt_bank,1),P(wt_table,95),P(spectral_shape,100),P(legacy_shape,100),P(position,100),P(cutoff,100),P(resonance,100),
    P(attack,2000),P(decay,2000),P(sustain,100),P(release,2000),P(level,100),
    P(osc1_warp_type,7),P(osc1_warp,100),P(osc1_detune,100),P(osc1_octave,4),P(osc1_pan,100),P(osc1_volume,100),
    P(osc2_wavetable,107),P(osc2_position,100),P(osc2_warp_type,7),P(osc2_warp,100),P(osc2_detune,100),P(osc2_octave,4),P(osc2_pan,100),P(osc2_volume,100),
    P(osc2_level,100),P(detune,100),P(lfo_rate,100),P(lfo_depth,100),P(lfo_wt_depth,100),P(drive,100),
    P(filter_env_amt,100),P(filter_env_attack,2000),P(filter_env_decay,2000),P(lfo_filter,100)
};
#define NP ((int)(sizeof(params)/sizeof(params[0])))
static int *param_ptr(Synth *s,int i){return (int*)((char*)s+params[i].offset);}
static void set_one(Synth *s,const char *key,const char *value){
    /* Stable proxy keys are necessary because Schwung caches physical knob
     * mappings when the component is loaded. */
    if(eq(key,"bank_select")){if(s->wt_bank==0)s->wave=clampi(integer(value),0,3);else s->wt_table=clampi(integer(value),0,95);return;}
    if(eq(key,"bank_shape")){if(s->wt_bank==0)s->legacy_shape=clampi(integer(value),0,100);else s->spectral_shape=clampi(integer(value),0,100);return;}
    if(eq(key,"wave")){
        if(eq(value,"Sine"))value="0";
        else if(eq(value,"Saw"))value="1";
        else if(eq(value,"Square")||eq(value,"Pulse"))value="2";
        else if(eq(value,"Triangle"))value="3";
    }
    for(int i=0;i<NP;i++)if(eq(key,params[i].name)){
        *param_ptr(s,i)=clampi(integer(value),params[i].min,params[i].max);return;
    }
}
static void set_param(void *instance,const char *key,const char *value){
    if(!instance||!key||!value)return;
    Synth *s=instance;
    if(eq(key,"state")){
        char k[32],v[24];int ix=0;
        while(value[ix] && ix<512){
            int ki=0,vi=0;
            while(value[ix] && value[ix]!='=' && value[ix]!=',' && ki<30)k[ki++]=value[ix++];
            k[ki]=0;
            if(value[ix]!='='){if(value[ix])ix++;continue;}ix++;
            while(value[ix] && value[ix]!=',' && vi<22)v[vi++]=value[ix++];
            v[vi]=0;
            if(value[ix]==',')ix++;
            set_one(s,k,v);
        }
        return;
    }
    set_one(s,key,value);
}
/* Sound generators must serve their hierarchy via get_param; module.json is ignored. */
/* Host may re-query hierarchy when bank changes. Keep legacy as default. */
static const char ui_hierarchy_json[] = "{\"levels\":{\"root\":{\"label\":\"Sprig WT\",\"knobs\":[\"lfo_rate\",\"lfo_depth\",\"osc1_detune\",\"osc2_detune\",\"osc2_volume\",\"wavetable\",\"position\",\"level\"],\"params\":[{\"key\":\"face\",\"name\":\"Synth Face\",\"type\":\"canvas\",\"canvas_script\":\"canvas.js\",\"as_page\":true,\"page_first\":true,\"show_value\":false,\"extra_keys\":[\"voice_activity\",\"cutoff\",\"lfo_depth\",\"filter_env_amt\",\"wt_bank\",\"wt_table\",\"wave\",\"position\",\"spectral_shape\",\"bank_select\",\"bank_shape\",\"legacy_shape\",\"wavetable\",\"shape\"]},{\"level\":\"osc1\",\"label\":\"OSC 1\"},{\"level\":\"osc2\",\"label\":\"OSC 2\"},{\"level\":\"filter\",\"label\":\"Filter\"},{\"level\":\"motion\",\"label\":\"Motion\"},{\"level\":\"amp\",\"label\":\"Amp Envelope\"}]},\"osc\":{\"label\":\"Oscillators\",\"knobs\":[\"wavetable\",\"position\",\"shape\",\"osc2_level\",\"detune\"],\"params\":[\"wavetable\",\"position\",\"shape\",\"osc2_level\",\"detune\"]},\"filter\":{\"label\":\"Filter + Color\",\"knobs\":[\"cutoff\",\"resonance\",\"drive\",\"filter_env_amt\",\"filter_env_attack\",\"filter_env_decay\",\"lfo_filter\"],\"params\":[\"cutoff\",\"resonance\",\"drive\",\"filter_env_amt\",\"filter_env_attack\",\"filter_env_decay\",\"lfo_filter\"]},\"motion\":{\"label\":\"Motion\",\"knobs\":[\"lfo_rate\",\"lfo_depth\",\"lfo_filter\",\"position\"],\"params\":[\"lfo_rate\",\"lfo_depth\",\"lfo_filter\",\"position\"]},\"amp\":{\"label\":\"Amp Envelope\",\"knobs\":[\"attack\",\"decay\",\"sustain\",\"release\"],\"params\":[\"attack\",\"decay\",\"sustain\",\"release\"]},\"output\":{\"label\":\"Output\",\"knobs\":[\"level\"],\"params\":[\"level\"]},\"filter_env\":{\"label\":\"Filter Envelope\",\"knobs\":[\"filter_env_attack\",\"filter_env_decay\",\"filter_env_amt\",\"lfo_filter\"],\"params\":[\"filter_env_attack\",\"filter_env_decay\",\"filter_env_amt\",\"lfo_filter\"]},\"osc1\":{\"label\":\"OSC 1\",\"knobs\":[\"wavetable\",\"position\",\"osc1_octave\",\"osc1_warp_type\",\"osc1_warp\",\"osc1_detune\",\"osc1_pan\",\"osc1_volume\"],\"params\":[\"wavetable\",\"position\",\"osc1_octave\",\"osc1_warp_type\",\"osc1_warp\",\"osc1_detune\",\"osc1_pan\",\"osc1_volume\"]},\"osc2\":{\"label\":\"OSC 2\",\"knobs\":[\"osc2_wavetable\",\"osc2_position\",\"osc2_octave\",\"osc2_warp_type\",\"osc2_warp\",\"osc2_detune\",\"osc2_pan\",\"osc2_volume\"],\"params\":[\"osc2_wavetable\",\"osc2_position\",\"osc2_octave\",\"osc2_warp_type\",\"osc2_warp\",\"osc2_detune\",\"osc2_pan\",\"osc2_volume\"]}}}";
static const char ui_hierarchy_expanded_json[] = "{\"levels\":{\"root\":{\"label\":\"Sprig WT\",\"knobs\":[\"lfo_rate\",\"lfo_depth\",\"osc1_detune\",\"osc2_detune\",\"osc2_volume\",\"wavetable\",\"position\",\"level\"],\"params\":[{\"key\":\"face\",\"name\":\"Synth Face\",\"type\":\"canvas\",\"canvas_script\":\"canvas.js\",\"as_page\":true,\"page_first\":true,\"show_value\":false,\"extra_keys\":[\"voice_activity\",\"cutoff\",\"lfo_depth\",\"filter_env_amt\",\"wt_bank\",\"wt_table\",\"wave\",\"position\",\"spectral_shape\",\"bank_select\",\"bank_shape\",\"legacy_shape\",\"wavetable\",\"shape\"]},{\"level\":\"osc1\",\"label\":\"OSC 1\"},{\"level\":\"osc2\",\"label\":\"OSC 2\"},{\"level\":\"filter\",\"label\":\"Filter\"},{\"level\":\"motion\",\"label\":\"Motion\"},{\"level\":\"amp\",\"label\":\"Amp Envelope\"}]},\"osc\":{\"label\":\"Oscillators\",\"knobs\":[\"wavetable\",\"position\",\"shape\",\"osc2_level\",\"detune\"],\"params\":[\"wavetable\",\"position\",\"shape\",\"osc2_level\",\"detune\"]},\"filter\":{\"label\":\"Filter + Color\",\"knobs\":[\"cutoff\",\"resonance\",\"drive\",\"filter_env_amt\",\"filter_env_attack\",\"filter_env_decay\",\"lfo_filter\"],\"params\":[\"cutoff\",\"resonance\",\"drive\",\"filter_env_amt\",\"filter_env_attack\",\"filter_env_decay\",\"lfo_filter\"]},\"motion\":{\"label\":\"Motion\",\"knobs\":[\"lfo_rate\",\"lfo_depth\",\"lfo_filter\",\"position\"],\"params\":[\"lfo_rate\",\"lfo_depth\",\"lfo_filter\",\"position\"]},\"amp\":{\"label\":\"Amp Envelope\",\"knobs\":[\"attack\",\"decay\",\"sustain\",\"release\"],\"params\":[\"attack\",\"decay\",\"sustain\",\"release\"]},\"output\":{\"label\":\"Output\",\"knobs\":[\"level\"],\"params\":[\"level\"]},\"filter_env\":{\"label\":\"Filter Envelope\",\"knobs\":[\"filter_env_attack\",\"filter_env_decay\",\"filter_env_amt\",\"lfo_filter\"],\"params\":[\"filter_env_attack\",\"filter_env_decay\",\"filter_env_amt\",\"lfo_filter\"]},\"osc1\":{\"label\":\"OSC 1\",\"knobs\":[\"wavetable\",\"position\",\"osc1_octave\",\"osc1_warp_type\",\"osc1_warp\",\"osc1_detune\",\"osc1_pan\",\"osc1_volume\"],\"params\":[\"wavetable\",\"position\",\"osc1_octave\",\"osc1_warp_type\",\"osc1_warp\",\"osc1_detune\",\"osc1_pan\",\"osc1_volume\"]},\"osc2\":{\"label\":\"OSC 2\",\"knobs\":[\"osc2_wavetable\",\"osc2_position\",\"osc2_octave\",\"osc2_warp_type\",\"osc2_warp\",\"osc2_detune\",\"osc2_pan\",\"osc2_volume\"],\"params\":[\"osc2_wavetable\",\"osc2_position\",\"osc2_octave\",\"osc2_warp_type\",\"osc2_warp\",\"osc2_detune\",\"osc2_pan\",\"osc2_volume\"]}}}";
/* Schwung v1.9 reads chain_params from the live DSP, not module.json.
 * Keep this in sync with src/module.json capabilities.chain_params.
 * Without it, v1.9 cannot identify Synth Face as an as_page canvas and
 * renders an orphan SYFACE knob instead of the authored graphical page. */
static const char chain_params_json[] = "[{\"key\":\"wavetable\",\"name\":\"OSC 1 Wavetable\",\"type\":\"int\",\"min\":0,\"max\":107,\"step\":1,\"default\":1},{\"key\":\"shape\",\"name\":\"Shape\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"wave\",\"name\":\"Wave\",\"type\":\"enum\",\"options\":[\"Sine\",\"Saw\",\"Square\",\"Triangle\"],\"peek\":false,\"default\":1},{\"key\":\"wt_bank\",\"name\":\"WT Bank\",\"type\":\"enum\",\"options\":[\"Legacy\",\"Expanded\"],\"peek\":false,\"default\":0},{\"key\":\"wt_table\",\"name\":\"WT Table\",\"type\":\"int\",\"min\":0,\"max\":95,\"step\":1,\"default\":0},{\"key\":\"spectral_shape\",\"name\":\"Spectral Shape\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"bank_select\",\"name\":\"Wave / Table\",\"type\":\"int\",\"min\":0,\"max\":95,\"step\":1,\"default\":1},{\"key\":\"bank_shape\",\"name\":\"Legacy / Spectral Shape\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"legacy_shape\",\"name\":\"Legacy Shape\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"position\",\"name\":\"OSC 1 WT Position\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":50,\"display_format\":\"%.0f\"},{\"key\":\"cutoff\",\"name\":\"Cutoff\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":78,\"display_format\":\"%.0f\"},{\"key\":\"resonance\",\"name\":\"Resonance\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":15,\"display_format\":\"%.0f\"},{\"key\":\"attack\",\"name\":\"Attack\",\"type\":\"float\",\"min\":0,\"max\":2000,\"step\":1,\"default\":10,\"unit\":\"ms\",\"display_format\":\"%.0f\"},{\"key\":\"decay\",\"name\":\"Decay\",\"type\":\"float\",\"min\":0,\"max\":2000,\"step\":1,\"default\":230,\"unit\":\"ms\",\"display_format\":\"%.0f\"},{\"key\":\"sustain\",\"name\":\"Sustain\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":72,\"display_format\":\"%.0f\"},{\"key\":\"release\",\"name\":\"Release\",\"type\":\"float\",\"min\":0,\"max\":2000,\"step\":1,\"default\":240,\"unit\":\"ms\",\"display_format\":\"%.0f\"},{\"key\":\"level\",\"name\":\"Output Level\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":65,\"display_format\":\"%.0f\"},{\"key\":\"osc2_level\",\"name\":\"Osc 2 Mix\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":0,\"display_format\":\"%.0f\"},{\"key\":\"detune\",\"name\":\"Osc 2 Detune\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":50,\"display_format\":\"%.0f\"},{\"key\":\"lfo_rate\",\"name\":\"Motion Rate\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":22,\"display_format\":\"%.0f\"},{\"key\":\"lfo_depth\",\"name\":\"Motion Depth\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":0,\"display_format\":\"%.0f\"},{\"key\":\"lfo_wt_depth\",\"name\":\"WT LFO Depth\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":0},{\"key\":\"drive\",\"name\":\"Drive\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":0,\"display_format\":\"%.0f\"},{\"key\":\"filter_env_amt\",\"name\":\"Filter Env Amount\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":0,\"display_format\":\"%.0f\"},{\"key\":\"filter_env_attack\",\"name\":\"Filter Env Attack\",\"type\":\"float\",\"min\":0,\"max\":2000,\"step\":1,\"default\":5,\"display_format\":\"%.0f\"},{\"key\":\"filter_env_decay\",\"name\":\"Filter Env Decay\",\"type\":\"float\",\"min\":0,\"max\":2000,\"step\":1,\"default\":400,\"display_format\":\"%.0f\"},{\"key\":\"lfo_filter\",\"name\":\"LFO Filter Depth\",\"type\":\"float\",\"min\":0,\"max\":100,\"step\":1,\"default\":0,\"display_format\":\"%.0f\"},{\"key\":\"face\",\"name\":\"Synth Face\",\"type\":\"canvas\",\"canvas_script\":\"canvas.js\",\"as_page\":true,\"page_first\":true,\"show_value\":false,\"extra_keys\":[\"voice_activity\",\"cutoff\",\"lfo_depth\",\"filter_env_amt\",\"wt_bank\",\"wt_table\",\"wave\",\"position\",\"spectral_shape\",\"bank_select\",\"bank_shape\",\"legacy_shape\",\"wavetable\",\"shape\"]},{\"key\":\"voice_activity\",\"name\":\"Voice Activity\",\"type\":\"int\",\"min\":0,\"max\":8,\"access\":\"read\"},{\"key\":\"osc1_warp_type\",\"name\":\"OSC 1 Warp Type\",\"type\":\"enum\",\"options\":[\"Off\",\"Sync\",\"Bend+\",\"Bend-\",\"PWM\",\"Asym\",\"Mirror\",\"Quant\"],\"default\":0},{\"key\":\"osc1_warp\",\"name\":\"OSC 1 Warp\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":0},{\"key\":\"osc1_detune\",\"name\":\"OSC 1 Detune\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"osc1_pan\",\"name\":\"OSC 1 Pan\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"osc1_volume\",\"name\":\"OSC 1 Volume\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":100},{\"key\":\"osc2_wavetable\",\"name\":\"OSC 2 Wavetable\",\"type\":\"int\",\"min\":0,\"max\":107,\"step\":1,\"default\":1},{\"key\":\"osc2_position\",\"name\":\"OSC 2 WT Position\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"osc2_warp_type\",\"name\":\"OSC 2 Warp Type\",\"type\":\"enum\",\"options\":[\"Off\",\"Sync\",\"Bend+\",\"Bend-\",\"PWM\",\"Asym\",\"Mirror\",\"Quant\"],\"default\":0},{\"key\":\"osc2_warp\",\"name\":\"OSC 2 Warp\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":0},{\"key\":\"osc2_detune\",\"name\":\"OSC 2 Detune\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"osc2_pan\",\"name\":\"OSC 2 Pan\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":50},{\"key\":\"osc2_volume\",\"name\":\"OSC 2 Volume\",\"type\":\"int\",\"min\":0,\"max\":100,\"step\":1,\"default\":0},{\"key\":\"osc1_octave\",\"name\":\"OSC 1 Octave\",\"type\":\"enum\",\"options\":[\"-2\",\"-1\",\"0\",\"+1\",\"+2\"],\"default\":2},{\"key\":\"osc2_octave\",\"name\":\"OSC 2 Octave\",\"type\":\"enum\",\"options\":[\"-2\",\"-1\",\"0\",\"+1\",\"+2\"],\"default\":2}]";
static int get_param(void *instance,const char *key,char *buf,int len){
    if(key && eq(key,"ui_hierarchy"))return write_str(buf,len,ui_hierarchy_json);
    if(key && eq(key,"chain_params"))return write_str(buf,len,chain_params_json);
    if(eq(key,"module_id"))return write_str(buf,len,"sprig-wt");
    if(!instance||!key||!buf||len<=0)return -1;
    Synth *s=instance;
    /* Count sounding voices, including release tails, for graphical animation.
     * This read-only value never enters the audio parameter or preset list. */
    if(eq(key,"bank_select")){buf[0]=0;return append_int(buf,len,0,s->wt_bank?s->wt_table:s->wave);}
    if(eq(key,"bank_shape")){buf[0]=0;return append_int(buf,len,0,s->wt_bank?s->spectral_shape:s->legacy_shape);}
    if(eq(key,"voice_activity")){
        int active=0;
        for(int i=0;i<SPRIG_VOICES;i++)if(s->voices[i].stage)active++;
        buf[0]=0;return append_int(buf,len,0,active);
    }
    if(eq(key,"state")){
        int at=0;buf[0]=0;
        for(int i=0;i<NP;i++){
            if(i)at=append(buf,len,at,",");
            at=append(buf,len,at,params[i].name);
            at=append(buf,len,at,"=");
            at=append_int(buf,len,at,*param_ptr(s,i));
            if(at<0){buf[0]=0;return -1;}
        }
        return at;
    }
    for(int i=0;i<NP;i++)if(eq(key,params[i].name)){
        buf[0]=0;return append_int(buf,len,0,*param_ptr(s,i));
    }
    return -1;
}
static int get_error(void *instance,char *buf,int len){(void)instance;return write_str(buf,len,"");}

static float env_next(Synth *s,Voice *v){
    float sus=.01f*(float)s->sustain;
    switch(v->stage){
        case ATTACK:
            v->env+=1.0f/(SR*.001f*clampf((float)s->attack,1.f,2000.f));
            if(v->env>=1.f){v->env=1.f;v->stage=DECAY;}break;
        case DECAY:
            v->env-=(1.f-sus)/(SR*.001f*clampf((float)s->decay,1.f,2000.f));
            if(v->env<=sus){v->env=sus;v->stage=SUSTAIN;}break;
        case SUSTAIN:v->env=sus;break;
        case RELEASE:
            v->env-=v->release_step;
            if(v->env<=0.f){v->env=0.f;v->stage=0;v->ic1=0;v->ic2=0;v->ic1_r=0;v->ic2_r=0;}break;
        default:return 0;
    }
    return v->env;
}
static float lookup(int wave,int frame,int band,float phase){
    /* Legacy bank remains sample-for-sample identical to v0.2. */
    return sprig_table_lookup_legacy(wave,frame,band,phase);
}
static float expanded_lookup(int table,int frame,int band,float phase){
    int i=(int)phase & TABLE_MASK;
    float t=phase-(float)((int)phase);
    const float *row=sprig_expanded_tables[table][frame][band];
    return row[i]+(row[(i+1)&TABLE_MASK]-row[i])*t;
}
static float sample_wave(Voice *v,float wave,float pos){
    int w0=(int)wave; int w1=w0<3?w0+1:3;
    int p0=(int)pos; int p1=p0<3?p0+1:3;
    float wt=wave-(float)w0,pt=pos-(float)p0;
    float a=lookup(w0,p0,v->band,v->phase);
    float b=lookup(w0,p1,v->band,v->phase);
    float c=lookup(w1,p0,v->band,v->phase);
    float d=lookup(w1,p1,v->band,v->phase);
    return (a+(b-a)*pt)*(1-wt)+(c+(d-c)*pt)*wt;
}
static float warp_phase(float p,int mode,float amount){
    p=p-(float)(int)p;if(p<0.f)p+=1.f;
    float a=clampf(amount*.01f,0.f,1.f);
    if(a<=0.f || mode==0)return p;
    if(mode==1){p=p*(1.f+3.f*a);p-=(float)(int)p;}
    else if(mode==2)p+=(p*p-p)*a*.95f;
    else if(mode==3)p+=(p-p*p)*a*.95f;
    else if(mode==4){float q=.5f+.45f*a;p=p<q?.5f*p/q:.5f+.5f*(p-q)/(1.f-q);}
    else if(mode==5){float q=.5f-.4f*a;p=p<q?.5f*p/q:.5f+.5f*(p-q)/(1.f-q);}
    else if(mode==6){float q=p*(1.f+2.f*a);int n=(int)q;p=(n&1)?1.f-(q-n):q-n;}
    else if(mode==7){float steps=64.f-60.f*a;p=(float)(int)(p*steps)/steps;}
    return clampf(p,0.f,.99999f);
}
static float table_at(int table,float position,int band,float phase){
    int t=clampi(table,0,107);float pos=clampf(position,0.f,3.f);
    int p0=(int)pos,p1=p0<3?p0+1:3;float pt=pos-p0;
    float a=t<4?lookup(t,p0,band,phase):expanded_lookup(t-4,p0,band,phase);
    float b=t<4?lookup(t,p1,band,phase):expanded_lookup(t-4,p1,band,phase);
    return a+(b-a)*pt;
}
static int16_t pcm(float f){
    float x=clampf(f*32767.0f,-32767.f,32767.f);
    return (int16_t)(x>=0.f?x+.5f:x-.5f);
}
static void render_block(void *instance,int16_t *out,int frames){
    if(!out||frames<=0)return;
    if(frames>128)frames=128;
    Synth *s=instance;
    if(!s){for(int i=0;i<frames*2;i++)out[i]=0;return;}
    for(int j=0;j<frames;j++){
        s->smooth_wave+=.004f*((float)s->wave-s->smooth_wave);
        s->smooth_bank+=.0015f*((float)s->wt_bank-s->smooth_bank);
        s->smooth_table+=.0015f*((float)s->wavetable-s->smooth_table);
        s->smooth_shape+=.003f*((float)s->shape-s->smooth_shape);
        s->smooth_position+=.004f*(.03f*(float)s->position-s->smooth_position);
        s->smooth_g+=.004f*(sprig_cutoff_g[s->cutoff]-s->smooth_g);
        s->smooth_res+=.004f*(.01f*(float)s->resonance-s->smooth_res);
        s->smooth_level+=.004f*(.01f*(float)s->level-s->smooth_level);
        /* One global low-frequency modulator for subtle continuous wavetable motion. */
        float lfo_hz=.06f+.12f*(float)s->lfo_rate;
        s->lfo_phase+=lfo_hz*(256.f/SR);
        if(s->lfo_phase>=256.f)s->lfo_phase-=256.f;
        float lfo=lookup(0,0,0,s->lfo_phase);
        float wave=clampf(s->smooth_wave,0,3);
        float pos=clampf(s->smooth_position + (.015f*s->lfo_depth+.015f*s->lfo_wt_depth)*lfo,0,3);
        float pos2=clampf(.03f*(float)s->osc2_position + (.015f*s->lfo_depth+.015f*s->lfo_wt_depth)*lfo,0.f,3.f);
        float k=2.f-1.9f*s->smooth_res;
        float sumL=0.f,sumR=0.f;
        for(int i=0;i<SPRIG_VOICES;i++){
            Voice *v=&s->voices[i];if(!v->stage)continue;
            float env=env_next(s,v);if(!v->stage)continue;
            float table=clampf(s->smooth_table,0.f,107.f);
            int t0=(int)table,t1=t0<107?t0+1:107;float tm=table-(float)t0;
            float p1=warp_phase(v->phase/256.f,s->osc1_warp_type,(float)s->osc1_warp)*256.f;
            float x=table_at(t0,pos,v->band,p1);
            if(tm>.00001f)x+=(table_at(t1,pos,v->band,p1)-x)*tm;
            float sh=clampf((s->smooth_shape-50.f)/50.f,-1.f,1.f);
            if(sh!=0.f){
                float ph1=p1+8.f,ph2=p1-8.f;
                if(ph1>=256.f)ph1-=256.f;if(ph2<0.f)ph2+=256.f;
                float avg=.5f*(table_at(t0,pos,v->band,ph1)+table_at(t0,pos,v->band,ph2));
                x+=sh<0.f?(avg-x)*(-sh*.9f):(x-avg)*(sh*.85f);
            }
            x*=.01f*s->osc1_volume;
            float p2=warp_phase(v->phase2/256.f,s->osc2_warp_type,(float)s->osc2_warp)*256.f;
            float second=table_at(s->osc2_wavetable,pos2,v->band,p2)*(.01f*s->osc2_volume);
            second+=lookup(1,0,v->band,v->phase2)*(.006f*s->osc2_level);
            float pan1=.01f*(float)s->osc1_pan,pan2=.01f*(float)s->osc2_pan;
            float left=x*(1.f-pan1)+second*(1.f-pan2);
            float right=x*pan1+second*pan2;
            x=left+right;
            v->phase2+=v->increment*(1.f+.0005776f*((float)s->osc2_detune-50.f))*(s->osc2_octave==0?.25f:s->osc2_octave==1?.5f:s->osc2_octave==3?2.f:s->osc2_octave==4?4.f:1.f);
            while(v->phase2>=256.f)v->phase2-=256.f;
            v->phase+=v->increment*(1.f+.0005776f*((float)s->osc1_detune-50.f))*(s->osc1_octave==0?.25f:s->osc1_octave==1?.5f:s->osc1_octave==3?2.f:s->osc1_octave==4?4.f:1.f);
            while(v->phase>=256.f)v->phase-=256.f;
            /* Soft clipping before filter: independent nonlinear shaper. */
            if(s->drive>0){float d=.03f*(float)s->drive;float u=left*(1.f+d);left=u/(1.f+(u<0.f?-u:u)*d*.25f);u=right*(1.f+d);right=u/(1.f+(u<0.f?-u:u)*d*.25f);}
            /* Triggered filter envelope (attack then decay to zero). */
            if(v->filter_stage==1){
                float denom=(float)s->filter_env_attack*.001f*SR;
                if(denom<1.f)denom=1.f;
                v->filter_env+=1.f/denom;
                if(v->filter_env>=1.f){v->filter_env=1.f;v->filter_stage=2;}
            }else if(v->filter_stage==2){
                float denom=(float)s->filter_env_decay*.001f*SR;
                if(denom<1.f)denom=1.f;
                v->filter_env-=1.f/denom;
                if(v->filter_env<=0.f){v->filter_env=0.f;v->filter_stage=0;}
            }
            float cutoff_target=(float)s->cutoff + .45f*(float)s->filter_env_amt*v->filter_env + .35f*(float)s->lfo_filter*lfo;
            v->smooth_cut+=.005f*(clampf(cutoff_target,0.f,100.f)-v->smooth_cut);
            int ci=clampi((int)(v->smooth_cut+.5f),0,100);
            float g=sprig_cutoff_g[ci];
            float a1=1.f/(1.f+g*(g+k)),a2=g*a1,a3=g*a2;
            float v3=left-v->ic2;
            float v1=a1*v->ic1+a2*v3;
            float v2=v->ic2+a2*v->ic1+a3*v3;
            v->ic1=2*v1-v->ic1;
            v->ic2=2*v2-v->ic2;
            float v3r=right-v->ic2_r;
            float v1r=a1*v->ic1_r+a2*v3r;
            float v2r=v->ic2_r+a2*v->ic1_r+a3*v3r;
            v->ic1_r=2*v1r-v->ic1_r;
            v->ic2_r=2*v2r-v->ic2_r;
            sumL+=v2*env*v->vel;
            sumR+=v2r*env*v->vel;
        }
        /* Conservative poly mix to prevent clipping with eight voices. */
        out[2*j]=pcm(sumL*.48f*s->smooth_level);
        out[2*j+1]=pcm(sumR*.48f*s->smooth_level);
    }
}
static plugin_api_v2_t api={2,create_instance,destroy_instance,on_midi,set_param,get_param,get_error,render_block};
__attribute__((visibility("default"))) plugin_api_v2_t *move_plugin_init_v2(const void *host){
    (void)host;return &api;
}
