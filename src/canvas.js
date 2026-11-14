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
      /* Schwung v1.9 passes the active encoder slot as touched and its
       * eight knob keys in o.keys. Preserve the large wave while exposing
       * the currently adjusted parameter directly in the body band. */
      const keys=o && Array.isArray(o.keys)?o.keys:[];
      const touched=o && Number.isInteger(o.touched)?o.touched:-1;
      const active=touched>=0&&touched<keys.length?keys[touched]:null;
      const names={
        wave:"WT TYPE",position:"WT POS",osc2_level:"OSC2 MIX",
        detune:"DETUNE",cutoff:"CUTOFF",resonance:"RESO",
        lfo_depth:"MOTION",level:"LEVEL"
      };
      const label=active&&names[active]||"SPRIG WT";
      const raw=active?value(v,active,0):0;
      const display=active==="wave"?["SINE","SAW","SQUARE","TRIANGLE"][Math.max(0,Math.min(3,raw|0))]
        :active?String(Math.round(bounded(raw,0,0,100))):"";
      /* Header is always present. No dropdown or modal is drawn by Sprig. */
      ctx.print(1,0,label,1);
      if(display){
        const dx=Math.max(55,W-(display.length*6)-2);
        ctx.print(dx,0,display,1);
      }else{
        ctx.print(Math.max(70,W-31),0,["SIN","SAW","SQR","TRI"][wave],1);
      }
      const waveY=10, waveH=Math.max(7,H-23);
      ctx.fillRect(0,waveY-1,W,1,1);
      trace(ctx,1,waveY+1,W-3,waveH,wave,animatedPos,drift);
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
