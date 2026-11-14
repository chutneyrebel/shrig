/* Sprig WT: native Move 128x64 graphics page.
 * Uses documented Schwung canvas overlay drawPage().
 * Pure rendering: no parameter reads, file operations or allocations from DSP.
 */
(function () {
  function bounded(v, fallback, lo, hi) {
    const n = Number(v);
    return Number.isFinite(n) ? Math.max(lo, Math.min(hi, n)) : fallback;
  }
  function value(values, key, fallback) {
    return values && values[key] != null ? Number(values[key]) : fallback;
  }
  function waveform(phase, wave, pos) {
    const sine = Math.sin(phase * 6.28318530718);
    const saw = phase * 2 - 1;
    const sq = phase < .5 ? 1 : -1;
    const tri = 1 - 4 * Math.abs(phase - .5);
    const shape = [sine, saw, sq, tri][Math.max(0, Math.min(3, wave | 0))];
    return shape * (1 - .19 * pos) + .19 * pos * Math.sin(phase * 18.84955592);
  }
  /* Visual approximation of the generated spectral families, not an audio readback.
   * Cap at 24 harmonics to keep the Move canvas render lightweight. */
  function expandedWave(phase, table, pos, shape=50) {
    const family=Math.floor(table/4),variant=table%4;
    const frame=pos*3;
    const tilt=.85+.33*variant+.22*frame;
    let sum=0,norm=0;
    for(let h=1;h<=24;h++){
      let weight=0;
      if(family===0)weight=1/Math.pow(h,tilt);
      else if(family===1)weight=(h%2?1:.01)/Math.pow(h,tilt);
      else if(family===2)weight=(h%3===1?1:.01)/Math.pow(h,tilt);
      else if(family===3)weight=(h%4===1?1:.01)/Math.pow(h,tilt);
      else if(family===4)weight=(.2+.8*Math.abs(Math.sin(h*(.55+.12*variant)+frame*.2)))/Math.pow(h,tilt);
      else if(family===5)weight=(Math.abs(h-(3+variant*2+frame*2))<=1?1:.005)/Math.pow(h,.35+.1*frame);
      else if(family===6)weight=([1,2+variant,5+Math.round(frame),9+variant*2].includes(h)?1:.005)/Math.pow(h,.4+.1*frame);
      else if(family===7)weight=(.02+.98*Math.abs(Math.cos(h*(1.2+.13*variant)+frame*.3)))/Math.pow(h,.55+.15*frame);
      else if(family===8)weight=([1,3+variant,8+Math.round(frame)*3,17+variant*4].includes(h)?1:.002)/Math.pow(h,.3);
      else if(family===9)weight=(h%2===0?1:.01)*Math.abs(Math.sin(h*(.3+.1*variant)+frame*.5))/Math.pow(h,.5+.1*frame);
      else if(family===10)weight=(h%(5+variant)===1?1:.005)/Math.pow(h,.3+.2*frame);
      else if(family===11)weight=([1,6+variant*2,13+Math.round(frame)*3,23+variant*3].includes(h)?1:.003)/Math.pow(h,.3+.15*frame);
      else if(family===12)weight=Math.exp(-Math.pow((h-(4+variant*3+frame*4))/(2+variant),2))+.02/h;
      else if(family===13)weight=.8*Math.exp(-Math.pow((h-(3+variant+frame*2))/2,2))+.7*Math.exp(-Math.pow((h-(14+variant*4-frame))/4,2))+.02/h;
      else if(family===14)weight=(Math.abs(h-(5+variant*2+frame*3))<3?.02:1)/Math.pow(h,.55+.12*variant);
      else if(family===15)weight=([1,4+variant,11+Math.round(frame)*2,22+variant*3].includes(h)?1:.002)/Math.pow(h,.18+.08*frame);
      else if(family===16)weight=(.1+.9*Math.abs(Math.sin(h*h*(.13+.02*variant)+frame*.7)))/Math.pow(h,.65+.1*frame);
      else if(family===17)weight=((h+Math.round(frame))%(3+variant)===0?1:.015)/Math.pow(h,.25+.16*frame);
      else if(family===18)weight=(.02+.98*Math.pow(Math.abs(Math.cos(h*(.24+.09*variant)+frame*.9)),4))/Math.pow(h,.5+.1*variant);
      else if(family===19)weight=([1,2,3+variant*2,20+Math.round(frame)*5].includes(h)?1:.003)/Math.pow(h,.3+.1*frame);
      else if(family===20)weight=Math.exp(-Math.pow((h-(9+variant*4-frame*2))/(3+frame),2))+.05/h;
      else if(family===21)weight=(h%(4+variant)===Math.round(frame)%(4+variant)?.02:1)/Math.pow(h,.7+.1*frame);
      else if(family===22)weight=(.1+.9*Math.abs(Math.sin(h*(1.9+.2*variant)+frame*.6)))/Math.pow(h,.2+.15*frame);
      else weight=([1,7+Math.round(frame)*3,16+variant*4,35-Math.round(frame)*4].includes(h)?1:.001)/Math.pow(h,.2+.1*variant);
      sum+=weight*Math.sin(h*phase*6.28318530718+.13*frame*h+.07*variant*h);
      norm+=weight;
    }
    const base=sum/Math.max(.6,norm*.55);
    const sh=(shape-50)/50;
    const dark=.5*(Math.sin(phase*6.28318530718)+Math.sin(phase*6.28318530718+.15));
    return Math.max(-1,Math.min(1,sh<0?base*(1+sh*.7)+dark*(-sh*.7):base*(1+sh*.35)));
  }
  function displayedWave(phase,wave,pos,bank,table,shape,legacyShape=50){
    const legacy=waveform(phase,wave,pos)+Math.sin(phase*6.28318530718)*((legacyShape-50)/50)*.32;
    return bank?expandedWave(phase,table,pos,shape):legacy;
  }
  function trace(ctx, x, y, w, h, wave, pos, drift, bank, table, shape, legacyShape) {
    let lastX=x,lastY=y+h/2;
    for(let i=0;i<w;i++){
      const v=displayedWave((i/w + drift) % 1,wave,pos,bank,table,shape,legacyShape);
      const py=y+Math.round(h/2-v*(h/2-2));
      if(i)ctx.line(lastX,lastY,x+i,py,1);
      lastX=x+i;lastY=py;
    }
  }
  // Detune visualization: a second trace separates in phase while notes sound.
  // Rate and direction follow the oscillator detune controls; no audio readback.
  function detuneGhost(ctx,x,y,w,h,wave,pos,drift,bank,table,shape,legacyShape,values,seconds){
    const d1=bounded(value(values,'osc1_detune',50),50,0,100)-50;
    const d2=bounded(value(values,'osc2_detune',50),50,0,100)-50;
    const mix=bounded(value(values,'osc2_volume',0),0,0,100)/100;
    const delta=(d2-d1)*.0005776;
    if(mix<.02||Math.abs(delta)<.00001)return;
    const slip=seconds*delta*1.8;
    const phaseOffset=slip-Math.floor(slip);
    for(let i=0;i<w;i+=3){
      const p=((i/w+drift+phaseOffset)%1+1)%1;
      const v=displayedWave(p,wave,pos,bank,table,shape,legacyShape);
      const py=y+Math.round(h/2-v*(h/2-2)*.72);
      ctx.fillRect(x+i,py,1,1,1);
    }
  }
  /* Four distinct page renderers. The host must register separate canvas
   * page entries for these to become physical jog-wheel stops. */
  function pageMeters(ctx,meters,H,W){
    const y=H-9,cell=Math.floor(W/meters.length);
    meters.forEach((m,i)=>{
      const x=i*cell,barW=Math.max(3,cell-11);
      ctx.print(x+1,y,m[0],1);
      ctx.fillRect(x+8,y+2,barW,3,0);
      ctx.fillRect(x+8,y+2,Math.round(barW*bounded(m[1],0,0,100)/100),3,1);
    });
  }
  function renderFace(ctx,o,which){
    const v=o&&o.values||{},W=ctx.width||128,H=ctx.height||40;
    if(W<32||H<18)return;
    const second=which==='osc2';
    const selected=bounded(value(v,second?'osc2_wavetable':'wavetable',1),1,0,99)|0;
    const pos=bounded(value(v,second?'osc2_position':'position',50),50,0,100)/100;
    const shape=bounded(value(v,'shape',50),50,0,100);
    const wave=Math.min(3,selected),bank=selected>=4?1:0,table=Math.max(0,selected-4);
    const voices=bounded(value(v,'voice_activity',0),0,0,8);
    const motion=bounded(value(v,'lfo_depth',0),0,0,100);
    const rate=bounded(value(v,'lfo_rate',22),22,0,100);
    const seconds=Number.isFinite(o&&o.nowMs)?o.nowMs/1000:frame/30;
    const drift=voices>0?motion*.0012*Math.sin(seconds*(.06+.12*rate)*6.28318530718):0;
    if(which==='filter'){
      const cutoff=bounded(value(v,'cutoff',78),78,0,100);
      const res=bounded(value(v,'resonance',15),15,0,100);
      const y0=2,h=Math.max(8,H-16);
      let lastY=0;
      for(let x=0;x<W-2;x++){
        const t=x/(W-2),center=.1+.8*cutoff/100;
        const slope=1/(1+Math.pow(Math.max(.001,t)/Math.max(.001,center),4));
        const peak=(res/100)*.4*Math.exp(-Math.pow((t-center)/.09,2));
        const y=y0+Math.round(h*(1-Math.min(1,slope+peak)));
        if(x)ctx.line(x,y0+lastY,x+1,y,1);
        lastY=y-y0;
      }
      pageMeters(ctx,[['C',cutoff],['R',res],['E',value(v,'filter_env_amt',0)],['L',value(v,'lfo_filter',0)]],H,W);
    }else{
      trace(ctx,1,2,W-3,Math.max(7,H-15),wave,Math.max(0,Math.min(1,pos+drift)),drift,bank,table,shape,shape);
      if(which==='main')pageMeters(ctx,[['C',value(v,'cutoff',78)],['M',motion],['E',value(v,'filter_env_amt',0)],['O',value(v,'osc2_volume',0)]],H,W);
      else pageMeters(ctx,[['W',value(v,second?'osc2_warp': 'osc1_warp',0)],['P',value(v,second?'osc2_pan':'osc1_pan',50)],['V',value(v,second?'osc2_volume':'osc1_volume',100)],['M',motion]],H,W);
    }
  }
  let frame = 0;
  globalThis.sprig_faces = {main:(ctx,o)=>renderFace(ctx,o,'main'),osc1:(ctx,o)=>renderFace(ctx,o,'osc1'),osc2:(ctx,o)=>renderFace(ctx,o,'osc2'),filter:(ctx,o)=>renderFace(ctx,o,'filter')};
  globalThis.canvas_overlay = {
    drawPage(ctx, o) {
      const v=o && o.values || {};
      const W=ctx.width||128,H=ctx.height||40;
      if(W<32||H<18)return;
      const selected=bounded(value(v,"wavetable",1),1,0,99)|0;
      const wave=Math.min(3,selected);
      const bank=selected>=4?1:0;
      const table=Math.max(0,selected-4);
      const shape=bounded(value(v,"shape",50),50,0,100);
      const legacyShape=shape;
      const pos=bounded(value(v,"position",50),50,0,100)/100;
      const cut=bounded(value(v,"cutoff",78),78,0,100);
      const motion=bounded(value(v,"lfo_depth",0),0,0,100);
      const env=bounded(value(v,"filter_env_amt",0),0,0,100);
      const mix=bounded(value(v,"osc2_level",0),0,0,100);
      const rate=bounded(value(v,"lfo_rate",22),22,0,100);
      /* Only sounding voices (including release tails) enable motion.
       * A missing activity read is treated as idle, never as always-on. */
      const voices=bounded(value(v,"voice_activity",0),0,0,8);
      const depth=voices>0?motion/100:0;
      /* Some Move hosts omit nowMs. Use redraw ticks as a fallback. */
      frame++;
      const now=o && o.nowMs;
      const seconds=(typeof now==="number" && Number.isFinite(now))?now/1000:frame/30;
      /* Motion depth shapes the visual only while a voice is sounding. */
      const hz=.06+.12*rate;
      const drift=depth*.12*Math.sin(seconds*hz*6.28318530718);
      const animatedPos=Math.max(0,Math.min(1,pos+depth*.12*Math.sin(seconds*hz*6.28318530718)));
      /* The host already draws the active encoder's label and value in its
       * own header. Duplicating that feedback inside drawPage creates two
       * overlapping rows on the actual Move display. Keep this page visual. */
      const waveY=1, waveH=Math.max(7,H-14);
      trace(ctx,1,waveY+1,W-3,waveH,wave,animatedPos,drift,bank,table,shape,legacyShape);
      if(voices>0)detuneGhost(ctx,1,waveY+1,W-3,waveH,wave,animatedPos,drift,bank,table,shape,legacyShape,v,seconds);
      /* A sparse second harmonic contour gives the technical trace an organic
       * shimmer. It exists only while voices sound and Motion is substantial.
       * The base waveform remains unchanged and idle stays perfectly still. */
      if(voices>0 && motion>=15){
        const x0=1, y0=waveY+1, width=W-3, height=waveH;
        const shimmer=depth*.16*Math.sin(seconds*hz*6.28318530718+1.57);
        const ghostPos=Math.max(0,Math.min(1,animatedPos+shimmer));
        for(let i=0;i<width;i+=4){
          const phase=(i/width+drift*.6+shimmer*.15)%1;
          const v0=displayedWave(phase<0?phase+1:phase,wave,ghostPos,bank,table,shape);
          const py=y0+Math.round(height/2-v0*(height/2-2)*.78);
          ctx.fillRect(x0+i,py,1,1,1);
        }
      }
      /* Tiny persistent signal meters keep the synth readable when idle. */
      const meters=[["C",cut],["M",motion],["E",env],["O",mix]];
      const y=H-9,cell=Math.floor(W/4);
      meters.forEach((m,i)=>{
        const x=i*cell;
        ctx.print(x+1,y,m[0],1);
        const barX=x+8,barW=Math.max(3,cell-11);
        ctx.fillRect(barX,y+2,barW,3,0);
        ctx.fillRect(barX,y+2,Math.round(barW*m[1]/100),3,1);
      });
    }
  };
})();
