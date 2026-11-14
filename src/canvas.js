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
  function trace(ctx, x, y, w, h, wave, pos) {
    let lastX=x,lastY=y+h/2;
    for(let i=0;i<w;i++){
      const v=waveform(i/w,wave,pos);
      const py=y+Math.round(h/2-v*(h/2-2));
      if(i)ctx.line(lastX,lastY,x+i,py,1);
      lastX=x+i;lastY=py;
    }
  }
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
      /* Left: active waveform, driven by the actual displayed parameter values. */
      ctx.print(1,0,["SIN","SAW","SQR","TRI"][wave],1);
      const leftW=Math.floor(W*.58);
      ctx.fillRect(0,10,leftW,1,1);
      trace(ctx,1,13,leftW-3,Math.max(7,H-18),wave,pos);
      /* Right: compact synthesis signal path and depth meters. */
      const rightX=leftW+4,barX=rightX+20,barW=Math.max(3,W-barX-3);
      const rows=[["CUT",cut],["MOD",motion],["ENV",env],["OSC",mix]];
      rows.forEach((r,i)=>{
        const y=1+i*9;if(y+6>=H)return;
        ctx.print(rightX,y,r[0],1);
        ctx.fillRect(barX,y+2,barW,3,0);
        ctx.fillRect(barX,y+2,Math.round(barW*r[1]/100),3,1);
      });
    }
  };
})();
