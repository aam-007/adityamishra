(() => {
  const destination = new URL('../cheeky.html', document.currentScript.src);
  const controls = 'a,button,input,select,textarea,label,summary,details,dialog,[role="button"],[role="link"],[role="menuitem"],[tabindex],[contenteditable]:not([contenteditable="false"])';
  let count=0,started=0,last=0,mode='',timer=0,origin=null,gesture=null,navigating=false;
  try { sessionStorage.removeItem('portfolio-click-count'); } catch (_) { /* No storage needed. */ }
  const reset = () => { count=0;started=last=0;mode='';origin=null;clearTimeout(timer); };
  const blocked = event => {
    const target=event.composedPath()[0];
    return !(target instanceof Element) || target.closest(controls) || target.isContentEditable ||
      document.querySelector('dialog[open]') || !window.getSelection()?.isCollapsed;
  };
  function advance(kind,point=null) {
    if(navigating)return;
    const now=performance.now(),gap=kind==='touch'?1000:700,duration=kind==='touch'?5000:3000;
    if(!count||mode!==kind||now-last>gap||now-started>duration||
        (point&&origin&&Math.hypot(point.x-origin.x,point.y-origin.y)>80)){
      reset();mode=kind;started=now;origin=point;
    }
    count++;last=now;clearTimeout(timer);
    if(count<5){timer=setTimeout(reset,gap);return;}
    reset();navigating=true;location.assign(destination.href);
  }
  document.addEventListener('keydown',event=>{
    if(!event.isTrusted||event.isComposing||event.defaultPrevented||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey||blocked(event)){
      reset();return;
    }
    if(event.code!=='Space'){reset();return;}
    event.preventDefault();
    if(event.repeat)return;
    gesture=null;advance('keyboard');
  });
  // Mouse clicks cannot activate the surprise; controls also break any key sequence.
  document.addEventListener('click',()=>{if(mode==='keyboard')reset();},true);
  document.addEventListener('touchstart',event=>{
    const touchesControl=Array.from(event.touches).some(touch=>touch.target instanceof Element&&(touch.target.closest(controls)||touch.target.isContentEditable));
    if(!event.isTrusted||blocked(event)||touchesControl||event.touches.length>2){gesture=null;reset();return;}
    const now=performance.now();
    if(!gesture){gesture={started:now,points:new Map(),paired:false,valid:true,center:null};}
    if(now-gesture.started>180){gesture.valid=false;reset();}
    for(const touch of event.touches){
      if(!gesture.points.has(touch.identifier))gesture.points.set(touch.identifier,{x:touch.clientX,y:touch.clientY});
    }
    if(event.touches.length===2&&gesture.points.size===2){
      gesture.paired=true;
      const points=[...gesture.points.values()];
      gesture.center={x:(points[0].x+points[1].x)/2,y:(points[0].y+points[1].y)/2};
    }
    if(gesture.points.size>2){gesture.valid=false;reset();}
  },{passive:true});
  function checkMovement(touches){
    if(!gesture)return;
    for(const touch of touches){
      const point=gesture.points.get(touch.identifier);
      if(!point||Math.hypot(touch.clientX-point.x,touch.clientY-point.y)>10){gesture.valid=false;reset();}
    }
  }
  document.addEventListener('touchmove',event=>checkMovement(event.touches),{passive:true});
  document.addEventListener('touchend',event=>{
    if(!gesture)return;
    checkMovement(event.changedTouches);
    if(event.touches.length)return;
    const completed=gesture;gesture=null;
    if(event.isTrusted&&completed.valid&&completed.paired&&performance.now()-completed.started<=350){advance('touch',completed.center);}
    else reset();
  },{passive:true});
  const cancel=()=>{gesture=null;reset();};
  document.addEventListener('touchcancel',cancel,{passive:true});
  document.addEventListener('scroll',cancel,{capture:true,passive:true});
  document.addEventListener('visibilitychange',cancel);
  window.addEventListener('blur',cancel);
  window.addEventListener('pagehide',cancel);
  window.addEventListener('pageshow',()=>{navigating=false;cancel();});
  window.addEventListener('popstate',cancel);
})();
