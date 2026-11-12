/* ============ Pintura al óleo generada con pinceladas ahusadas ============ */
(function () {
  var skySvg = document.getElementById('sky'), fgSvg = document.getElementById('fg');
  if (!skySvg || !fgSvg) return;

  var NS = 'http://www.w3.org/2000/svg', seed = 11;
  function rnd() { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
  function R(a, b) { return a + (b - a) * rnd(); }
  function f(n) { return Math.round(n * 10) / 10; }
  function el(tag, at, par) { var e = document.createElementNS(NS, tag); for (var k in at) e.setAttribute(k, at[k]); if (par) par.appendChild(e); return e; }
  function grp(par) { return el('g', { fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, par); }

  /* Pincelada: polígono ahusado (fino en las puntas, ancho al centro) + vetas de cerdas */
  function brush(g, p0, p1, p2, w, cls) {
    var N = 9, pts = [], i, t, x, y, dx, dy, n, hw;
    for (i = 0; i <= N; i++) {
      t = i / N;
      x = (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0];
      y = (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1];
      dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]);
      dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]);
      n = Math.hypot(dx, dy) || 1;
      hw = w / 2 * Math.pow(Math.sin(Math.PI * (.07 + .86 * t)), .55);
      pts.push({ x: x, y: y, nx: -dy / n, ny: dx / n, hw: hw });
    }
    function P(u) { return pts.map(function (p) { return f(p.x + p.nx * p.hw * u) + ' ' + f(p.y + p.ny * p.hw * u); }); }
    el('path', { d: 'M' + P(-1).join('L') + 'L' + P(1).reverse().join('L') + 'Z', 'class': cls, opacity: f(R(.8, 1)) }, g);
    if (w > 7) for (var k = 0; k < 3; k++) {
      if (rnd() < .65) el('path', { d: 'M' + P(R(-.7, .7)).join('L'), 'class': rnd() < .5 ? 'bs' : 'bd' }, g);
    }
  }

  /* Campo de flujo: ondas suaves + remolinos */
  var SW = [{ x: 840, y: 300, r: 170, d: 1 }, { x: 430, y: 240, r: 100, d: -1 }, { x: 1200, y: 320, r: 90, d: 1 }];
  function ang(x, y) {
    var a = Math.sin(x * .006 + y * .009) * .55 + Math.sin(y * .02) * .12, vx = Math.cos(a), vy = Math.sin(a);
    for (var i = 0; i < SW.length; i++) {
      var s = SW[i], dx = x - s.x, dy = y - s.y, d = Math.hypot(dx, dy) || 1, w = 3 * Math.exp(-d * d / (s.r * s.r * 2.2));
      vx += -dy / d * s.d * w; vy += dx / d * s.d * w;
    }
    return Math.atan2(vy, vx);
  }
  function flow(g, x, y, L, w, cls) {
    var a = ang(x, y), p1 = [x + Math.cos(a) * L / 2, y + Math.sin(a) * L / 2], a2 = ang(p1[0], p1[1]);
    brush(g, [x, y], p1, [p1[0] + Math.cos(a2) * L / 2, p1[1] + Math.sin(a2) * L / 2], w, cls);
  }
  function skyCls(x, y) {
    var n = 1e9, c = rnd(), i;
    for (i = 0; i < SW.length; i++) n = Math.min(n, Math.hypot(x - SW[i].x, y - SW[i].y) / SW[i].r);
    if (n < 1.15) return c < .35 ? 'p3' : c < .6 ? 'p4' : c < .85 ? 'p2' : 'p1';
    if (y < 260) return c < .45 ? 'p0' : c < .85 ? 'p1' : 'p5';
    return c < .35 ? 'p1' : c < .65 ? 'p2' : c < .85 ? 'p0' : c < .95 ? 'p3' : 'p4';
  }

  /* 1) Cielo: capa base de trazos anchos, luego trazos medios y detalle fino */
  var sg = grp(skySvg), i, x, y;
  for (i = 0; i < 260; i++) flow(sg, R(-60, 1660), R(-40, 780), R(110, 170), R(24, 36), rnd() < .6 ? 'p0' : 'p1');
  for (i = 0; i < 1500; i++) { x = R(-40, 1640); y = R(-20, 780); flow(sg, x, y, R(50, 110), R(9, 18), skyCls(x, y)); }
  for (i = 0; i < 500; i++) { x = R(-40, 1640); y = R(-20, 780); flow(sg, x, y, R(24, 50), R(4, 8), skyCls(x, y)); }

  /* 2) Remolinos giratorios */
  var stage = document.querySelector('.stage');
  function polar(r, t) { return [Math.cos(t) * r, Math.sin(t) * r]; }
  function spiral(s, dur, rev) {
    var S = s.r * 1.25, arms = 4, a, t;
    var sv = el('svg', { viewBox: (-S) + ' ' + (-S) + ' ' + 2 * S + ' ' + 2 * S, 'class': 'sw' });
    sv.style.cssText = 'left:' + f((s.x - S) / 16) + '%;top:' + f((s.y - S) / 9) + '%;width:' + f(2 * S / 16) + '%;height:' + f(2 * S / 9) + '%;animation-duration:' + dur + 's;animation-direction:' + (rev ? 'reverse' : 'normal');
    var g = grp(sv);
    for (a = 0; a < arms; a++) for (t = 0; t < 60; t++) {
      var th = a * 2 * Math.PI / arms + t * .24 * s.d, r = 10 + t * (s.r / 60) * 1.1, dl = R(30, 55) / (2 * r + 10) * s.d, c = rnd();
      var cls = r < s.r * .35 ? (c < .5 ? 'p4' : 'p3') : (c < .4 ? 'p3' : c < .6 ? 'p2' : c < .8 ? 'p4' : 'p1');
      brush(g, polar(r, th - dl), polar(r * 1.06, th), polar(r * 1.03 + 2, th + dl), 5 + r / s.r * 10, cls);
    }
    stage.insertBefore(sv, fgSvg);
  }
  spiral(SW[0], 80, false); spiral(SW[1], 55, true); spiral(SW[2], 65, false);

  /* 2b) Estrellas: anillos de pinceladas amarillas (solo de noche) */
  var STARS = [[160, 150], [420, 80], [580, 245], [780, 110], [1000, 215], [1130, 80], [700, 340], [1020, 400], [1235, 310], [1500, 385], [300, 345]];
  var ng = grp(el('g', { 'class': 'nt' }, fgSvg));
  function q(c, r, th) { return [c[0] + Math.cos(th) * r, c[1] + Math.sin(th) * r]; }
  STARS.forEach(function (s) {
    [20, 31, 43].forEach(function (r, j) {
      var n = Math.round(6.283 * r / 15), k, th, dl = 7.5 / r;
      for (k = 0; k < n; k++) {
        th = k * 6.283 / n + R(-.1, .1);
        brush(ng, q(s, r, th - dl), q(s, r * 1.05, th), q(s, r, th + dl), R(3, 5) + (2 - j), j === 2 ? 'p3' : 'p4');
      }
    });
  });

  /* 3) Colinas, pueblo y ciprés */
  function hy1(x) { return 640 + 38 * Math.sin(x / 240 + 1) + 14 * Math.sin(x / 90); }
  function hy2(x) { return 752 + 22 * Math.sin(x / 210 + 2) + 8 * Math.sin(x / 70); }
  function hill(fn, fillCls, sc, n) {
    var d = 'M0 900', k; for (k = 0; k <= 1600; k += 20) d += 'L' + k + ' ' + f(fn(k)); d += 'L1600 900Z';
    el('path', { d: d, 'class': fillCls }, fgSvg);
    var g = grp(fgSvg);
    for (var j = 0; j < n; j++) {
      var x = R(-20, 1620), y = fn(x) + R(6, 900 - fn(x)), a = Math.atan2(fn(x + 10) - fn(x - 10), 20), L = R(40, 90);
      brush(g, [x, y], [x + Math.cos(a) * L / 2, y + Math.sin(a) * L / 2 + R(-5, 5)], [x + Math.cos(a) * L, y + Math.sin(a) * L], R(8, 15), sc[(rnd() * sc.length) | 0]);
    }
  }
  hill(hy1, 'fh1', ['h1a', 'h1b', 'h1a'], 340);
  var vg = el('g', {}, fgSvg);
  [[620, 40, 30], [690, 52, 38], [775, 46, 34], [1010, 60, 42], [1100, 44, 32], [1160, 50, 36]].forEach(function (h) {
    var yy = hy1(h[0] + h[1] / 2) + 12;
    el('rect', { x: h[0], y: yy - h[2], width: h[1], height: h[2], 'class': 'fhouse' }, vg);
    el('polygon', { points: (h[0] - 6) + ',' + (yy - h[2]) + ' ' + (h[0] + h[1] / 2) + ',' + (yy - h[2] - 24) + ' ' + (h[0] + h[1] + 6) + ',' + (yy - h[2]), 'class': 'froof' }, vg);
    el('rect', { x: h[0] + h[1] / 2 - 5, y: yy - h[2] + 10, width: 10, height: 13, 'class': 'win' }, vg);
  });
  var cy = hy1(914) + 12;
  el('rect', { x: 900, y: cy - 90, width: 28, height: 90, 'class': 'fhouse' }, vg);
  el('polygon', { points: '896,' + (cy - 90) + ' 914,' + (cy - 176) + ' 932,' + (cy - 90), 'class': 'froof' }, vg);
  el('rect', { x: 909, y: cy - 62, width: 10, height: 16, 'class': 'win' }, vg);
  hill(hy2, 'fh2', ['h2a', 'h2b', 'h2b'], 260);

  function cx(yv) { return 262 + 16 * Math.sin(yv * .012); }
  function hw(yv) { var t = Math.max(0, (yv - 215) / 685); return 62 * Math.pow(t, .62) * (1 + .14 * Math.sin(yv * .045)); }
  var cg = el('g', {}, fgSvg), d = 'M' + f(cx(215)) + ' 215', yy;
  for (yy = 215; yy <= 905; yy += 15) d += 'L' + f(cx(yy) - hw(yy)) + ' ' + yy;
  for (yy = 905; yy >= 215; yy -= 15) d += 'L' + f(cx(yy) + hw(yy)) + ' ' + yy;
  el('path', { d: d + 'Z', 'class': 'fcyp' }, cg);
  var cgs = grp(cg), cc = ['cy0', 'cy1', 'cy2', 'cy0'];
  for (i = 0; i < 360; i++) {
    yy = R(230, 900); x = cx(yy) + R(-1, 1) * hw(yy) * .9;
    var L = R(40, 80), tl = -Math.PI / 2 + Math.sin(yy * .03 + x) * .35;
    brush(cgs, [x, yy], [x + Math.cos(tl) * L / 2, yy + Math.sin(tl) * L / 2], [x + Math.cos(tl) * L * .9 + R(-6, 6), yy + Math.sin(tl) * L], R(7, 13), cc[(rnd() * 4) | 0]);
  }
})();