/** Scroll is illustrative; it never advances an investigation or recovery. */
export function storyProgress(top:number,height:number,viewport:number,hero=false){
  const travel=hero?-top:viewport*.65-top;
  const span=hero?height*.8:height-viewport*.2;
  return Math.min(1,Math.max(0,travel/Math.max(1,span)));
}
