/* The three-axis map of the 2026 lists: a rotatable cube, three flat charts, a table and the method. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc, V = window.AxesView;
  A.mount("axes");
  var main = document.getElementById("main");
  if (!V) { A.notFound(main, "נתוני מפת הצירים לא נטענו."); return; }
  var AX = V.AX;
  var e = A.byKey[AX.election];
  var SVGNS = "http://www.w3.org/2000/svg";

  // the scored lists, largest in the polls first
  var LISTS = e.lists.filter(function (l) { return AX.lists[l.id]; }).sort(function (a, b) {
    return (b.polls ? b.polls.overall : 0) - (a.polls ? a.polls.overall : 0);
  }).map(function (l) {
    var d = AX.lists[l.id];
    return { l: l, color: A.partyColor(l), name: V.shortName(l), href: A.partyHref(e.key, l.id) + "#axes",
             s: { sec: d.axes.sec.score, soc: d.axes.soc.score, eco: d.axes.eco.score } };
  });
  var AXK = ["sec", "soc", "eco"];
  function axisOf(k) { return V.BY_AXIS[k]; }
  function tip(p) {
    return p.l.name + ": " + AXK.map(function (k) { return axisOf(k).he + " " + V.scoreText(p.s[k]); }).join(", ");
  }

  /* ------------------------------------------------------------ the cube */
  var CW = 640, CH = 500, SC = 150, yaw = -0.62, pitch = 0.38, START = [yaw, pitch];
  function cubeFrame() {
    function v(k, s) { return s == null ? null : (s - 5) / 5; }
    var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    function proj(x, y, z) {                       // x = security, y = social (up), z = economic
      var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
      var y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
      var f = 4.2 / (4.2 - z2), s = SC;
      return { x: CW / 2 + x1 * s * f, y: CH / 2 - y2 * s * f, z: z2 };
    }
    var g = [];
    // wire cube
    var C = [-1, 1], corners = [];
    C.forEach(function (x) { C.forEach(function (y) { C.forEach(function (z) { corners.push([x, y, z]); }); }); });
    corners.forEach(function (a, i) {
      corners.forEach(function (b, j) {
        if (j <= i) return;
        var diff = 0; for (var k = 0; k < 3; k++) if (a[k] !== b[k]) diff++;
        if (diff !== 1) return;
        var p = proj(a[0], a[1], a[2]), q = proj(b[0], b[1], b[2]);
        g.push({ z: (p.z + q.z) / 2 - 3, s: '<line x1="' + p.x.toFixed(1) + '" y1="' + p.y.toFixed(1) + '" x2="' + q.x.toFixed(1) + '" y2="' + q.y.toFixed(1) + '" class="cb-edge"/>' });
      });
    });
    // central axes with their end labels
    [["sec", [1, 0, 0]], ["soc", [0, 1, 0]], ["eco", [0, 0, 1]]].forEach(function (d) {
      var a = axisOf(d[0]), u = d[1];
      var p = proj(-u[0], -u[1], -u[2]), q = proj(u[0], u[1], u[2]);
      var p2 = proj(-1.28 * u[0], -1.28 * u[1], -1.28 * u[2]), q2 = proj(1.28 * u[0], 1.28 * u[1], 1.28 * u[2]);
      g.push({ z: -2.5, s: '<line x1="' + p.x.toFixed(1) + '" y1="' + p.y.toFixed(1) + '" x2="' + q.x.toFixed(1) + '" y2="' + q.y.toFixed(1) + '" class="cb-axis ' + d[0] + '"/>' });
      g.push({ z: 5, s: '<text x="' + p2.x.toFixed(1) + '" y="' + p2.y.toFixed(1) + '" class="cb-end ' + d[0] + '">' + esc(a.lo) + "</text>" });
      g.push({ z: 5, s: '<text x="' + q2.x.toFixed(1) + '" y="' + q2.y.toFixed(1) + '" class="cb-end ' + d[0] + '">' + esc(a.hi) + "</text>" });
    });
    // the lists
    LISTS.forEach(function (p) {
      var x = v("sec", p.s.sec), y = v("soc", p.s.soc), z = v("eco", p.s.eco);
      var unknown = [x, y, z].filter(function (t) { return t == null; }).length;
      if (unknown > 1) return;
      var link = '<a href="' + esc(p.href) + '" class="cb-pt"><title>' + esc(tip(p)) + "</title>";
      if (unknown) {
        var a = proj(x == null ? -1 : x, y == null ? -1 : y, z == null ? -1 : z);
        var b = proj(x == null ? 1 : x, y == null ? 1 : y, z == null ? 1 : z);
        var m = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
        g.push({ z: (a.z + b.z) / 2, s: link + '<line x1="' + a.x.toFixed(1) + '" y1="' + a.y.toFixed(1) + '" x2="' + b.x.toFixed(1) + '" y2="' + b.y.toFixed(1) + '" class="cb-unk" stroke="' + p.color + '"/>' +
          '<text x="' + (m.x + 8).toFixed(1) + '" y="' + (m.y - 6).toFixed(1) + '" class="cb-lbl">' + esc(p.name) + "</text></a>" });
        return;
      }
      var c = proj(x, y, z), fl = proj(x, -1, z);
      var r = 6 + 2.2 * (c.z + 1);
      g.push({ z: c.z, s: link + '<line x1="' + c.x.toFixed(1) + '" y1="' + c.y.toFixed(1) + '" x2="' + fl.x.toFixed(1) + '" y2="' + fl.y.toFixed(1) + '" class="cb-drop" stroke="' + p.color + '"/>' +
        '<circle cx="' + fl.x.toFixed(1) + '" cy="' + fl.y.toFixed(1) + '" r="2.4" fill="' + p.color + '" opacity="0.45"/>' +
        '<circle cx="' + c.x.toFixed(1) + '" cy="' + c.y.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="' + p.color + '" class="cb-dot"/>' +
        '<text x="' + (c.x + r + 4).toFixed(1) + '" y="' + (c.y + 4).toFixed(1) + '" class="cb-lbl">' + esc(p.name) + "</text></a>" });
    });
    g.sort(function (a, b) { return a.z - b.z; });
    return g.map(function (o) { return o.s; }).join("");
  }

  /* ------------------------------------------------------------ a flat chart */
  function flat(kx, ky) {
    var W = 380, H = 380, m = { l: 40, r: 14, t: 14, b: 46 }, pw = W - m.l - m.r, ph = H - m.t - m.b;
    var ax = axisOf(kx), ay = axisOf(ky);
    function X(v) { return m.l + v / 10 * pw; }
    function Y(v) { return m.t + ph - v / 10 * ph; }
    var out = [], boxes = [];
    for (var i = 0; i <= 10; i++) {
      var cls = i === 5 ? "fl-grid mid" : "fl-grid";
      out.push('<line x1="' + X(i) + '" x2="' + X(i) + '" y1="' + Y(0) + '" y2="' + Y(10) + '" class="' + cls + '"/>');
      out.push('<line y1="' + Y(i) + '" y2="' + Y(i) + '" x1="' + X(0) + '" x2="' + X(10) + '" class="' + cls + '"/>');
    }
    [0, 5, 10].forEach(function (t) {
      out.push('<text x="' + X(t) + '" y="' + (Y(0) + 15) + '" class="fl-tick">' + t + "</text>");
      out.push('<text x="' + (X(0) - 8) + '" y="' + (Y(t) + 4) + '" class="fl-tick y">' + t + "</text>");
    });
    out.push('<text x="' + X(0) + '" y="' + (H - 8) + '" class="fl-end" text-anchor="start">' + esc(ax.lo) + "</text>");
    out.push('<text x="' + X(10) + '" y="' + (H - 8) + '" class="fl-end" text-anchor="end">' + esc(ax.hi) + "</text>");
    out.push('<text x="' + X(5) + '" y="' + (H - 8) + '" class="fl-name">' + esc(ax.he) + " →</text>");
    out.push('<text transform="translate(13 ' + Y(5) + ') rotate(-90)" class="fl-name">' + esc(ay.he) + " →</text>");
    out.push('<text transform="translate(13 ' + Y(0) + ') rotate(-90)" class="fl-end" text-anchor="start">' + esc(ay.lo) + "</text>");
    out.push('<text transform="translate(13 ' + Y(10) + ') rotate(-90)" class="fl-end" text-anchor="end">' + esc(ay.hi) + "</text>");

    // group lists that share a point
    var groups = {}, order = [], dashed = [];
    LISTS.forEach(function (p) {
      var x = p.s[kx], y = p.s[ky];
      if (x == null && y == null) return;
      if (x == null || y == null) { dashed.push(p); return; }
      var k = x + "," + y;
      if (!groups[k]) { groups[k] = { x: x, y: y, ps: [] }; order.push(k); }
      groups[k].ps.push(p);
    });
    var dots = [];
    order.forEach(function (k) {
      var gr = groups[k], n = gr.ps.length;
      gr.ps.forEach(function (p, i) {
        var off = n === 1 ? 0 : (i - (n - 1) / 2) * 11;
        var cx = X(gr.x) + off, cy = Y(gr.y);
        dots.push('<a href="' + esc(p.href) + '"><title>' + esc(tip(p)) + '</title><circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="6.5" fill="' + p.color + '" class="fl-dot"/></a>');
        boxes.push([cx - 7, cy - 7, cx + 7, cy + 7]);
      });
    });
    // dashed lines for an unknown axis
    var dash = dashed.map(function (p) {
      var x = p.s[kx], y = p.s[ky], ln;
      if (x == null) ln = [X(0), Y(y), X(10), Y(y)]; else ln = [X(x), Y(0), X(x), Y(10)];
      return { p: p, ln: ln };
    });
    dash.forEach(function (d) {
      out.push('<a href="' + esc(d.p.href) + '"><title>' + esc(tip(d.p)) + '</title><line x1="' + d.ln[0] + '" y1="' + d.ln[1] + '" x2="' + d.ln[2] + '" y2="' + d.ln[3] + '" stroke="' + d.p.color + '" class="fl-unk"/></a>');
    });
    // labels: first free spot around each group
    function width(t) { return t.length * 7 + 4; }
    // overlap with what is already drawn, plus a large penalty for leaving the plot
    function cost(b) {
      var c = 0;
      b = [b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2];     // keep a little air between labels
      if (b[0] < 2 || b[2] > W - 2 || b[1] < m.t - 4 || b[3] > Y(0) + 2) c += 1e6;
      for (var i = 0; i < boxes.length; i++) {
        var o = boxes[i];
        var ox = Math.min(b[2], o[2]) - Math.max(b[0], o[0]), oy = Math.min(b[3], o[3]) - Math.max(b[1], o[1]);
        if (ox > 0 && oy > 0) c += ox * oy;
      }
      return c;
    }
    var labels = [];
    function place(text, cx, cy, half, alt) {
      var w = width(text), h = 14, cand = [];
      [[cx, cy]].concat(alt || []).forEach(function (pt) {
        var x = pt[0], y = pt[1];
        cand.push([x + half + 4, y - h / 2], [x - half - 4 - w, y - h / 2], [x - w / 2, y - 9 - h], [x - w / 2, y + 9],
          [x + half + 2, y - h - 4], [x + half + 2, y + 4], [x - half - 2 - w, y - h - 4], [x - half - 2 - w, y + 4],
          [x + half + 2, y - h - 16], [x + half + 2, y + 16], [x - half - 2 - w, y - h - 16], [x - half - 2 - w, y + 16]);
      });
      var best = null, bc = Infinity;
      for (var i = 0; i < cand.length; i++) {
        var bx = [cand[i][0], cand[i][1], cand[i][0] + w, cand[i][1] + h], c = cost(bx);
        if (c < bc) { bc = c; best = bx; }
        if (c === 0) break;
      }
      boxes.push(best);
      // a thin leader line when the label ended up away from its point
      var lx = Math.max(best[0], Math.min(cx, best[2])), ly = Math.max(best[1], Math.min(cy, best[3]));
      if (Math.abs(lx - cx) + Math.abs(ly - cy) > half + 14) {
        labels.push('<line x1="' + cx.toFixed(1) + '" y1="' + cy.toFixed(1) + '" x2="' + lx.toFixed(1) + '" y2="' + ly.toFixed(1) + '" class="fl-lead"/>');
      }
      labels.push('<text x="' + (best[0] + 2).toFixed(1) + '" y="' + (best[1] + 10.5).toFixed(1) + '" class="fl-lbl">' + esc(text) + "</text>");
    }
    order.slice().sort(function (a, b) { return groups[b].ps.length - groups[a].ps.length; }).forEach(function (k) {
      var gr = groups[k], half = 6.5 + (gr.ps.length - 1) * 5.5;
      place(gr.ps.map(function (p) { return p.name; }).join(" · "), X(gr.x), Y(gr.y), half);
    });
    dash.forEach(function (d) {
      var ln = d.ln;
      if (ln[1] === ln[3]) place(d.p.name + " (?)", X(0.6), ln[1], 0, [[X(9.4), ln[1]], [X(5), ln[1]]]);
      else place(d.p.name + " (?)", ln[0], Y(9.6), 0, [[ln[0], Y(0.5)], [ln[0], Y(5)]]);
    });
    return '<figure class="fl-chart"><svg viewBox="0 0 ' + W + " " + H + '" role="img" direction="ltr" aria-label="' +
      esc(ax.he + " מול " + ay.he) + '">' + out.join("") + dots.join("") + labels.join("") + "</svg>" +
      "<figcaption><b>" + esc(ax.he) + "</b> (אופקי) מול <b>" + esc(ay.he) + "</b> (אנכי)</figcaption></figure>";
  }

  /* ------------------------------------------------------------ the table */
  function table() {
    return '<div class="table-scroll"><table class="data ax-table"><thead><tr><th>רשימה</th>' +
      AXK.map(function (k) { var a = axisOf(k); return '<th>' + esc(a.he) + ' <span class="small">(' + esc(a.lo) + " 0 · " + esc(a.hi) + " 10)</span></th>"; }).join("") +
      "</tr></thead><tbody>" + LISTS.map(function (p) {
        return '<tr><td><a class="ax-who" href="' + esc(p.href) + '">' + A.slip(p.l, "sm") + "<span>" + esc(p.l.name) + "</span></a></td>" +
          AXK.map(function (k) {
            var s = p.s[k];
            return '<td class="ax-cell' + (s == null ? " unk" : "") + '"><b>' + V.scoreText(s) + "</b>" + V.track(s, p.color) + "</td>";
          }).join("") + "</tr>";
      }).join("") + "</tbody></table></div>";
  }

  /* ------------------------------------------------------------ page */
  var unknown = LISTS.filter(function (p) { return AXK.some(function (k) { return p.s[k] == null; }); });
  main.innerHTML =
    '<section class="e-head"><div class="wrap"><div class="bg-num" aria-hidden="true">3D</div><h1>מפת הצירים</h1>' +
    '<p class="lede" style="margin-top:8px">כל רשימה שעברה את אחוז החסימה לפחות בסקר אחד לפני הבחירות לכנסת ה-26, על שלושה צירים: <b>ביטחוני</b> (יוני–ניצי), <b>חברתי</b> (ליברלי–שמרני) ו<b>כלכלי</b> (סוציאליסטי–קפיטליסטי). 0 עד 10 בכל ציר.</p></div></section>' +
    '<section class="block" style="padding-top:18px"><div class="wrap"><div class="panel-intro">' +
    "<p><b>זו הערכה של האתר, לא הגדרה של המפלגות.</b> כל ציר מחולק למדדים, וכל מדד מקבל ציון לפי עוגנים קבועים (בתחתית העמוד) ולפי ראיות: קודם הצבעות, חקיקה והתנהלות בממשלה, ורק אחר כך מצעים והצהרות. " +
    "לכל ציון יש מקור, בעמוד של כל רשימה. האיסוף נעשה בעזרת AI, וכל ציון נבדק ואושר ידנית; אם מצאתם טעות, כתבו לנו (פרטים בעמוד <a href=\"" + A.pageHref("about") + "\">על האתר</a>).</p>" +
    "<p>הצירים כאן אינם הצבע של הרשימה באתר: הצבע (וציר ימין-שמאל בתעודות הזהות) לקוח מוויקיפדיה האנגלית, כמקור חיצוני.</p></div></div></section>" +
    '<section class="block"><div class="wrap"><header><h2>הקובייה</h2><p>גוררים כדי לסובב; לחיצה על נקודה פותחת את הנימוקים</p></header>' +
    '<div class="cube"><svg viewBox="0 0 ' + CW + " " + CH + '" direction="ltr" tabindex="0" role="img" aria-label="מפה תלת-ממדית של הרשימות על שלושת הצירים. אפשר לסובב בגרירה או בחצים." data-cube></svg>' +
    '<div class="cube-ctl"><button type="button" class="btn ghost" data-view="sec,soc">מלפנים: ביטחוני × חברתי</button>' +
    '<button type="button" class="btn ghost" data-view="eco,soc">מהצד: כלכלי × חברתי</button>' +
    '<button type="button" class="btn ghost" data-view="sec,eco">מלמעלה: ביטחוני × כלכלי</button>' +
    '<button type="button" class="btn ghost" data-view="reset">זווית התחלתית</button></div>' +
    '<p class="small">הקו מכל נקודה לרצפה עוזר לראות עומק. ' + (unknown.length ? "קו מקווקו: רשימה שאחד הצירים שלה לא ידוע (" + esc(unknown.map(function (p) { return p.l.name; }).join(", ")) + "), והיא יכולה להיות בכל מקום לאורכו." : "") + "</p></div></div></section>" +
    '<section class="block"><div class="wrap"><header><h2>שלושה מבטים שטוחים</h2><p>אותם ציונים, זוג צירים בכל פעם; קל יותר לקרוא מהם ערכים</p></header>' +
    '<div class="fl-grid3">' + flat("sec", "soc") + flat("sec", "eco") + flat("soc", "eco") + "</div>" +
    '<p class="small">רשימות באותה נקודה מוצגות זו לצד זו. "(?)" וקו מקווקו: הציר השני של הרשימה לא ידוע.</p></div></section>' +
    '<section class="block"><div class="wrap"><header><h2>כל הציונים</h2><p>לפי ממוצע הסקרים; לחיצה על רשימה פותחת את המדדים והמקורות</p></header>' + table() + "</div></section>" +
    '<section class="block" id="method"><div class="wrap"><header><h2>השיטה</h2><p>הכללים והעוגנים שלפיהם ניתן כל ציון</p></header>' +
    '<ol class="ax-rules">' + AX.rules.map(function (r) { return "<li>" + esc(r) + "</li>"; }).join("") + "</ol>" +
    V.anchorsTables() + "</div></section>";

  /* ------------------------------------------------------------ cube interaction */
  var svg = main.querySelector("[data-cube]");
  // a smaller drawing area on narrow screens, so the labels stay readable
  function fit() {
    var narrow = svg.getBoundingClientRect().width < 560;
    CW = narrow ? 420 : 640; CH = narrow ? 420 : 500; SC = narrow ? 120 : 150;
    svg.setAttribute("viewBox", "0 0 " + CW + " " + CH);
  }
  function draw() { svg.innerHTML = cubeFrame(); }
  fit();
  window.addEventListener("resize", function () { fit(); draw(); });
  draw();
  var spinning = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var anim = null;
  function stop() { spinning = false; if (anim) { cancelAnimationFrame(anim); anim = null; } }
  function spin() {
    if (!spinning) return;
    yaw += 0.003; draw();
    anim = requestAnimationFrame(spin);
  }
  var drag = null, moved = 0;
  svg.addEventListener("pointerdown", function (ev) {
    stop(); drag = { x: ev.clientX, y: ev.clientY }; moved = 0;
    try { svg.setPointerCapture(ev.pointerId); } catch (err) { /* old browsers */ }
  });
  svg.addEventListener("pointermove", function (ev) {
    if (!drag) return;
    var dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    moved += Math.abs(dx) + Math.abs(dy);
    drag = { x: ev.clientX, y: ev.clientY };
    yaw += dx * 0.01; pitch = Math.max(-1.45, Math.min(1.45, pitch + dy * 0.01));
    draw();
  });
  function end() { drag = null; }
  svg.addEventListener("pointerup", end);
  svg.addEventListener("pointercancel", end);
  svg.addEventListener("click", function (ev) { if (moved > 5) { ev.preventDefault(); ev.stopPropagation(); } }, true);
  svg.addEventListener("keydown", function (ev) {
    var k = ev.key;
    if (k === "ArrowLeft") yaw -= 0.12; else if (k === "ArrowRight") yaw += 0.12;
    else if (k === "ArrowUp") pitch = Math.max(-1.45, pitch - 0.12); else if (k === "ArrowDown") pitch = Math.min(1.45, pitch + 0.12);
    else return;
    ev.preventDefault(); stop(); draw();
  });
  var VIEWS = { "sec,soc": [0, 0], "eco,soc": [-Math.PI / 2, 0], "sec,eco": [0, -(Math.PI / 2 - 0.001)], "reset": START };
  main.querySelectorAll("[data-view]").forEach(function (b) {
    b.addEventListener("click", function () {
      stop();
      var v = VIEWS[b.getAttribute("data-view")];
      yaw = v[0]; pitch = v[1]; draw();
    });
  });
  if (spinning) anim = requestAnimationFrame(spin);
})();
