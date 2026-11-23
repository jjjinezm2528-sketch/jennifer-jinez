(function(){
'use strict';
var D=document,R=D.documentElement,M=Math,
    art=D.getElementById('nt-art'),cv=D.getElementById('nt-cv'),moon=D.querySelector('.nt-moon');
if(!art||!cv)return;

var K=.5,                       // el canvas trabaja a media resolución (más ligero)
    x=cv.getContext('2d'),W=0,H=0,P=[],S=[],sh=null,shT=240,
    mx=0,my=0,tx=0,ty=0,sy=0,lsy=-1,CX=0,CY=0,CR=1,paused=false,
    mq=matchMedia('(prefers-reduced-motion:reduce)'),
    COL=['#9fc3ee','#f4dd7a','#fff3b0','#3a73c4','#cfe3ff'],
    N=innerWidth<700?80:170;

function pt(p){p=p||{};p.x=M.random()*W;p.y=M.random()*H;p.c=COL[M.random()*COL.length|0];p.w=1.4+M.random()*3;p.l=0;return p}
function rs(){
  W=cv.width=M.ceil(innerWidth*K);H=cv.height=M.ceil(innerHeight*K);
  // centro del remolino en pantalla (calculado sin leer el DOM en cada cuadro)
  var w=M.max(innerWidth,innerHeight*.6667),h=w*1.5;
  CX=(innerWidth-w)/2+w*.68;CY=(innerHeight-h)*.22+h*.27;CR=w*.3;
}
rs();addEventListener('resize',rs);
for(var i=0;i<N;i++)P.push(pt());

// campo de flujo: ondas suaves + giro alrededor del remolino
function ang(px,py){
  var X=px/K,Y=py/K,dx=X-CX,dy=Y-CY,d=M.hypot(dx,dy),w=M.exp(-d*d/(CR*CR*2)),
      b=M.sin(X/170+Y/240)*.5+M.sin(Y/110)*.25,s=M.atan2(dy,dx)+1.87;
  return M.atan2(M.sin(b)*(1-w)+M.sin(s)*w,M.cos(b)*(1-w)+M.cos(s)*w);
}

// estrellas y remolinos alineados con la pintura (coordenadas 736x1104)
function bx(cx,cy,r){return 'left:'+(cx-r)/7.36+'%;top:'+(cy-r)/11.04+'%;width:'+2*r/7.36+'%;aspect-ratio:1;'}
[[155,95,62],[285,268,48],[322,510,115],[2,450,55]].forEach(function(s,k){
  var a=D.createElement('div');a.className='nt-st';
  a.style.cssText=bx(s[0],s[1],s[2])+'animation-delay:-'+k*.9+'s;animation-duration:'+(3+k*.7)+'s';art.appendChild(a);
  var g=D.createElement('div');g.className='nt-rg';
  g.style.cssText=bx(s[0],s[1],s[2]*1.15)+'animation-duration:'+(18+k*7)+'s;animation-direction:'+(k%2?'reverse':'normal');art.appendChild(g);
});
function vx(cx,cy,r,dur,dir){
  var o=D.createElement('div');o.className='nt-vx nt-pic';
  o.style.cssText=bx(cx,cy,r)+'background-size:'+736/(2*r)*100+'% auto;background-position:'+(cx-r)/(736-2*r)*100+'% '+(cy-r)/(1104-2*r)*100+'%;animation-duration:'+dur+'s;animation-direction:'+dir;
  art.appendChild(o);
}
vx(505,300,210,80,'normal');vx(505,300,115,45,'reverse');

// mouse y scroll
addEventListener('pointermove',function(e){
  tx=e.clientX/innerWidth-.5;ty=e.clientY/innerHeight-.5;
  if(e.pointerType==='mouse'&&!paused&&!mq.matches&&S.length<120)
    for(var k=0;k<2;k++)S.push({x:e.clientX*K,y:e.clientY*K,vx:(M.random()-.5)*.9,vy:(M.random()-.5)*.9+.15,l:0});
},{passive:true});
addEventListener('scroll',function(){sy=scrollY},{passive:true});

function frame(){
  requestAnimationFrame(frame);
  var reduce=mq.matches;

  // parallax suave (se escribe directo en el elemento, sin recalcular toda la página)
  if(!reduce){
    var dx=tx-mx,dy=ty-my;
    if(M.abs(dx)>.0004||M.abs(dy)>.0004||sy!==lsy){
      mx+=dx*.06;my+=dy*.06;lsy=sy;
      art.style.transform='translate3d('+(-mx*22).toFixed(2)+'px,'+(-my*14-sy*.05).toFixed(2)+'px,0) scale(1.06)';
      if(moon)moon.style.transform='translate3d('+(mx*34).toFixed(2)+'px,'+(my*22).toFixed(2)+'px,0)';
    }
  }
  if(paused||reduce)return;

  // desvanece el cuadro anterior y dibuja las pinceladas
  x.globalCompositeOperation='destination-out';x.fillStyle='rgba(0,0,0,.06)';x.fillRect(0,0,W,H);
  x.globalCompositeOperation='source-over';x.lineCap='round';x.globalAlpha=.3;
  for(var i=0;i<P.length;i++){
    var p=P[i],a=ang(p.x,p.y),nx=p.x+M.cos(a)*1.1,ny=p.y+M.sin(a)*1.1;
    x.strokeStyle=p.c;x.lineWidth=p.w;x.beginPath();x.moveTo(p.x,p.y);x.lineTo(nx,ny);x.stroke();
    p.x=nx;p.y=ny;
    if(++p.l>260||nx<0||ny<0||nx>W||ny>H)pt(p);
  }

  // estrella fugaz ocasional
  if(!sh&&--shT<0){var q=.5+M.random()*.3;sh={x:M.random()*W*.7,y:M.random()*H*.3,vx:M.cos(q)*5,vy:M.sin(q)*5,l:0};shT=500+M.random()*700}
  if(sh){
    x.globalAlpha=.9;x.strokeStyle='#fff6c8';x.lineWidth=1.6;x.beginPath();x.moveTo(sh.x,sh.y);
    sh.x+=sh.vx;sh.y+=sh.vy;x.lineTo(sh.x,sh.y);x.stroke();
    if(++sh.l>60)sh=null;
  }

  // polvo de estrellas del cursor
  for(var j=S.length-1;j>=0;j--){
    var s=S[j];s.x+=s.vx;s.y+=s.vy;
    if(++s.l>40){S.splice(j,1);continue}
    x.globalAlpha=1-s.l/40;x.fillStyle='#ffe27a';x.beginPath();x.arc(s.x,s.y,1.2,0,6.3);x.fill();
    x.globalAlpha*=.3;x.beginPath();x.arc(s.x,s.y,3,0,6.3);x.fill();
  }
  x.globalAlpha=1;
}
frame();

// inclinación 3D + destello en tarjetas (solo con mouse)
D.querySelectorAll('.nt-card').forEach(function(c){
  var f=c.querySelector('.nt-fr');if(!f)return;
  c.addEventListener('pointermove',function(e){
    if(e.pointerType!=='mouse'||mq.matches)return;
    var r=c.getBoundingClientRect(),u=(e.clientX-r.left)/r.width-.5,v=(e.clientY-r.top)/r.height-.5;
    f.style.transform='perspective(900px) rotateY('+u*12+'deg) rotateX('+(-v*12)+'deg) translateY(-6px)';
    f.style.setProperty('--gx',(u+.5)*100+'%');f.style.setProperty('--gy',(v+.5)*100+'%');
  });
  c.addEventListener('pointerleave',function(){f.style.transform=''});
});

// botón pausa
var pb=D.getElementById('nt-pause');
if(pb)pb.addEventListener('click',function(){
  paused=!paused;R.classList.toggle('nt-paused',paused);pb.setAttribute('aria-pressed',paused);
});
})();