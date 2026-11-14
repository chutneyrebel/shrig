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
      else weight=([1,6+variant*2,13+Math.round(frame)*3,23+variant*3].includes(h)?1:.003)/Math.pow(h,.3+.15*frame);
      sum+=weight*Math.sin(h*phase*6.28318530718+.13*frame*h+.07*variant*h);
      norm+=weight;
    }
    const base=sum/Math.max(.6,norm*.55);
    const sh=(shape-50)/50;
    const dark=.5*(Math.sin(phase*6.28318530718)+Math.sin(phase*6.28318530718+.15));
    return Math.max(-1,Math.min(1,sh<0?base*(1+sh*.7)+dark*(-sh*.7):base*(1+sh*.35)));
  }
  function displayedWave(phase,wave,pos,bank,table,shape){
    const legacy=waveform(phase,wave,pos);
    return bank?expandedWave(phase,table,pos,shape):legacy;
  }
  function trace(ctx, x, y, w, h, wave, pos, drift, bank, table, shape) {
    let lastX=x,lastY=y+h/2;
    for(let i=0;i<w;i++){
      const v=displayedWave((i/w + drift) % 1,wave,pos,bank,table,shape);
      const py=y+Math.round(h/2-v*(h/2-2));
      if(i)ctx.line(lastX,lastY,x+i,py,1);
      lastX=x+i;lastY=py;
    }
  }
  let frame = 0;
  globalThis.canvas_overlay = {
    drawPage(ctx, o) {
      const v=o && o.values || {};
      const W=ctx.width||128,H=ctx.height||40;
      if(W<32||H<18)return;
      const wave=bounded(value(v,"wave",1),1,0,3)|0;
      const bank=bounded(value(v,"wt_bank",0),0,0,1)|0;
      const table=bounded(value(v,"wt_table",0),0,0,47)|0;
      const shape=bounded(value(v,"spectral_shape",50),50,0,100);
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
      trace(ctx,1,waveY+1,W-3,waveH,wave,animatedPos,drift,bank,table,shape);
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
