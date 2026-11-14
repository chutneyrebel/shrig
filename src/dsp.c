/* Sprig WT: independently authored wavetable sound generator for Schwung.
 * Freestanding C11, no libc dependencies, no file I/O or allocations in DSP.
 * API layout matches src/host/plugin_api_v1.h from charlesvestal/schwung.
 * All parameters are integer display values, eliminating RT parsing costs.
 */
#include <stdint.h>
#include <stddef.h>
#include "tables.h"

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
    float phase, increment, env, vel, release_step;
    float ic1, ic2;
    unsigned age;
    uint8_t note, band, stage, down;
} Voice;

typedef struct {
    int wave, position, cutoff, resonance, attack, decay, sustain, release, level;
    float smooth_wave, smooth_position, smooth_g, smooth_res, smooth_level;
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
    s->wave=1;s->position=50;s->cutoff=78;s->resonance=15;
    s->attack=10;s->decay=230;s->sustain=72;s->release=240;s->level=65;
    s->smooth_wave=1;s->smooth_position=1.5f;
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
    P(wave,3),P(position,100),P(cutoff,100),P(resonance,100),
    P(attack,2000),P(decay,2000),P(sustain,100),P(release,2000),P(level,100)
};
#define NP ((int)(sizeof(params)/sizeof(params[0])))
static int *param_ptr(Synth *s,int i){return (int*)((char*)s+params[i].offset);}
static void set_one(Synth *s,const char *key,const char *value){
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
static int get_param(void *instance,const char *key,char *buf,int len){
    if(eq(key,"module_id"))return write_str(buf,len,"sprig-wt");
    if(!instance||!key||!buf||len<=0)return -1;
    Synth *s=instance;
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
            if(v->env<=0.f){v->env=0.f;v->stage=0;v->ic1=0;v->ic2=0;}break;
        default:return 0;
    }
    return v->env;
}
static float lookup(int wave,int frame,int band,float phase){
    int i=(int)phase & TABLE_MASK;
    float t=phase-(float)((int)phase);
    const float *row=sprig_wavetables[wave][frame][band];
    float a=row[i],b=row[(i+1)&TABLE_MASK];return a+(b-a)*t;
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
        s->smooth_position+=.004f*(.03f*(float)s->position-s->smooth_position);
        s->smooth_g+=.004f*(sprig_cutoff_g[s->cutoff]-s->smooth_g);
        s->smooth_res+=.004f*(.01f*(float)s->resonance-s->smooth_res);
        s->smooth_level+=.004f*(.01f*(float)s->level-s->smooth_level);
        float wave=clampf(s->smooth_wave,0,3),pos=clampf(s->smooth_position,0,3);
        float g=s->smooth_g,k=2.f-1.9f*s->smooth_res;
        float a1=1.f/(1.f+g*(g+k)),a2=g*a1,a3=g*a2;
        float sum=0.f;
        for(int i=0;i<SPRIG_VOICES;i++){
            Voice *v=&s->voices[i];if(!v->stage)continue;
            float env=env_next(s,v);if(!v->stage)continue;
            float x=sample_wave(v,wave,pos);
            v->phase+=v->increment;
            if(v->phase>=256.f)v->phase-=256.f;
            float v3=x-v->ic2;
            float v1=a1*v->ic1+a2*v3;
            float v2=v->ic2+a2*v->ic1+a3*v3;
            v->ic1=2*v1-v->ic1;
            v->ic2=2*v2-v->ic2;
            sum+=v2*env*v->vel;
        }
        /* Conservative poly mix to prevent clipping with eight voices. */
        int16_t y=pcm(sum*.24f*s->smooth_level);
        out[2*j]=y;out[2*j+1]=y;
    }
}
static plugin_api_v2_t api={2,create_instance,destroy_instance,on_midi,set_param,get_param,get_error,render_block};
__attribute__((visibility("default"))) plugin_api_v2_t *move_plugin_init_v2(const void *host){
    (void)host;return &api;
}
