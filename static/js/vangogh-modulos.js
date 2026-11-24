/* vangogh-modulos.js — activa el diseño Van Gogh en las páginas de módulos.
   Sin librerías. No hace nada en la portada (esa tiene su propio vangogh.js). */
(function(){
"use strict";
if(document.getElementById("vg-cielo"))return;

var b=document.body,h=document.documentElement,R=Math.random;
var MOD={productos:"productos",clientes:"clientes",proveedores:"proveedores",compras:"proveedores",
         ventas:"ventas",pedidos:"ventas",reportes:"reportes",tienda:"tienda",catalogo:"tienda",carrito:"tienda"};
var seg=(location.pathname.split("/")[1]||"").toLowerCase();

/* Módulo actual: se puede forzar desde la plantilla con {% block body_class %}vgm-ventas{% endblock %} */
b.classList.add("vgm");
var yaTiene=Array.prototype.some.call(b.classList,function(c){return c.indexOf("vgm-")===0;});
if(!yaTiene)b.classList.add("vgm-"+(MOD[seg]||"productos"));

/* Grano de lienzo (mismo que la portada) */
(function(){
  var g=document.createElement("canvas");g.width=g.height=140;
  var x=g.getContext("2d"),im=x.createImageData(140,140),i;
  for(i=0;i<im.data.length;i+=4){im.data[i]=im.data[i+1]=im.data[i+2]=R()*255|0;im.data[i+3]=70;}
  x.putImageData(im,0,0);x.fillStyle="rgba(255,255,255,.07)";
  for(i=0;i<140;i+=3){x.fillRect(0,i,140,1);x.fillRect(i,0,1,140);}
  h.style.setProperty("--grano","url("+g.toDataURL()+")");
})();

/* Tema claro/oscuro: sigue lo que haga el botón de tema de base.html.
   Se ignoran las clases propias (vg...) para no detectarse a sí mismo. */
var claro=null;
function esClaro(){
  var v=[h.getAttribute("data-theme"),h.getAttribute("data-bs-theme"),
         b.getAttribute("data-theme"),b.getAttribute("data-bs-theme")].join(" ").toLowerCase();
  if(/light|claro/.test(v))return true;
  if(/dark|oscuro/.test(v))return false;
  var cl=(h.className+" "+b.className).toLowerCase().split(/\s+/)
    .filter(function(x){return x.indexOf("vg")!==0;}).join(" ");
  if(/(^|[\s-])(dark|oscuro)($|\s)/.test(cl))return false;
  return /(^|[\s-])(light|claro)($|\s)/.test(cl);
}
function aplicarTema(){
  var cl=esClaro();if(cl===claro)return;
  claro=cl;b.classList.toggle("vgm-claro",cl);
}
var mo=new MutationObserver(aplicarTema),op={attributes:true,attributeFilter:["data-theme","data-bs-theme","class"]};
mo.observe(h,op);mo.observe(b,op);
document.addEventListener("click",function(e){
  if(e.target.closest&&e.target.closest(".theme-toggle"))setTimeout(aplicarTema,80);
});
aplicarTema();

/* Luz deslizante de la barra: descansa sobre el módulo actual y viaja al pasar por otros */
function barra(){
  var caja=document.querySelector(".erp-nav-links");if(!caja)return;
  var links=caja.querySelectorAll("a.erp-nav-link"),luz=document.createElement("span"),reposo=null;
  var COLOR={productos:"#6f9be6",clientes:"#f2c230",proveedores:"#e68a45",ventas:"#f6d54a",
             reportes:"#9bbcf0",catalogo:"#ffe48a",tienda:"#9fd8d4",admin:"#cfe0fa",accounts:"#e8a81e"};
  luz.className="vgm-luz";caja.appendChild(luz);
  var L=0,Rr=0,vL=0,vR=0,tL=0,tR=0,kL=.14,kR=.14,corre=false,ini=false;
  function paso(){
    vL=(vL+(tL-L)*kL)*.72;L+=vL;vR=(vR+(tR-Rr)*kR)*.72;Rr+=vR;
    luz.style.transform="translateX("+L+"px)";luz.style.width=Math.max(20,Rr-L)+"px";
    if(Math.abs(vL)+Math.abs(vR)+Math.abs(tL-L)+Math.abs(tR-Rr)>.4)requestAnimationFrame(paso);else corre=false;
  }
  function ir(a){
    var n=caja.getBoundingClientRect(),r=a.getBoundingClientRect(),s=(a.getAttribute("href")||"").split("/")[1];
    luz.style.setProperty("--luz",COLOR[s]||"#f2c230");
    luz.style.top=(r.top-n.top-2)+"px";luz.style.height=(r.height+4)+"px";
    tL=r.left-n.left-4;tR=r.right-n.left+4;
    if(!ini){L=tL;Rr=tR;ini=true;}
    var dir=(tL+tR)>(L+Rr)?1:-1;
    kR=dir>0?.24:.1;kL=dir>0?.1:.24;
    luz.classList.add("on");
    if(!corre){corre=true;requestAnimationFrame(paso);}
  }
  Array.prototype.forEach.call(links,function(l){
    var s=(l.getAttribute("href")||"").split("/")[1];
    if(s&&s.toLowerCase()===seg)reposo=l;
  });
  if(!reposo)reposo=caja.querySelector("a.erp-nav-link.active");
  function volver(){if(reposo)ir(reposo);else luz.classList.remove("on");}
  Array.prototype.forEach.call(links,function(l){
    l.addEventListener("pointerenter",function(){ir(l);});
    l.addEventListener("focus",function(){ir(l);});
    l.addEventListener("blur",volver);
  });
  caja.addEventListener("pointerleave",volver);
  addEventListener("resize",function(){ini=false;volver();});
  addEventListener("load",function(){ini=false;volver();});
  volver();
}
barra();
})();

