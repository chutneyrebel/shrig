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
  function trace(ctx, x, y, w, h, wave, pos, drift) {
    let lastX=x,lastY=y+h/2;
    for(let i=0;i<w;i++){
      const v=waveform((i/w + drift) % 1,wave,pos);
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
      trace(ctx,1,waveY+1,W-3,waveH,wave,animatedPos,drift);
      /* A sparse second harmonic contour gives the technical trace an organic
       * shimmer. It exists only while voices sound and Motion is substantial.
       * The base waveform remains unchanged and idle stays perfectly still. */
      if(voices>0 && motion>=15){
        const x0=1, y0=waveY+1, width=W-3, height=waveH;
        const shimmer=depth*.16*Math.sin(seconds*hz*6.28318530718+1.57);
        const ghostPos=Math.max(0,Math.min(1,animatedPos+shimmer));
        for(let i=0;i<width;i+=4){
          const phase=(i/width+drift*.6+shimmer*.15)%1;
          const v0=waveform(phase<0?phase+1:phase,wave,ghostPos);
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
