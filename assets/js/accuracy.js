/* Pollster accuracy: the last poll each outlet published before election day, against the result. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc, PV = window.PollsView;
  var POLLS = window.POLLS || [];
  A.mount("accuracy");
  var main = document.getElementById("main");

  // only elections that already have official results
  var ELS = A.ELECTIONS.filter(function (e) { return e.lists.some(function (l) { return l.seats > 0; }); });
  var OUTLETS = Object.keys(A.META.outlets || {});

  /* ------------------------------------------------------------ the metric */
  // Seats moved = half the sum of the absolute differences. The lists tracked in
  // the polls are compared one by one; everything else is one "other lists" group
  // (poll: its total minus the tracked lists; result: 120 minus the tracked lists).
  function pollScore(e, p) {
    var seats = {};
    e.lists.forEach(function (l) { seats[l.name] = l.seats; });
    var rows = [], sum = 0, trackedPoll = 0, trackedRes = 0;
    for (var i = 0; i < e.tracked.length; i++) {
      var n = e.tracked[i], v = p.values[n];
      if (v == null) return null;                     // a tracked list not reported: not comparable
      rows.push({ name: n, poll: v, res: seats[n], diff: v - seats[n] });
      sum += Math.abs(v - seats[n]);
      trackedPoll += v; trackedRes += seats[n];
    }
    var other = { name: "שאר הרשימות", poll: p.total - trackedPoll, res: 120 - trackedRes, other: true };
    other.diff = other.poll - other.res;
    sum += Math.abs(other.diff);
    rows.push(other);
    return { moved: sum / 2, rows: rows, total: p.total };
  }
  function exitScore(e, x) {
    var rows = [], sum = 0;
    e.lists.forEach(function (l) {
      var v = x.seats[l.name] || 0;
      if (!v && !l.seats) return;
      rows.push({ name: l.name, poll: v, res: l.seats, diff: v - l.seats });
      sum += Math.abs(v - l.seats);
    });
    return { moved: sum / 2, rows: rows, total: 120 };
  }

  function lastPolls(e) {
    var out = [];
    OUTLETS.forEach(function (o) {
      var ps = POLLS.filter(function (p) { return p.e === e.key && p.outlet === o; });
      if (!ps.length) return;
      var last = ps.reduce(function (m, p) { return p.end > m ? p.end : m; }, "");
      var tied = ps.filter(function (p) { return p.end === last; });
      tied.forEach(function (p) {
        var s = pollScore(e, p);
        if (s) out.push({ outlet: o, poll: p, score: s, tied: tied.length });
      });
    });
    return out.sort(function (a, b) { return a.score.moved - b.score.moved || (a.poll.end < b.poll.end ? 1 : -1); });
  }

  var DATA = ELS.map(function (e) {
    return {
      e: e,
      polls: lastPolls(e),
      exits: e.exitPolls.map(function (x) { return { x: x, score: exitScore(e, x) }; })
        .sort(function (a, b) { return a.score.moved - b.score.moved; })
    };
  });
  function mean(arr) { return arr.length ? arr.reduce(function (a, b) { return a + b; }, 0) / arr.length : null; }
  function fmt(v) { return v == null ? "—" : A.fmtSeats(Math.round(v * 10) / 10); }

  /* ------------------------------------------------------------ overview matrix */
  function cellFor(d, o) {
    var rs = d.polls.filter(function (r) { return r.outlet === o; });
    if (!rs.length) return null;
    return { v: mean(rs.map(function (r) { return r.score.moved; })), tied: rs.length > 1, rows: rs };
  }
  function matrix() {
    var head = "<tr><th>גוף</th>" + DATA.map(function (d) {
      return '<th class="n"><a class="rowlink" href="#e-' + esc(d.e.key) + '" data-key="' + esc(d.e.key) + '">' + esc(A.shortWhen(d.e)) + "</a></th>";
    }).join("") + '<th class="n">ממוצע</th></tr>';
    var best = {};
    DATA.forEach(function (d) {
      var vals = OUTLETS.map(function (o) { var c = cellFor(d, o); return c ? c.v : Infinity; });
      best[d.e.key] = Math.min.apply(null, vals);
    });
    var body = OUTLETS.map(function (o) {
      var vals = [];
      var tds = DATA.map(function (d) {
        var c = cellFor(d, o);
        if (!c) return '<td class="n muted">—</td>';
        vals.push(c.v);
        var isBest = c.v === best[d.e.key];
        return '<td class="n' + (isBest ? " best" : "") + '" title="' + esc(PV.outletName(d.e, o) + ", " + A.fmtDate(c.rows[0].poll.end)) + '">' +
          fmt(c.v) + (c.tied ? '<span class="note-mark" title="שני סקרים באותו יום אחרון; מוצג הממוצע">*</span>' : "") + "</td>";
      }).join("");
      var pred = (A.META.predecessors || {})[o];
      return '<tr><th scope="row" class="who">' + esc(A.META.outlets[o]) + (pred ? '<span class="small">עד 2015: ' + esc(pred) + "</span>" : "") + "</th>" + tds +
        '<td class="n avg">' + fmt(mean(vals)) + '<span class="small">' + vals.length + " מערכות</span></td></tr>";
    }).join("");
    var foot = '<tr class="sum-row"><th scope="row">כל הגופים</th>' + DATA.map(function (d) {
      return '<td class="n">' + fmt(mean(d.polls.map(function (r) { return r.score.moved; }))) + "</td>";
    }).join("") + '<td class="n"></td></tr>' +
      '<tr class="sum-row exit"><th scope="row">מדגמי ליל הבחירות</th>' + DATA.map(function (d) {
        return '<td class="n">' + fmt(mean(d.exits.map(function (r) { return r.score.moved; }))) + "</td>";
      }).join("") + '<td class="n"></td></tr>';
    return '<div class="table-scroll"><table class="data acc-matrix"><thead>' + head + "</thead><tbody>" + body + "</tbody><tfoot>" + foot + "</tfoot></table></div>" +
      '<p class="small" style="margin-top:8px">מנדטים שהוזזו בסקר האחרון של כל גוף. מודגש: הגוף המדויק ביותר באותה מערכת. ממוצע הגופים ומדגמי ליל הבחירות בשורות התחתונות.</p>';
  }

  /* ------------------------------------------------------------ election-by-election chart */
  function trendChart() {
    var W = 860, H = 250, m = { l: 34, r: 12, t: 16, b: 42 };
    var ds = DATA.slice().reverse();               // oldest first, left to right
    var maxV = 0;
    ds.forEach(function (d) {
      d.pAvg = mean(d.polls.map(function (r) { return r.score.moved; }));
      d.xAvg = mean(d.exits.map(function (r) { return r.score.moved; }));
      maxV = Math.max(maxV, d.pAvg || 0, d.xAvg || 0);
    });
    maxV = Math.ceil(maxV / 5) * 5;
    var bw = (W - m.l - m.r) / ds.length, g = [];
    function y(v) { return H - m.b - (H - m.t - m.b) * v / maxV; }
    for (var v = 0; v <= maxV; v += 5) {
      g.push('<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#e8eaef"/>');
      g.push('<text x="' + (m.l - 6) + '" y="' + (y(v) + 4) + '" font-size="11" fill="#6b7385" text-anchor="end">' + v + "</text>");
    }
    ds.forEach(function (d, i) {
      var x0 = m.l + i * bw + bw * 0.18, w = bw * 0.3;
      g.push('<rect x="' + x0.toFixed(1) + '" y="' + y(d.pAvg).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (H - m.b - y(d.pAvg)).toFixed(1) + '" fill="#18203a" rx="2"><title>' +
        esc(A.shortWhen(d.e) + ": סקרים אחרונים, " + fmt(d.pAvg) + " מנדטים") + "</title></rect>");
      g.push('<rect x="' + (x0 + w + 4).toFixed(1) + '" y="' + y(d.xAvg).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (H - m.b - y(d.xAvg)).toFixed(1) + '" fill="#b9bfcc" rx="2"><title>' +
        esc(A.shortWhen(d.e) + ": מדגמים, " + fmt(d.xAvg) + " מנדטים") + "</title></rect>");
      g.push('<text x="' + (x0 + w / 2).toFixed(1) + '" y="' + (y(d.pAvg) - 5).toFixed(1) + '" font-size="12" font-weight="700" text-anchor="middle" fill="#18203a">' + fmt(d.pAvg) + "</text>");
      g.push('<text x="' + (x0 + w * 1.5 + 4).toFixed(1) + '" y="' + (y(d.xAvg) - 5).toFixed(1) + '" font-size="12" text-anchor="middle" fill="#6b7385">' + fmt(d.xAvg) + "</text>");
      var parts = A.shortWhen(d.e).split(" ");
      g.push('<text x="' + (m.l + i * bw + bw / 2).toFixed(1) + '" y="' + (H - m.b + 17) + '" font-size="12" text-anchor="middle" fill="#18203a">' + esc(parts[0]) + "</text>");
      g.push('<text x="' + (m.l + i * bw + bw / 2).toFixed(1) + '" y="' + (H - m.b + 32) + '" font-size="12" text-anchor="middle" fill="#6b7385">' + esc(parts.slice(1).join(" ")) + "</text>");
    });
    return '<figure class="acc-trend"><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="ממוצע המנדטים שהוזזו בכל מערכת: סקרים אחרונים מול מדגמים" direction="ltr">' + g.join("") + "</svg>" +
      '<div class="legend"><span class="C"><i></i>הסקר האחרון של כל גוף (ממוצע)</span><span class="O"><i></i>מדגמי ליל הבחירות (ממוצע)</span></div></figure>';
  }

  /* ------------------------------------------------------------ one election in detail */
  function diffCell(d) {
    if (!d) return '<td class="n">0</td>';
    return '<td class="n ' + (d > 0 ? "delta-pos" : "delta-neg") + '"><span dir="ltr">' + (d > 0 ? "+" : "−") + A.fmtSeats(Math.abs(d)) + "</span></td>";
  }
  function detailTable(e, s, label) {
    return '<div class="table-scroll"><table class="data"><thead><tr><th>רשימה</th><th class="n">' + esc(label) + '</th><th class="n">תוצאה</th><th class="n">פער</th></tr></thead><tbody>' +
      s.rows.map(function (r) {
        return "<tr" + (r.other ? ' class="below"' : "") + "><td>" + esc(r.name) + '</td><td class="n">' + A.fmtSeats(r.poll) + '</td><td class="n">' + r.res + "</td>" + diffCell(r.diff) + "</tr>";
      }).join("") + "</tbody></table></div>";
  }
  function scoreRow(e, label, sub, s, max, src, extra, kind) {
    var w = max ? (100 * s.moved / max) : 0;
    return '<li class="acc-row ' + kind + '"><div class="who"><b>' + esc(label) + "</b>" + (sub ? '<span class="small">' + sub + "</span>" : "") + "</div>" +
      '<div class="meter"><span style="width:' + w.toFixed(2) + '%"></span></div>' +
      '<div class="v"><b>' + fmt(s.moved) + '</b><span class="small">מנדטים</span></div>' +
      '<details class="more"><summary>פירוט' + (src ? "" : "") + "</summary>" + (src ? '<p class="small">מקור: ' + src + "</p>" : "") + (extra || "") + detailTable(e, s, kind === "exit" ? "מדגם" : "סקר") + "</details></li>";
  }
  function detail(d) {
    var e = d.e;
    var max = Math.max.apply(null, d.polls.map(function (r) { return r.score.moved; }).concat(d.exits.map(function (r) { return r.score.moved; })));
    var polls = d.polls.map(function (r) {
      var p = r.poll;
      var sub = esc(A.fmtDate(p.end)) + (p.firm ? " · " + esc(p.firm) : "") + (r.tied > 1 ? " · " + esc(p.publisher) : "");
      var extra = r.score.total !== 120 ? '<p class="small">הסקר מסתכם ב-' + r.score.total + ' מושבים (כך הוא מופיע במקור), ולכן "שאר הרשימות" בו אינו משלים ל-120.</p>' : "";
      return scoreRow(e, PV.outletName(e, r.outlet), sub, r.score, max, PV.sourceLink(p), extra, "poll");
    }).join("");
    var exits = d.exits.map(function (r) {
      var x = r.x;
      var srcLink = x.source ? '<a href="' + esc(x.source) + '" target="_blank" rel="noopener">' + esc(x.source.replace(/^https?:\/\/(www\.)?/, "").split("/")[0]) + "</a>" : "";
      return scoreRow(e, PV.outletName(e, x.channel), esc(x.version), r.score, max, srcLink, "", "exit");
    }).join("");
    var pAvg = mean(d.polls.map(function (r) { return r.score.moved; })), xAvg = mean(d.exits.map(function (r) { return r.score.moved; }));
    return '<header><h2>' + esc(A.electionTitle(e)) + '</h2><p>' + esc(A.shortWhen(e)) + ' · <a href="' + A.electionHref(e.key) + '">לתוצאות ולרשימות</a> · <a href="' + A.pollsHref(e.key) + '">לכל הסקרים</a></p></header>' +
      '<div class="acc-sum"><div><span class="big">' + fmt(pAvg) + '</span><span>מנדטים הוזזו בממוצע<br>בסקרים האחרונים</span></div>' +
      '<div><span class="big mute">' + fmt(xAvg) + '</span><span>מנדטים הוזזו בממוצע<br>במדגמי ליל הבחירות</span></div></div>' +
      '<div class="two-col acc-cols"><div><h3>הסקר האחרון של כל גוף</h3><ol class="acc-list">' + polls + "</ol></div>" +
      "<div><h3>מדגמי ליל הבחירות</h3><ol class=\"acc-list\">" + exits + "</ol>" +
      '<p class="small">המדגם מושווה לכל הרשימות. הגרסה המוצגת היא המאוחרת ביותר שנמצאה באותו לילה, ולכן לא כל המדגמים פורסמו באותה שעה.</p></div></div>';
  }

  /* ------------------------------------------------------------ page */
  main.innerHTML =
    '<section class="e-head"><div class="wrap"><div class="bg-num" aria-hidden="true">±</div><h1>דיוק הסוקרים</h1>' +
    '<p class="lede" style="margin-top:8px">כמה קרוב היה הסקר האחרון של כל גוף לתוצאה בקלפי? המדד: <b>מנדטים שהוזזו</b>, כלומר כמה מושבים היה צריך להעביר מרשימה לרשימה כדי שהסקר יהיה זהה לתוצאה. 0 הוא פגיעה מושלמת.</p></div></section>' +
    '<section class="block" style="padding-top:18px"><div class="wrap">' +
    '<div class="panel-intro"><p><b>איך מחשבים:</b> לכל רשימה שבמעקב לוקחים את הפער בין הסקר לתוצאה, ואת כל שאר הרשימות סופרים כקבוצה אחת. סוכמים את הפערים ומחלקים ב-2, כי כל מושב שעודף אצל רשימה אחת חסר אצל אחרת. ' +
    "&quot;הסקר האחרון&quot; הוא הסקר האחרון שהגוף פרסם בשלושת החודשים שלפני הבחירות; לפי החוק אסור לפרסם סקרים בימים האחרונים שלפני יום הבחירות.</p></div>" +
    "</div></section>" +
    '<section class="block"><div class="wrap"><header><h2>כל הגופים, כל המערכות</h2><p>ככל שהמספר קטן יותר, הסקר היה מדויק יותר</p></header>' + matrix() + "</div></section>" +
    '<section class="block"><div class="wrap"><header><h2>סקרים מול מדגמים</h2><p>ממוצע המנדטים שהוזזו בכל מערכת</p></header>' + trendChart() + "</div></section>" +
    '<section class="block"><div class="wrap"><header><h2>מערכת אחר מערכת</h2></header>' +
    '<nav class="e-switch" aria-label="בחירת מערכת">' + DATA.map(function (d) {
      return '<a href="#e-' + esc(d.e.key) + '" data-key="' + esc(d.e.key) + '">' + esc(A.shortWhen(d.e)) + "</a>";
    }).join("") + '</nav><div class="acc-detail" data-detail></div></div></section>';

  var box = main.querySelector("[data-detail]");
  function show(key, scroll) {
    var d = DATA.filter(function (x) { return x.e.key === key; })[0] || DATA[0];
    box.innerHTML = detail(d);
    box.id = "e-" + d.e.key;
    main.querySelectorAll(".e-switch a").forEach(function (a) {
      if (a.getAttribute("data-key") === d.e.key) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    if (scroll) box.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  main.querySelectorAll("a[data-key]").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      var k = a.getAttribute("data-key");
      try { history.replaceState(null, "", A.pageHref("accuracy", "e=" + encodeURIComponent(k))); } catch (err) { /* file:// */ }
      show(k, true);
    });
  });
  var start = A.qs("e");
  show(DATA.some(function (d) { return d.e.key === start; }) ? start : DATA[0].e.key, false);
})();