/* ===== ANIMACIONES ===== */
(function(){
"use strict";
if(document.getElementById("vg-cielo"))return;   /* no actúa en la portada */

var b=document.body,h=document.documentElement,R=Math.random;

/* 1. Fondo: estrellas titilantes con parallax */
var sy=0,ticking=false;
function onScroll(){
  sy=window.pageYOffset||h.scrollTop||0;
  if(ticking)return;ticking=true;
  requestAnimationFrame(function(){h.style.setProperty("--vgm-par",sy);ticking=false;});
}
addEventListener("scroll",onScroll,{passive:true});onScroll();

var cv=document.createElement("canvas");cv.className="vgm-estrellas";
b.insertBefore(cv,b.firstChild);
var cx=cv.getContext("2d"),W=0,H=0,dpr=Math.min(window.devicePixelRatio||1,2),P=[],last=0;
function medir(){
  W=innerWidth;H=innerHeight;cv.width=W*dpr;cv.height=H*dpr;cx.setTransform(dpr,0,0,dpr,0,0);
  var n=Math.max(28,Math.min(80,Math.round(W*H/22000)));P=[];
  for(var i=0;i<n;i++)P.push({x:R()*W,y:R()*H,r:.8+R()*2.2,v:4+R()*10,ph:R()*6.28,s:.6+R()*1.6,z:.3+R()*.7,dx:(R()-.5)*6});
}
function cuadro(t){
  requestAnimationFrame(cuadro);
  if(document.hidden)return;
  var dt=Math.min(.05,(t-last)/1000||0);last=t;
  var claro=b.classList.contains("vgm-claro"),rgb=claro?"255,150,30":"246,213,74";
  cx.clearRect(0,0,W,H);
  for(var i=0;i<P.length;i++){
    var p=P[i];
    p.y-=p.v*dt;p.x+=p.dx*dt;
    if(p.y<-10)p.y=H+10;if(p.x<-10)p.x=W+10;if(p.x>W+10)p.x=-10;
    var yy=(((p.y-sy*p.z*.6)%H)+H)%H;
    var a=.25+.5*(Math.sin(t*.001*p.s+p.ph)+1)/2;
    cx.fillStyle="rgba("+rgb+","+(a*.22)+")";cx.beginPath();cx.arc(p.x,yy,p.r*3.2,0,6.283);cx.fill();
    cx.fillStyle="rgba("+rgb+","+a+")";cx.beginPath();cx.arc(p.x,yy,p.r,0,6.283);cx.fill();
  }
}
medir();addEventListener("resize",medir);requestAnimationFrame(cuadro);

/* 2. Entrada tipo notificación al bajar */
var SEL_REVELA=".erp-main tbody tr,.erp-main .card,.erp-main .list-group-item,.erp-main .alert";
var SEL_ELIGE=".erp-main tbody tr,.erp-main .card,.erp-main .list-group-item";
var io=null;
if("IntersectionObserver" in window){
  io=new IntersectionObserver(function(es){
    var n=0;
    es.forEach(function(e){
      if(!e.isIntersecting)return;
      var el=e.target;io.unobserve(el);
      el.style.setProperty("--vgm-d",(n++*70)+"ms");
      el.classList.remove("vgm-pre");el.classList.add("vgm-in");
    });
  },{threshold:.08,rootMargin:"0px 0px -4% 0px"});
}
function revisar(raiz){
  if(!raiz||raiz.nodeType!==1)return;
  var lista=[];
  if(raiz.matches&&raiz.matches(SEL_REVELA))lista.push(raiz);
  Array.prototype.push.apply(lista,raiz.querySelectorAll(SEL_REVELA));
  lista.forEach(function(el){
    if(el.classList.contains("vgm-visto"))return;
    el.classList.add("vgm-visto");
    if(el.matches(SEL_ELIGE))el.classList.add("vgm-item");
    if(io){el.classList.add("vgm-pre");io.observe(el);}
  });
}
function iniciar(){
  var main=document.querySelector(".erp-main")||b;
  revisar(main);
  new MutationObserver(function(ms){
    ms.forEach(function(m){Array.prototype.forEach.call(m.addedNodes,revisar);});
  }).observe(main,{childList:true,subtree:true});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",iniciar);else iniciar();

/* 3. Elegir: la opción se centra y las demás bajan un poco */
function grupo(el){return el.parentNode.closest("tbody,.list-group,.row")||el.parentNode;}
function hermanos(g){
  return Array.prototype.filter.call(g.querySelectorAll(".vgm-item"),function(x){return grupo(x)===g;});
}
function limpiar(g){
  Array.prototype.forEach.call((g||document).querySelectorAll(".vgm-sel,.vgm-baja"),function(x){
    x.classList.remove("vgm-sel","vgm-baja");
  });
}
document.addEventListener("click",function(e){
  var t=e.target;if(!t.closest)return;
  if(t.closest("a,button,input,select,textarea,label,.btn,.dropdown-menu,.modal,.page-link"))return;
  var it=t.closest(".vgm-item");
  if(!it){limpiar();return;}
  var g=grupo(it),lista=hermanos(g);
  if(lista.length<2)return;
  if(it.classList.contains("vgm-sel")){limpiar(g);return;}
  limpiar(g);
  lista.forEach(function(x){if(x!==it)x.classList.add("vgm-baja");});
  it.classList.add("vgm-sel");
  it.scrollIntoView({behavior:"smooth",block:"center"});
});
document.addEventListener("keydown",function(e){if(e.key==="Escape")limpiar();});
})();