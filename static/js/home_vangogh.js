/* vangogh.js — portada ERP. Sin librerías ni imágenes: todo se dibuja con canvas */
(function(){
"use strict";
document.body.classList.add("vg");
var $=function(i){return document.getElementById(i)};
var cielo=$("vg-cielo"),astros=$("vg-astros"),btn=$("vg-pausa");
if(!cielo||!astros)return;
var c=cielo.getContext&&cielo.getContext("2d"),a=astros.getContext&&astros.getContext("2d");
if(!c||!a){if(btn)btn.hidden=true;return;}

var ESC=.5,W,H,M,partes=[],t=0,pausado=false,ultimo=0,lentos=0,paisaje,luna,mr,VX,VY,Q,R=Math.random;
try{pausado=localStorage.getItem("vg-pausa")==="1";}catch(e){}

var estrellas=[{x:.46,y:.25,r:.07,s:1},{x:.72,y:.17,r:.055,s:-1},{x:.90,y:.44,r:.06,s:1},{x:.60,y:.48,r:.045,s:-1},{x:.22,y:.52,r:.04,s:1}];
var azules=["#0e2470","#162f85","#1d3d9c","#2447b0","#2f5cc4","#3a68d0","#4a78dc","#2b8ac0","#5f8ce0","#58b0d8","#7fa6e8","#9bbcf0","#b9d0f6","#cfe0fa"];
var amarillos=["#f6d54a","#f2c230","#ffe98a","#e8a81e","#ffd23c","#fff0a8","#d9a020","#f7c948","#ffb81f","#fbe38a"];

function campo(x,y){
  VX=Math.sin(y*.012+t*.4)*.35;VY=Math.cos(x*.01+t*.3)*.15;Q=0;
  for(var i=0;i<estrellas.length;i++){
    var e=estrellas[i],dx=x-e.x*W,dy=y-e.y*H,d=Math.sqrt(dx*dx+dy*dy)+1,r=e.r*M*3.2;
    var f=e.s*Math.exp(-d*d/(r*r))*2.6;
    VX+=-dy/d*f;VY+=dx/d*f;
    var q=Math.exp(-d*d/(r*r*.12));if(q>Q)Q=q;
  }
}
function nueva(){return{x:R()*W,y:R()*H,vida:40+R()*120,k:R()*30|0,g:2+R()*4,am:R()<.14};}

function pincel(){
  c.globalAlpha=.06;c.fillStyle="#0a1642";c.fillRect(0,0,W,H);
  c.globalAlpha=.85;c.lineCap="round";
  for(var i=0;i<partes.length;i++){
    var p=partes[i];campo(p.x,p.y);
    var nx=p.x+VX*2.4,ny=p.y+VY*2.4,l=Math.sqrt(VX*VX+VY*VY)+.01,ox=-VY/l*p.g*.45,oy=VX/l*p.g*.45;
    var pal=(Q>.3||p.am)?amarillos:azules,n=pal.length;
    c.lineWidth=p.g*.7;
    c.strokeStyle=pal[p.k%n];c.beginPath();c.moveTo(p.x+ox,p.y+oy);c.lineTo(nx+ox,ny+oy);c.stroke();
    c.strokeStyle=pal[(p.k+3)%n];c.beginPath();c.moveTo(p.x-ox,p.y-oy);c.lineTo(nx-ox,ny-oy);c.stroke();
    p.x=nx;p.y=ny;
    if(--p.vida<0||nx<0||ny<0||nx>W||ny>H)partes[i]=nueva();
  }
  c.globalAlpha=1;
}

function hacerPaisaje(){
  paisaje=document.createElement("canvas");paisaje.width=W;paisaje.height=H;
  var g=paisaje.getContext("2d"),i,j;g.lineCap="round";
  var cols=["#0d1d52","#0a1642","#07102f"];
  for(i=0;i<3;i++){
    var by=H*(.80+i*.045);g.fillStyle=cols[i];g.beginPath();g.moveTo(0,H);
    for(j=0;j<=24;j++)g.lineTo(W*j/24,by+Math.sin(j*.7+i*2)*H*.03);
    g.lineTo(W,H);g.fill();
    g.lineWidth=2;for(j=0;j<90;j++){var x=R()*W,y=by+R()*H*.12;
      g.strokeStyle="rgba(95,140,224,"+(.12+R()*.15)+")";g.beginPath();g.moveTo(x,y);g.lineTo(x+14+R()*16,y+(R()-.5)*5);g.stroke();}
  }
  g.fillStyle="#f6d54a";for(i=0;i<9;i++)g.fillRect(W*(.52+R()*.3),H*(.84+R()*.04),3,4);
  var cx=W*.045,ch=H*.66,cw=W*.055;
  g.beginPath();g.moveTo(cx-cw/2,H);
  g.bezierCurveTo(cx-cw*.9,H-ch*.4,cx-cw*.2,H-ch*.6,cx,H-ch);
  g.bezierCurveTo(cx+cw*.5,H-ch*.55,cx+cw*.9,H-ch*.3,cx+cw/2,H);g.closePath();
  g.fillStyle="#07140f";g.fill();g.save();g.clip();g.lineWidth=3;
  var vs=["#1d4a2e","#0e2a1c","#2a5a3a","#050d0a"];
  for(i=0;i<190;i++){var x2=cx+(R()-.5)*cw*1.6,y2=H-R()*ch;
    g.strokeStyle=vs[i%4];g.beginPath();g.moveTo(x2,y2);
    g.quadraticCurveTo(x2+(R()-.5)*8,y2-14,x2+(R()-.5)*10,y2-28);g.stroke();}
  g.restore();
}

function hacerLuna(){
  mr=M*.095;var s=Math.ceil(mr*2.4),cx=s/2,i;
  luna=document.createElement("canvas");luna.width=luna.height=s;
  var g=luna.getContext("2d");g.lineCap="round";
  g.fillStyle="#f8de6a";g.beginPath();g.arc(cx,cx,mr,0,6.283);g.fill();
  g.globalCompositeOperation="source-atop";
  for(i=0;i<110;i++){var an=R()*6.283,d=Math.sqrt(R())*mr,x=cx+Math.cos(an)*d,y=cx+Math.sin(an)*d,tg=an+1.57;
    g.strokeStyle=i%3?"#fff1a8":"#e6b020";g.lineWidth=2+R()*3;
    g.beginPath();g.moveTo(x,y);g.lineTo(x+Math.cos(tg)*(8+R()*8),y+Math.sin(tg)*(8+R()*8));g.stroke();}
  g.globalCompositeOperation="destination-out";
  g.beginPath();g.arc(cx-mr*.42,cx-mr*.08,mr*.88,0,6.283);g.fill();
}

function astrosYLuna(){
  a.clearRect(0,0,W,H);a.drawImage(paisaje,0,0);a.lineCap="round";
  var i,k,j;
  for(i=0;i<estrellas.length;i++){
    var e=estrellas[i],x=e.x*W,y=e.y*H,r=e.r*M,pul=1+.1*Math.sin(t*1.6+i*1.7);
    a.setLineDash([12,10]);a.lineDashOffset=-t*40*e.s;
    for(k=0;k<3;k++){
      a.beginPath();
      for(j=0;j<=30;j++){var u=j/30,rr=r*(.3+u*3.4),an=t*.7*e.s+k*2.094+u*5.2*e.s;
        var px=x+Math.cos(an)*rr,py=y+Math.sin(an)*rr;j?a.lineTo(px,py):a.moveTo(px,py);}
      a.strokeStyle="rgba(255,226,110,"+(.7-.15*(k%2))+")";a.lineWidth=3.4;a.stroke();
    }
    a.setLineDash([]);
    for(k=1;k<=3;k++){a.beginPath();a.arc(x,y,r*pul*(.75+k*.45),0,6.283);
      a.strokeStyle="rgba(246,213,74,"+(.6/k)+")";a.lineWidth=3;a.stroke();}
    var gr=a.createRadialGradient(x,y,0,x,y,r*pul);
    gr.addColorStop(0,"#fffde8");gr.addColorStop(.35,"#ffe45a");gr.addColorStop(.75,"#f2b820");gr.addColorStop(1,"rgba(242,184,32,0)");
    a.fillStyle=gr;a.beginPath();a.arc(x,y,r*pul,0,6.283);a.fill();
  }
  var mx=W*.91,my=H*.17,pl=1+.05*Math.sin(t*1.1);
  var gl=a.createRadialGradient(mx,my,mr*.6,mx,my,mr*3.2);
  gl.addColorStop(0,"rgba(255,200,60,.55)");gl.addColorStop(1,"rgba(255,160,30,0)");
  a.fillStyle=gl;a.beginPath();a.arc(mx,my,mr*3.2,0,6.283);a.fill();
  a.lineWidth=3.5;
  for(k=1;k<=5;k++){a.beginPath();a.arc(mx,my,mr*(1.15+k*.38)*pl,0,6.283);
    a.strokeStyle=(k%2?"rgba(255,170,40,":"rgba(255,235,120,")+(.75-k*.11)+")";a.setLineDash([16,9]);a.lineDashOffset=t*25*(k%2?1:-1);a.stroke();}
  a.setLineDash([]);a.drawImage(luna,mx-luna.width/2,my-luna.height/2);
}

var PAL={azul:["#0c2268","#1d3d9c","#3a68d0","#7fa6e8","#c8dcf8","#f6d54a"],
         oro:["#6b3f06","#b87a0e","#e0a81c","#f2c230","#ffe48a","#fff3c0"],
         tierra:["#4a190a","#8f3a17","#c4592a","#e68a45","#f7b66a","#ffe0a0"],
         verde:["#0b2a1c","#1b5a36","#3f8f4a","#8dbf5a","#d6e68a","#f6e27a"],
         violeta:["#1a1040","#3b2a8a","#6a4fc0","#9b86e0","#cdbff5","#f6d54a"],
         rosa:["#0b3a4a","#1c7a8a","#4fb0b8","#9fd8d4","#f4c6cf","#fff0e0"]};
var CFG={azul:[.38,.5,1.4],oro:[.5,.58,0],tierra:[.7,.35,1.2,.9],verde:[.3,.55,1.0,.5],violeta:[.62,.45,1.5],rosa:[.5,.4,.8,.7]};
var MAPA={productos:"azul",ventas:"oro",proveedores:"tierra",clientes:"verde",reportes:"violeta",tienda:"rosa",catalogo:"rosa"};
var ORDEN=["azul","oro","tierra","verde","violeta","rosa"];

function pintar(cv){
  var tipo=cv.getAttribute("data-pintura"),p=PAL[tipo],f=CFG[tipo],g=cv.getContext("2d"),w=cv.width=360,h=cv.height=200,i,s;
  g.fillStyle=p[0];g.fillRect(0,0,w,h);g.lineCap="round";
  for(i=0;i<1500;i++){
    var x=R()*w,y=R()*h,d=Math.sqrt((x-f[0]*w)*(x-f[0]*w)+(y-f[1]*h)*(y-f[1]*h));
    g.strokeStyle=p[5-Math.min(5,Math.floor(d/48+R()*2))];g.lineWidth=2+R()*4;g.globalAlpha=.88;
    g.beginPath();g.moveTo(x,y);
    for(s=0;s<6;s++){
      var an=Math.atan2(y-f[1]*h,x-f[0]*w)+f[2]+(f[3]?Math.sin(y*.05+x*.02)*f[3]:Math.sin(x*.03)*.4);
      x+=Math.cos(an)*5;y+=Math.sin(an)*5;g.lineTo(x,y);}
    g.stroke();
  }
}

function cubrir(cv){
  var cu=cv.parentNode.querySelector(".vg-cubierta");if(!cu)return;
  var g=cu.getContext("2d"),w=cu.width=360,h=cu.height=200,i,tipo=cv.getAttribute("data-pintura"),f=CFG[tipo],cx=f[0]*w,cy=f[1]*h;
  g.fillStyle="#e8dcbc";g.fillRect(0,0,w,h);g.lineCap="round";
  for(i=0;i<500;i++){g.strokeStyle=R()<.5?"rgba(255,250,225,.5)":"rgba(170,150,100,.18)";g.lineWidth=1+R()*3;
    var x=R()*w,y=R()*h;g.beginPath();g.moveTo(x,y);g.lineTo(x+10+R()*18,y+(R()-.5)*4);g.stroke();}
  g.strokeStyle="rgba(60,50,35,.35)";g.lineWidth=1.4;g.beginPath();
  if(tipo=="oro"){g.arc(cx,cy,26,0,6.283);for(i=0;i<16;i++){var an=i*.3927;
    g.moveTo(cx+Math.cos(an)*34,cy+Math.sin(an)*34);g.lineTo(cx+Math.cos(an)*(60+R()*30),cy+Math.sin(an)*(60+R()*30));}}
  else{for(i=0;i<=120;i++){var u=i/120,rr=4+u*80,a2=u*15,px=cx+Math.cos(a2)*rr,py=cy+Math.sin(a2)*rr;i?g.lineTo(px,py):g.moveTo(px,py);}}
  g.stroke();
  g.font="italic 15px Georgia,serif";g.fillStyle="rgba(90,72,40,.8)";g.textAlign="center";
  g.fillText("Pasa el cursor para pintar",w/2,h-14);
  var ult=null,hecho={},n=0,listo=false;
  function trazo(x,y){
    g.globalCompositeOperation="destination-out";
    var qx=ult?ult[0]:x,qy=ult?ult[1]:y,k;
    for(k=0;k<3;k++){g.lineWidth=14+R()*22;g.beginPath();g.moveTo(qx+(R()-.5)*8,qy+(R()-.5)*8);g.lineTo(x+(R()-.5)*8,y+(R()-.5)*8);g.stroke();}
    g.globalCompositeOperation="source-over";ult=[x,y];
    var key=(x/45|0)+","+(y/40|0);
    if(!hecho[key]){hecho[key]=1;if(++n>=28&&!listo){listo=true;cu.classList.add("listo");}}
  }
  function auto(){
    if(listo)return;var s=0;ult=null;
    (function paso(){
      if(listo||s>=100){if(!listo){listo=true;cu.classList.add("listo");}return;}
      for(var k=0;k<2;k++){var u=s/100*5,row=Math.min(4,u|0),pr=u-row;
        trazo((row%2?1-pr:pr)*w,20+row*40+Math.sin(pr*18)*8);s++;}
      requestAnimationFrame(paso);
    })();
  }
  cu.addEventListener("pointermove",function(e){
    var r=cu.getBoundingClientRect();trazo((e.clientX-r.left)*w/r.width,(e.clientY-r.top)*h/r.height);});
  cu.addEventListener("pointerleave",function(){ult=null;});
  cu.addEventListener("pointerdown",function(e){if(e.pointerType==="touch")auto();});
  var enlace=cu.closest?cu.closest("a"):null;if(enlace)enlace.addEventListener("focus",auto);
}

function barra(){
  var caja=document.querySelector(".erp-nav-links");if(!caja)return;
  var links=caja.querySelectorAll("a.erp-nav-link"),luz=document.createElement("span");
  var COLOR={productos:"#6f9be6",clientes:"#f2c230",proveedores:"#e68a45",ventas:"#f6d54a",reportes:"#9bbcf0",catalogo:"#ffe48a",admin:"#cfe0fa",accounts:"#e8a81e"};
  luz.className="vg-luz";caja.appendChild(luz);
  var L=0,Rr=0,vL=0,vR=0,tL=0,tR=0,kL=.14,kR=.14,corre=false,ini=false;
  function paso(){
    vL=(vL+(tL-L)*kL)*.72;L+=vL;vR=(vR+(tR-Rr)*kR)*.72;Rr+=vR;
    luz.style.transform="translateX("+L+"px)";luz.style.width=Math.max(20,Rr-L)+"px";
    if(Math.abs(vL)+Math.abs(vR)+Math.abs(tL-L)+Math.abs(tR-Rr)>.4)requestAnimationFrame(paso);else corre=false;
  }
  function ir(a){
    var n=caja.getBoundingClientRect(),r=a.getBoundingClientRect(),seg=(a.getAttribute("href")||"").split("/")[1];
    luz.style.setProperty("--luz",COLOR[seg]||"#f2c230");
    luz.style.top=(r.top-n.top-2)+"px";luz.style.height=(r.height+4)+"px";
    tL=r.left-n.left-4;tR=r.right-n.left+4;
    if(!ini){L=tL;Rr=tR;ini=true;}
    var dir=(tL+tR)>(L+Rr)?1:-1;
    kR=dir>0?.24:.1;kL=dir>0?.1:.24;
    luz.classList.add("on");
    if(!corre){corre=true;requestAnimationFrame(paso);}
  }
  function apagar(){luz.classList.remove("on");}
  Array.prototype.forEach.call(links,function(l){
    l.addEventListener("pointerenter",function(){ir(l);});
    l.addEventListener("focus",function(){ir(l);});
    l.addEventListener("blur",apagar);
  });
  caja.addEventListener("pointerleave",apagar);
}

function grano(){
  var g=document.createElement("canvas");g.width=g.height=140;var x=g.getContext("2d"),im=x.createImageData(140,140),i;
  for(i=0;i<im.data.length;i+=4){im.data[i]=im.data[i+1]=im.data[i+2]=R()*255|0;im.data[i+3]=70;}
  x.putImageData(im,0,0);x.fillStyle="rgba(255,255,255,.07)";
  for(i=0;i<140;i+=3){x.fillRect(0,i,140,1);x.fillRect(i,0,1,140);}
  document.documentElement.style.setProperty("--grano","url("+g.toDataURL()+")");
}

function tam(){
  W=cielo.width=astros.width=Math.ceil(innerWidth*ESC);H=cielo.height=astros.height=Math.ceil(innerHeight*ESC);M=Math.min(W,H);
  var n=Math.min(760,Math.round(W*H/900)),i;partes=[];for(i=0;i<n;i++)partes.push(nueva());
  c.fillStyle="#0a1642";c.fillRect(0,0,W,H);hacerPaisaje();hacerLuna();
  for(i=0;i<110;i++){t+=.02;pincel();}
  astrosYLuna();
}
function cuadro(ts){
  requestAnimationFrame(cuadro);
  if(pausado||document.hidden||ts-ultimo<33)return;
  if(ts-ultimo>80){if(++lentos>20&&partes.length>120){partes.length=Math.round(partes.length*.6);lentos=0;}}else lentos=0;
  ultimo=ts;t+=.02;pincel();astrosYLuna();
}
function etiqueta(){if(!btn)return;btn.textContent=pausado?"Reanudar animación":"Pausar animación";btn.setAttribute("aria-pressed",pausado);}
if(btn)btn.addEventListener("click",function(){pausado=!pausado;etiqueta();try{localStorage.setItem("vg-pausa",pausado?"1":"0");}catch(e){}});
var rt;addEventListener("resize",function(){clearTimeout(rt);rt=setTimeout(tam,250);});

grano();
Array.prototype.forEach.call(document.querySelectorAll(".vg-pintura"),function(cv,i){
  cv.setAttribute("data-pintura",MAPA[cv.getAttribute("data-clave")]||ORDEN[i%ORDEN.length]);
  pintar(cv);cubrir(cv);
});
barra();tam();etiqueta();requestAnimationFrame(cuadro);
})();