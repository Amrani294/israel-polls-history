/* Home: the chamber today, the eight elections, party trajectories, poll surprises, blocs. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc;
  A.mount("home");
  var main = document.getElementById("main");
  var E = A.ELECTIONS;                       // newest first
  var CHRONO = E.slice().reverse();          // oldest first
  var latest = E[0];

  function axisLegend() {
    var stops = [-3, -2, -1, 0, 1, 2, 3];
    var grad = stops.map(function (s, i) { return A.colorAt(s) + " " + (100 * i / 6).toFixed(1) + "%"; }).join(", ");
    return '<div class="axis-legend" style="margin-top:22px;max-width:460px">' +
      '<div style="height:10px;border-radius:999px;background:linear-gradient(90deg,' + grad + ')"></div>' +
      '<div style="display:flex;justify-content:space-between;font-size:0.8rem;color:var(--mute);margin-top:4px" dir="ltr">' +
      "<span>שמאל קיצוני</span><span>מרכז</span><span>ימין קיצוני</span></div>" +
      '<p class="small" style="margin-top:6px">צבע כל רשימה נקבע לפי המיקום הפוליטי שלה בתיבת המידע של ויקיפדיה האנגלית. אפור: אין מיקום במקור.</p></div>';
  }

  function shortLabel(e) {
    if (e.key === "2019a") return "אפריל 2019";
    if (e.key === "2019b") return "ספטמבר 2019";
    return e.date.slice(0, 4);
  }

  function card(e) {
    var top = e.lists.slice().sort(function (a, b) { return b.seats - a.seats; })[0];
    return '<a class="card" href="' + A.electionHref(e.key) + '">' +
      '<span><span class="when">' + esc(A.shortWhen(e)) + '</span><br><span class="kn">הכנסת ה-' + esc(e.knesset) + "</span></span>" +
      "<span></span>" + A.hemicycle(e, { center: false, label: "חלוקת המושבים, " + A.electionTitle(e) }) +
      '<span class="winner">' + A.slip(top, "sm") + "<span>הגדולה: <b>" + esc(top.name) + "</b>, " + top.seats + " מושבים<br>" +
      (e.government ? esc(e.government.name) + ": " + esc(e.government.pm) : "לא הוקמה ממשלה") + "</span></span></a>";
  }

  /* ---------------------------------------------------------------- party trajectories */
  function trajectories() {
    var count = {}, last = {};
    CHRONO.forEach(function (e) {
      e.lists.forEach(function (l) { if (l.seats > 0) { count[l.id] = (count[l.id] || 0) + 1; last[l.id] = l; } });
    });
    var ids = Object.keys(count).filter(function (id) { return count[id] >= 4; })
      .sort(function (a, b) { return last[b].seats - last[a].seats; });
    var W = 900, H = 400, m = { l: 34, r: 130, t: 20, b: 40 };
    var n = CHRONO.length, maxV = 40;
    function x(i) { return m.l + (W - m.l - m.r) * i / (n - 1); }
    function y(v) { return H - m.b - (H - m.t - m.b) * v / maxV; }
    var g = [];
    for (var v = 0; v <= maxV; v += 10) {
      g.push('<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#e8eaef"/>');
      g.push('<text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" font-size="11" fill="#6b7385" text-anchor="end">' + v + "</text>");
    }
    CHRONO.forEach(function (e, i) {
      g.push('<text x="' + x(i) + '" y="' + (H - m.b + 22) + '" font-size="11.5" fill="#4a5268" text-anchor="middle">' + esc(shortLabel(e)) + "</text>");
    });
    var lines = [], ends = [];
    ids.forEach(function (id) {
      var pts = CHRONO.map(function (e) {
        var l = e.lists.filter(function (q) { return q.id === id && q.seats > 0; })[0];
        return l || null;
      });
      var c = A.partyColor(last[id]);
      for (var i = 1; i < n; i++) {
        if (pts[i] && pts[i - 1]) {
          lines.push('<line data-f="' + id + '" x1="' + x(i - 1) + '" y1="' + y(pts[i - 1].seats) + '" x2="' + x(i) + '" y2="' + y(pts[i].seats) + '" stroke="' + c + '" stroke-width="2.5" stroke-linecap="round"/>');
        }
      }
      pts.forEach(function (l, i) {
        if (!l) return;
        lines.push('<circle data-f="' + id + '" cx="' + x(i) + '" cy="' + y(l.seats) + '" r="4.5" fill="' + c + '" stroke="#fff" stroke-width="1.5"><title>' +
          esc(l.name + ", " + A.shortWhen(CHRONO[i]) + ": " + l.seats + " מושבים") + "</title></circle>");
      });
      var lastIdx = -1;
      pts.forEach(function (l, i) { if (l) lastIdx = i; });
      ends.push({ id: id, name: last[id].name, c: c, y: y(pts[lastIdx].seats), x: x(lastIdx) });
    });
    // keep end labels from overlapping
    ends.sort(function (a, b) { return a.y - b.y; });
    for (var k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < 14) ends[k].y = ends[k - 1].y + 14;
    var labels = ends.map(function (t) {
      return '<text data-f="' + t.id + '" x="' + (W - m.r + 12) + '" y="' + (t.y + 4) + '" font-size="12.5" font-weight="600" fill="' + t.c + '">' + esc(t.name) + "</text>";
    });
    var legend = ids.map(function (id) {
      return '<button type="button" aria-pressed="false" data-f="' + id + '" style="--pc:' + A.partyColor(last[id]) + '">' + esc(last[id].name) + "</button>";
    }).join("");
    return '<figure><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="מספר המושבים של הרשימות הגדולות בכל מערכת בחירות" direction="ltr">' +
      g.join("") + lines.join("") + labels.join("") + "</svg>" +
      '<div class="lg">' + legend + "</div>" +
      '<figcaption class="small" style="margin-top:8px">רשימות שנכנסו לכנסת לפחות ארבע פעמים. קו נקטע כשהרשימה לא רצה לבד: למשל ב-2013 הליכוד וישראל ביתנו רצו יחד (31 מושבים), וב-2015 העבודה רצה במחנה הציוני. ' +
      "המרווח בין המערכות שווה ואינו לפי הזמן שעבר. לחיצה על שם מבליטה את הקו.</figcaption></figure>";
  }

  /* ---------------------------------------------------------------- surprises */
  function surprises() {
    var all = [];
    E.forEach(function (e) {
      e.lists.forEach(function (l) {
        if (l.polls && l.polls.overall != null) all.push({ e: e, l: l, d: l.seats - l.polls.overall });
      });
    });
    all.sort(function (a, b) { return Math.abs(b.d) - Math.abs(a.d); });
    return all.slice(0, 8).map(function (s) {
      var up = s.d > 0;
      return '<a class="surprise" style="--pc:' + A.partyColor(s.l) + '" href="' + A.partyHref(s.e.key, s.l.id) + '">' + A.slip(s.l, "sm") +
        '<span class="txt"><span class="t">' + esc(s.l.name) + '</span><span class="s">' + esc(A.shortWhen(s.e)) + '</span><span class="s">סקרים ' + A.fmtSeats(s.l.polls.overall) +
        " | קלפי " + s.l.seats + '</span></span><span class="d ' + (up ? "up" : "down") + '">' + (up ? "+" : "−") + A.fmtSeats(Math.abs(s.d)) + "</span></a>";
    }).join("");
  }

  function blocRows() {
    return E.map(function (e) {
      var rows = [["סקרים", e.blocs.polls], ["מדגמים", e.blocs.exit], ["תוצאה", e.blocs.final]];
      return '<div class="bloc-row"><div class="who"><a href="' + A.electionHref(e.key) + '">' + esc(A.shortWhen(e)) + "</a><br>" +
        '<span class="small">' + (e.kind === "rec" ? "לפי ההמלצות לנשיא" : "לפי הממשלה שהושבעה") + "</span></div>" +
        '<div class="bars">' + rows.map(function (r) {
          return '<div class="bar-wrap"><span class="bar-label">' + r[0] + "</span>" + A.blocBar(e, r[1]) + "</div>";
        }).join("") + "</div></div>";
    }).join("");
  }

  main.innerHTML =
    '<section class="hero"><div class="wrap"><div class="hero-grid"><div>' +
    "<h1>היסטוריית הסקרים של ישראל</h1>" +
    '<p class="lede" style="margin-top:14px">שמונה מערכות בחירות לכנסת, מ-2009 ועד 2022: מי נבחר, איך התחלקה הכנסת בין ימין לשמאל ובין קואליציה לאופוזיציה, ומה אמרו הסקרים לפני כן.</p>' +
    axisLegend() +
    '<div class="kicker-row"><a class="btn" href="' + A.electionHref(latest.key) + '">' + esc(A.electionTitle(latest)) + '</a><a class="btn ghost" href="polls.html">ארכיון הסקרים</a></div>' +
    '</div><a class="hero-chamber" href="' + A.electionHref(latest.key) + '" style="text-decoration:none;color:inherit">' + A.hemicycle(latest, { label: "הכנסת ה-" + latest.knesset + " כפי שנבחרה" }) +
    '<div class="cap"><b>הכנסת ה-' + esc(latest.knesset) + "</b><span>כפי שנבחרה, " + esc(A.fmtDate(latest.date)) + "</span></div></a>" +
    "</div></div></section>" +

    '<section class="block"><div class="wrap"><header><h2>שמונה מערכות בחירות</h2><p>לחיצה על מערכת פותחת את התוצאות, הרשימות והסקרים שלה</p></header>' +
    '<div class="strip" style="margin-top:0">' + E.map(card).join("") + "</div></div></section>" +

    '<section class="block traj"><div class="wrap"><header><h2>מסלול המפלגות</h2><p>מושבים בכל מערכת, לרשימות שחזרו שוב ושוב</p></header>' +
    trajectories() + "</div></section>" +

    '<section class="block"><div class="wrap"><header><h2>הפתעות הקלפי</h2><p>הפערים הגדולים ביותר בין ממוצע הסקרים בשלושת החודשים האחרונים לבין התוצאה</p></header>' +
    '<div class="surprises">' + surprises() + "</div>" +
    '<p class="small" style="margin-top:10px">מחושב לרשימות שנכללו במעקב הסקרים. ממוצע הסקרים הוא ממוצע הגופים (כל גוף במשקל שווה).</p></div></section>' +

    '<section class="block"><div class="wrap"><header><h2>הסקרים מול הקלפי, לפי גושים</h2><p>ממוצע הסקרים, ממוצע המדגמים ותוצאת האמת</p></header>' +
    '<div class="legend"><span class="C"><i></i>קואליציה (2019: המליצו על נתניהו)</span><span class="O"><i></i>אופוזיציה (2019: המליצו על גנץ)</span>' +
    '<span class="N"><i></i>לא המליצו על אף אחד (2019)</span><span class="X"><i></i>לא נכנסו לכנסת</span></div>' +
    '<div class="bloc-rows">' + blocRows() + "</div>" +
    '<p class="small" style="margin-top:14px">השיוך לגוש נקבע לפי הרכב הממשלה הראשונה שהושבעה אחרי כל בחירות; באפריל ובספטמבר 2019 לא הוקמה ממשלה, ולכן לפי ההמלצות לנשיא. רשימה שהתפצלה אחרי הבחירות שויכה לפי רוב חבריה.</p>' +
    '<p style="margin-top:18px"><a class="btn" href="polls.html">לארכיון הסקרים המלא</a></p>' +
    "</div></section>";

  // highlight one party's line
  var traj = main.querySelector(".traj figure");
  traj.querySelectorAll(".lg button").forEach(function (b) {
    b.addEventListener("click", function () {
      var on = b.getAttribute("aria-pressed") !== "true";
      traj.querySelectorAll(".lg button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
      b.setAttribute("aria-pressed", String(on));
      var id = on ? b.getAttribute("data-f") : null;
      traj.querySelectorAll("svg [data-f]").forEach(function (nd) {
        nd.style.opacity = !id || nd.getAttribute("data-f") === id ? "" : "0.1";
      });
    });
  });
})();
