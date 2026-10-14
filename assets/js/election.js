/* One election: seat map, lists, blocs, recommendations, polls summary, sources. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc;
  A.mount("home");
  var main = document.getElementById("main");
  var key = A.qs("e") || A.ELECTIONS[0].key;
  var e = A.byKey[key];
  if (!e) { A.notFound(main, "אין במאגר מערכת בחירות בשם “" + key + "”."); return; }
  document.title = A.electionTitle(e) + " (" + A.shortWhen(e) + ") | היסטוריית הסקרים של ישראל";
  if (e.upcoming) { upcoming(); return; }

  var lists = e.lists.slice().sort(function (a, b) { return b.seats - a.seats || (b.votes - a.votes); });
  var inK = lists.filter(function (l) { return l.seats > 0; });
  var out = lists.filter(function (l) { return l.seats === 0; });

  /* ---------------------------------------------------------------- head */
  var info = e.info;
  var head =
    '<section class="e-head"><div class="bg-num" aria-hidden="true">' + esc(e.knesset) + '</div><div class="wrap">' +
    '<div class="crumbs"><a href="' + A.pageHref("index") + '">כל מערכות הבחירות</a></div>' +
    "<h1>" + esc(A.electionTitle(e)) + "</h1>" +
    '<p class="lede" style="margin-top:6px">' + esc(A.fmtDate(e.date)) + "</p>" +
    '<dl class="facts">' +
    "<div><dt>בעלי זכות בחירה</dt><dd>" + A.fmtInt(info.eligible) + "</dd></div>" +
    "<div><dt>קולות כשרים</dt><dd>" + A.fmtInt(info.valid) + ' <span class="small">(' + A.pctOf(info.valid, info.eligible) + " מבעלי זכות הבחירה)</span></dd></div>" +
    "<div><dt>אחוז החסימה</dt><dd>" + esc(info.threshold.replace(/\s*\(.*\)/, "")) + "</dd></div>" +
    "<div><dt>רשימות שהתמודדו</dt><dd>" + (e.lists.length + e.small.length) + "</dd></div>" +
    "<div><dt>הממשלה שהוקמה</dt><dd>" + (e.government ? esc(e.government.name) + ", " + esc(A.fmtDate(e.government.date)) : "לא הוקמה ממשלה; נקבעו בחירות חוזרות") + "</dd></div>" +
    "</dl>" +
    '<div class="leaders" style="--n:' + inK.length + '">' + inK.map(function (l) {
      return '<a href="' + A.partyHref(key, l.id) + '" style="--pc:' + A.partyColor(l) + '">' + A.portrait(l.leader, A.partyColor(l)) +
        '<span class="row"><span><span class="nm">' + esc(A.displayName(l.leader)) + '</span><br><span class="party">' + esc(l.name) + '</span></span><span class="seats">' + l.seats + "</span></span></a>";
    }).join("") + "</div>" +
    '<nav class="e-switch" aria-label="מערכות בחירות אחרות">' + A.ELECTIONS.map(function (x) {
      return '<a href="' + A.electionHref(x.key) + '"' + (x.key === key ? ' aria-current="page"' : "") + ">" + esc(A.shortWhen(x)) + "</a>";
    }).join("") + "</nav></div></section>";

  /* ---------------------------------------------------------------- seat map */
  var order = A.seatingOrder(e.lists);
  var legend = order.slice().reverse().map(function (l) {
    return '<li><a href="' + A.partyHref(key, l.id) + '" data-id="' + esc(l.id) + '"><span class="sw' + (l.bloc === "C" ? "" : " opp") + '" style="--pc:' + A.partyColor(l) + '"></span>' +
      "<span>" + esc(l.name) + ' <span class="small">' + esc(e.blocLabels[l.bloc]) + '</span></span><span class="n">' + l.seats + "</span></a></li>";
  }).join("");
  var parl =
    '<section class="block"><div class="wrap"><header><h2>הכנסת שנבחרה</h2><p>כל עיגול הוא מושב. הרשימות מסודרות משמאל לימין לפי המיקום הפוליטי שלהן</p></header>' +
    '<div class="parl"><figure><div class="toggle" role="group" aria-label="צביעת המושבים">' +
    '<button type="button" aria-pressed="true" data-mode="position">לפי ימין-שמאל</button>' +
    '<button type="button" aria-pressed="false" data-mode="bloc">' + (e.kind === "rec" ? "לפי ההמלצות לנשיא" : "לפי קואליציה ואופוזיציה") + "</button></div>" +
    '<div data-hemi>' + A.hemicycle(e) + "</div>" +
    '<figcaption class="axis-note">המיקום הפוליטי לקוח מתיבת המידע של כל רשימה בוויקיפדיה האנגלית. רשימה בלי מיקום במקור מוצגת באפור, בקצה השמאלי של הקשת.' +
    " בתצוגה השנייה המושבים מקובצים לפי גוש (" + esc(e.blocLabels.C) + " מימין), ובתוך כל גוש לפי המיקום הפוליטי." +
    (e.kind === "rec" ? " במערכת זו לא הוקמה ממשלה, ולכן החלוקה השנייה היא לפי ההמלצות לנשיא." : "") + "</figcaption></figure>" +
    '<div><ul class="seat-legend">' + legend + "</ul>" +
    '<p class="small" style="margin-top:10px">עיגול מלא בצבע: ' + esc(e.blocLabels.C) + ". עיגול עם טבעת: " + esc(e.blocLabels.O) + (e.blocOrder.indexOf("N") >= 0 ? " או " + esc(e.blocLabels.N) : "") + ".</p></div>" +
    "</div></div></section>";

  /* ---------------------------------------------------------------- lists table */
  function row(l) {
    var p = l.polls ? l.polls.overall : null;
    var diff = p != null ? Math.round((l.seats - p) * 10) / 10 : null;
    return "<tr" + (l.seats ? "" : ' class="below"') + '><td><a class="rowlink party-cell" href="' + A.partyHref(key, l.id) + '">' + A.slip(l, "sm") + "<span>" + esc(l.name) + "</span></a></td>" +
      "<td>" + esc(A.displayName(l.leader)) + '</td><td class="n"><b>' + l.seats + '</b></td><td class="n">' + A.fmtInt(l.votes) + '</td><td class="n">' + esc(l.pct) + "</td>" +
      '<td class="n">' + A.fmtSeats(p) + '</td><td class="n">' + A.fmtSeats(l.exitAvg) + "</td>" +
      '<td class="n ' + (diff == null ? "" : diff > 0 ? "delta-pos" : diff < 0 ? "delta-neg" : "") + '">' + (diff == null ? "—" : '<span dir="ltr">' + (diff > 0 ? "+" : diff < 0 ? "−" : "") + A.fmtSeats(Math.abs(diff)) + "</span>") + "</td>" +
      "<td>" + A.blocChip(e, l.bloc) + "</td></tr>";
  }
  var table =
    '<section class="block"><div class="wrap"><header><h2>הרשימות</h2><p>לחיצה על רשימה פותחת את תעודת הזהות שלה במערכת זו</p></header>' +
    '<div class="table-scroll"><table class="data"><thead><tr><th>רשימה</th><th>ראש הרשימה</th><th class="n">מושבים</th><th class="n">קולות</th><th class="n">אחוז</th>' +
    '<th class="n">ממוצע הסקרים</th><th class="n">ממוצע המדגמים</th><th class="n">תוצאה מול סקרים</th><th>גוש</th></tr></thead><tbody>' +
    inK.map(row).join("") +
    (out.length ? '<tr><td colspan="9" class="small" style="background:#f7f8fa">מתחת לאחוז החסימה (' + esc(info.threshold.replace(/\s*\(.*\)/, "")) + ")</td></tr>" + out.map(row).join("") : "") +
    "</tbody></table></div>" +
    '<p class="small" style="margin-top:6px">ממוצע הסקרים מוצג לרשימות שנסקרו לאורך החלון; “תוצאה מול סקרים” = המושבים בפועל פחות ממוצע הסקרים.</p>' +
    (e.small.length ? '<details class="more"><summary>עוד ' + e.small.length + " רשימות שהתמודדו ולא עברו את אחוז החסימה</summary>" +
      '<div class="table-scroll" style="margin-top:8px"><table class="data"><thead><tr><th>אותיות</th><th>שם הרשימה בפתק</th><th>ראש הרשימה</th><th class="n">קולות</th><th class="n">אחוז</th></tr></thead><tbody>' +
      e.small.map(function (s) {
        return "<tr><td><b>" + esc(s.letters) + '</b></td><td class="wrapcell">' + esc(s.name) + "</td><td>" + esc(s.leader) + '</td><td class="n">' + A.fmtInt(s.votes) + '</td><td class="n">' + esc(s.pct) + "</td></tr>";
      }).join("") + "</tbody></table></div></details>" : "") +
    "</div></section>";

  /* ---------------------------------------------------------------- blocs */
  var blocs =
    '<section class="block"><div class="wrap"><header><h2>' + (e.kind === "rec" ? "גושי ההמלצות: סקרים, מדגמים ותוצאה" : "קואליציה ואופוזיציה: סקרים, מדגמים ותוצאה") + "</h2>" +
    "<p>" + (e.kind === "rec" ? "לפי ההמלצות לנשיא אחרי הבחירות" : "לפי הרכב " + esc(e.government.name) + " בהשבעתה") + "</p></header>" +
    A.blocLegend(e) +
    '<div class="bars" style="max-width:820px">' +
    [["סקרים", e.blocs.polls], ["מדגמים", e.blocs.exit], ["תוצאה", e.blocs.final]].map(function (r) {
      return '<div class="bar-wrap"><span class="bar-label">' + r[0] + "</span>" + A.blocBar(e, r[1]) + "</div>";
    }).join("") + "</div>" +
    '<div class="table-scroll" style="margin-top:16px;max-width:820px"><table class="data"><thead><tr><th></th>' +
    e.blocOrder.map(function (b) { return '<th class="n">' + esc(e.blocLabels[b]) + "</th>"; }).join("") + "</tr></thead><tbody>" +
    [["ממוצע הסקרים (" + e.blocs.pollsUsed + " סקרים)", e.blocs.polls], ["ממוצע המדגמים", e.blocs.exit], ["תוצאה", e.blocs.final]].map(function (r) {
      return "<tr><td>" + r[0] + "</td>" + e.blocOrder.map(function (b) { return '<td class="n">' + A.fmtSeats(r[1][b]) + "</td>"; }).join("") + "</tr>";
    }).join("") + "</tbody></table></div>" +
    '<p class="small" style="margin-top:6px">ממוצע הסקרים: סכום הגוש בכל סקר, ממוצע לכל גוף, ואז ממוצע הגופים; רק סקרים שמסתכמים ב-120. ' +
    "“לא נכנסו לכנסת” = מנדטים שהסקרים והמדגמים נתנו לרשימות שבסוף לא עברו את אחוז החסימה.</p>" +
    (lists.some(function (l) { return l.blocNote; }) ? '<ul class="notes" style="margin-top:10px">' + lists.filter(function (l) { return l.blocNote; }).map(function (l) {
      return "<li><b>" + esc(l.name) + ":</b> " + esc(l.blocNote) + "</li>";
    }).join("") + "</ul>" : "") +
    "</div></section>";

  /* ---------------------------------------------------------------- recommendations */
  var groups = {};
  inK.forEach(function (l) { (groups[l.rec] = groups[l.rec] || []).push(l); });
  var recOrder = Object.keys(groups).sort(function (a, b) {
    if (a === "-") return 1; if (b === "-") return -1;
    var sa = groups[a].reduce(function (s, l) { return s + l.seats; }, 0), sb = groups[b].reduce(function (s, l) { return s + l.seats; }, 0);
    return sb - sa;
  });
  var recs =
    '<section class="block"><div class="wrap"><header><h2>ההמלצות לנשיא</h2><p>על מי המליצה כל רשימה להטיל את הרכבת הממשלה</p></header>' +
    '<div class="rec-groups">' + recOrder.map(function (r) {
      var seats = groups[r].reduce(function (s, l) { return s + l.seats; }, 0);
      return '<div class="rec-group"><h3><span>' + esc(r === "-" ? "לא המליצו על אף מועמד" : (A.META.candidates || {})[r]) + '</span><span class="n">' + seats + "</span></h3><ul>" +
        groups[r].map(function (l) { return '<li><a href="' + A.partyHref(key, l.id) + '" class="chip" style="text-decoration:none">' + esc(l.name) + " " + l.seats + "</a></li>"; }).join("") +
        "</ul></div>";
    }).join("") + "</div>" +
    (inK.some(function (l) { return l.recNote; }) ? '<ul class="notes" style="margin-top:10px">' + inK.filter(function (l) { return l.recNote; }).map(function (l) {
      return "<li><b>" + esc(l.name) + ":</b> " + esc(l.recNote) + "</li>";
    }).join("") + "</ul>" : "") +
    (e.recNote ? '<p class="small" style="margin-top:8px">' + esc(e.recNote) + "</p>" : "") +
    '<p class="small"><a href="' + esc(e.recSrc) + '" target="_blank" rel="noopener">מקור ההמלצות</a></p>' +
    "</div></section>";

  /* ---------------------------------------------------------------- polls teaser */
  var polls =
    '<section class="block"><div class="wrap"><header><h2>מה אמרו הסקרים</h2><p>ממוצע שלושת החודשים האחרונים לפי גוף, מול המדגמים והתוצאה</p></header>' +
    '<div data-polls-summary></div>' +
    '<p style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap"><button class="btn" type="button" data-open-polls>פתיחת חלונית הסקרים</button>' +
    '<a class="btn ghost" href="' + A.pollsHref(key) + '">לארכיון הסקרים</a></p></div></section>';

  /* ---------------------------------------------------------------- sources */
  var sources =
    '<section class="block"><div class="wrap"><header><h2>מקורות והערות</h2></header>' +
    '<div class="two-col"><div><h3 style="margin-bottom:8px">פרסומים רשמיים</h3><div class="sources">' +
    e.links.map(function (l) { return '<a href="' + esc(l.url) + '" target="_blank" rel="noopener">' + esc(l.label) + "</a>"; }).join("") + "</div>" +
    '<h3 style="margin:16px 0 8px">עוד מקורות</h3><div class="sources">' +
    '<a href="' + esc(e.heWiki) + '" target="_blank" rel="noopener">הערך על הבחירות בוויקיפדיה העברית (תוצאות, אותיות, ראשי רשימות)</a>' +
    '<a href="' + esc(e.resultsSrc) + '" target="_blank" rel="noopener">הערך על הבחירות בוויקיפדיה האנגלית</a>' +
    '<a href="' + esc(e.govSrc) + '" target="_blank" rel="noopener">הרכב הממשלה / ההמלצות</a>' +
    '<a href="' + esc(e.pollSrc) + '" target="_blank" rel="noopener">טבלאות הסקרים</a></div></div>' +
    '<div><h3 style="margin-bottom:8px">הערות</h3><ul class="notes">' + e.notes.map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("") + "</ul></div></div>" +
    "</div></section>";

  main.innerHTML = head + parl + table + blocs + recs + polls + sources;

  /* ---------------------------------------------------------------- behaviour */
  var hemi = main.querySelector("[data-hemi]");
  var mode = "position";
  main.querySelectorAll(".toggle button").forEach(function (b) {
    b.addEventListener("click", function () {
      mode = b.getAttribute("data-mode");
      main.querySelectorAll(".toggle button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      hemi.innerHTML = A.hemicycle(e, { mode: mode });
      wireSeats();
    });
  });
  function highlight(id) {
    hemi.querySelectorAll(".seat").forEach(function (s) { s.classList.toggle("dim", !!id && s.getAttribute("data-id") !== id); });
  }
  function wireSeats() {
    hemi.querySelectorAll(".seat").forEach(function (s) {
      s.style.cursor = "pointer";
      s.addEventListener("mouseenter", function () { highlight(s.getAttribute("data-id")); });
      s.addEventListener("mouseleave", function () { highlight(null); });
      s.addEventListener("click", function () { location.href = A.partyHref(key, s.getAttribute("data-id")); });
    });
  }
  wireSeats();
  main.querySelectorAll(".seat-legend a").forEach(function (a) {
    a.addEventListener("mouseenter", function () { highlight(a.getAttribute("data-id")); });
    a.addEventListener("focus", function () { highlight(a.getAttribute("data-id")); });
    a.addEventListener("mouseleave", function () { highlight(null); });
    a.addEventListener("blur", function () { highlight(null); });
  });

  // compact outlet table inside the page; the full material is in the drawer
  var sumEl = main.querySelector("[data-polls-summary]");
  var tracked = e.tracked.map(function (n) { return e.lists.filter(function (l) { return l.name === n; })[0]; }).filter(Boolean)
    .sort(function (a, b) { return b.seats - a.seats; });
  var os = Object.keys(A.META.outlets).filter(function (o) { return tracked.some(function (l) { return l.polls && l.polls.outlets[o] && l.polls.outlets[o].n; }); });
  sumEl.innerHTML = '<div class="table-scroll"><table class="data"><thead><tr><th>רשימה</th>' +
    os.map(function (o) { return '<th class="n">' + esc(window.PollsView.outletName(e, o)) + "</th>"; }).join("") +
    '<th class="n">ממוצע הגופים</th><th class="n">מדגמים</th><th class="n">תוצאה</th></tr></thead><tbody>' +
    tracked.map(function (l) {
      return '<tr><td><a class="rowlink party-cell" href="' + A.partyHref(key, l.id) + '">' + A.slip(l, "sm") + esc(l.name) + "</a></td>" +
        os.map(function (o) { var d = l.polls.outlets[o]; return '<td class="n">' + (d && d.n ? A.fmtSeats(d.mean) : "—") + "</td>"; }).join("") +
        '<td class="n"><b>' + A.fmtSeats(l.polls.overall) + '</b></td><td class="n">' + A.fmtSeats(l.exitAvg) + '</td><td class="n"><b>' + l.seats + "</b></td></tr>";
    }).join("") + "</tbody></table></div>";
  main.querySelector("[data-open-polls]").addEventListener("click", function () { window.PollsView.open(key); });

  /* ================================================================ before election day */
  function upcoming() {
    var lists = e.lists.slice().sort(function (a, b) { return b.polls.overall - a.polls.overall; });
    var os = Object.keys(A.META.outlets).filter(function (o) { return lists.some(function (l) { return l.polls.outlets[o] && l.polls.outlets[o].n; }); });
    var nPolls = (window.POLLS || []).filter(function (p) { return p.e === key; }).length;
    var days = Math.round((A.parseISO(e.date) - A.parseISO(new Date().toISOString().slice(0, 10))) / 864e5);
    var when = days > 1 ? "בעוד " + days + " ימים" : days === 1 ? "מחר" : days === 0 ? "היום" : "הבחירות התקיימו; התוצאות עוד לא נוספו לאתר";
    var maxAvg = 1;   // scale: the largest outlet mean, so every tick stays on the track
    lists.forEach(function (l) { Object.keys(l.polls.outlets).forEach(function (o) { var d = l.polls.outlets[o]; if (d && d.n) maxAvg = Math.max(maxAvg, d.mean); }); });

    var head =
      '<section class="e-head"><div class="bg-num" aria-hidden="true">' + esc(e.knesset) + '</div><div class="wrap">' +
      '<div class="crumbs"><a href="' + A.pageHref("index") + '">כל מערכות הבחירות</a></div>' +
      '<p class="up-tag"><span class="chip pre">לפני הבחירות</span> <span class="small">עודכן ב-' + esc(A.fmtDate(e.asOf)) + ", הסקר האחרון: " + esc(A.fmtDate(e.lastPoll)) + "</span></p>" +
      "<h1>" + esc(A.electionTitle(e)) + "</h1>" +
      '<p class="lede" style="margin-top:6px">' + esc(A.fmtDate(e.date)) + " · " + esc(when) + "</p>" +
      '<dl class="facts">' +
      "<div><dt>רשימות שהגישו מועמדים</dt><dd>" + (e.lists.length + e.small.length) + "</dd></div>" +
      "<div><dt>רשימות במעקב הסקרים</dt><dd>" + e.lists.length + "</dd></div>" +
      "<div><dt>סקרים בחלון</dt><dd>" + nPolls + ' <span class="small">(מ-' + esc(A.fmtDate(e.windowStart, { day: "numeric", month: "long" })) + ")</span></dd></div>" +
      "<div><dt>הממשלה היוצאת</dt><dd>" + esc(e.outgoing.name) + "</dd></div>" +
      "</dl>" +
      '<div class="leaders" style="--n:' + Math.min(lists.length, 8) + '">' + lists.slice(0, 8).map(function (l) {
        return '<a href="' + A.partyHref(key, l.id) + '" style="--pc:' + A.partyColor(l) + '">' + A.portrait(l.leader, A.partyColor(l)) +
          '<span class="row"><span><span class="nm">' + esc(A.displayName(l.leader)) + '</span><br><span class="party">' + esc(l.name) + '</span></span><span class="seats">' + A.fmtSeats(Math.round(l.polls.overall * 10) / 10) + "</span></span></a>";
      }).join("") + "</div>" +
      '<p class="small" style="margin-top:8px">המספר ליד כל ראש רשימה: ממוצע הסקרים (מושבים).</p>' +
      '<nav class="e-switch" aria-label="מערכות בחירות אחרות">' + A.ELECTIONS.map(function (x) {
        return '<a href="' + A.electionHref(x.key) + '"' + (x.key === key ? ' aria-current="page"' : "") + ">" + esc(A.shortWhen(x)) + "</a>";
      }).join("") + "</nav></div></section>";

    var avg =
      '<section class="block"><div class="wrap"><header><h2>ממוצע הסקרים</h2><p>ממוצע הגופים לכל רשימה; הסימנים הקטנים הם הממוצע של כל גוף בנפרד</p></header>' +
      '<div class="avg-bars">' + lists.map(function (l) {
        var ticks = os.map(function (o) {
          var d = l.polls.outlets[o];
          if (!d || !d.n) return "";
          return '<i style="inset-inline-start:' + (100 * d.mean / maxAvg).toFixed(2) + '%" title="' + esc(window.PollsView.outletName(e, o) + ": " + A.fmtSeats(d.mean) + " (" + d.n + " סקרים)") + '"></i>';
        }).join("");
        return '<a class="avg-row" href="' + A.partyHref(key, l.id) + '" style="--pc:' + A.partyColor(l) + '">' + A.slip(l, "sm") +
          '<span class="nm">' + esc(l.name) + '<span class="small">' + esc(A.displayName(l.leader)) + "</span></span>" +
          '<span class="track"><span class="fill" style="width:' + (100 * l.polls.overall / maxAvg).toFixed(2) + '%"></span>' + ticks + "</span>" +
          '<span class="v">' + A.fmtSeats(Math.round(l.polls.overall * 10) / 10) + "</span></a>";
      }).join("") + "</div>" +
      '<p class="small" style="margin-top:8px">רשימה מתחת לאחוז החסימה בסקר נספרת כ-0 מושבים. לכן ממוצע נמוך מ-4 אינו תחזית למספר מושבים, אלא סימן שבחלק מהסקרים הרשימה לא עברה את אחוז החסימה.</p>' +
      "</div></section>";

    var table =
      '<section class="block"><div class="wrap"><header><h2>הרשימות</h2><p>לחיצה על רשימה פותחת את תעודת הזהות שלה: אותיות, מועמדים, מיקום פוליטי וסקרים</p></header>' +
      '<div class="table-scroll"><table class="data"><thead><tr><th>רשימה</th><th>ראש הרשימה</th>' +
      os.map(function (o) { return '<th class="n">' + esc(window.PollsView.outletName(e, o)) + "</th>"; }).join("") +
      '<th class="n">ממוצע הגופים</th><th>גוש</th></tr></thead><tbody>' +
      lists.map(function (l) {
        return '<tr><td><a class="rowlink party-cell" href="' + A.partyHref(key, l.id) + '">' + A.slip(l, "sm") + "<span>" + esc(l.name) + "</span></a></td><td>" + esc(A.displayName(l.leader)) + "</td>" +
          os.map(function (o) { var d = l.polls.outlets[o]; return '<td class="n">' + (d && d.n ? A.fmtSeats(d.mean) + ' <span class="small">(' + d.n + ")</span>" : "—") + "</td>"; }).join("") +
          '<td class="n"><b>' + A.fmtSeats(l.polls.overall) + "</b></td><td>" + A.blocChip(e, l.bloc) + "</td></tr>";
      }).join("") + "</tbody></table></div>" +
      '<p class="small" style="margin-top:6px">בסוגריים: מספר הסקרים של הגוף שבהם הרשימה הופיעה. ממוצע הגופים = ממוצע של ממוצעי הגופים.</p>' +
      (e.small.length ? '<details class="more"><summary>עוד ' + e.small.length + " רשימות שהגישו מועמדים ואינן בטבלת הסקרים</summary>" +
        '<div class="table-scroll" style="margin-top:8px"><table class="data"><thead><tr><th>אותיות</th><th>שם הרשימה</th><th>ראש הרשימה</th></tr></thead><tbody>' +
        e.small.map(function (x) { return "<tr><td><b>" + esc(x.letters) + "</b></td><td>" + esc(x.name) + "</td><td>" + esc(x.leader || "—") + "</td></tr>"; }).join("") +
        "</tbody></table></div></details>" : "") +
      "</div></section>";

    var C = e.blocs.polls.C, O = e.blocs.polls.O;
    var blocs =
      '<section class="block"><div class="wrap"><header><h2>' + esc(e.blocLabels.C) + " מול " + esc(e.blocLabels.O) + "</h2><p>" +
      "מפלגות " + esc(e.outgoing.name) + " מול כל שאר הרשימות, בממוצע הסקרים</p></header>" +
      '<div class="up-blocs"><div class="side C"><span class="big">' + A.fmtSeats(C) + "</span><span>" + esc(e.blocLabels.C) + "</span></div>" +
      '<div class="co-bar" aria-hidden="true"><span style="width:' + (100 * C / 120).toFixed(2) + '%;--pc:var(--coal)"></span><span style="width:' + (100 * O / 120).toFixed(2) + '%;--pc:var(--opp)"></span><i class="line" style="inset-inline-start:' + (100 * 61 / 120).toFixed(3) + '%"></i></div>' +
      '<div class="side O"><span class="big">' + A.fmtSeats(O) + "</span><span>" + esc(e.blocLabels.O) + "</span></div></div>" +
      '<div class="table-scroll" style="margin-top:16px;max-width:620px"><table class="data"><thead><tr><th>גוף</th>' +
      e.blocOrder.map(function (b) { return '<th class="n">' + esc(e.blocLabels[b]) + "</th>"; }).join("") + '<th class="n">סקרים</th></tr></thead><tbody>' +
      Object.keys(e.blocs.pollsByOutlet).map(function (o) {
        var d = e.blocs.pollsByOutlet[o];
        return "<tr><td>" + esc(window.PollsView.outletName(e, o)) + "</td>" + e.blocOrder.map(function (b) { return '<td class="n">' + A.fmtSeats(d[b]) + "</td>"; }).join("") + '<td class="n">' + d.n + "</td></tr>";
      }).join("") +
      "<tr><td><b>ממוצע הגופים</b></td>" + e.blocOrder.map(function (b) { return '<td class="n"><b>' + A.fmtSeats(e.blocs.polls[b]) + "</b></td>"; }).join("") + '<td class="n">' + e.blocs.pollsUsed + "</td></tr>" +
      "</tbody></table></div>" +
      '<p class="small" style="margin-top:6px">הקו באמצע הפס: 61 מושבים. רק סקרים שמסתכמים ב-120. ' + esc(e.blocLabels.C) + ": " + esc(lists.filter(function (l) { return l.bloc === "C"; }).map(function (l) { return l.name; }).join(", ")) + ". " +
      'אפשר לנסות צירופים אחרים ב<a href="' + A.pageHref("coalition", "e=" + encodeURIComponent(key) + "&m=polls") + '">בונה הקואליציות</a>.</p>' +
      "</div></section>";

    var polls =
      '<section class="block"><div class="wrap"><header><h2>כל הסקרים</h2><p>כל סקר בחלון, לפי גוף, עם קישור לפרסום</p></header>' +
      '<p style="display:flex;gap:10px;flex-wrap:wrap"><button class="btn" type="button" data-open-polls>פתיחת חלונית הסקרים</button>' +
      '<a class="btn ghost" href="' + A.pollsHref(key) + '">לארכיון הסקרים</a></p></div></section>';

    var sources =
      '<section class="block"><div class="wrap"><header><h2>מקורות והערות</h2></header>' +
      '<div class="two-col"><div><h3 style="margin-bottom:8px">פרסומים רשמיים</h3><div class="sources">' +
      e.links.map(function (l) { return '<a href="' + esc(l.url) + '" target="_blank" rel="noopener">' + esc(l.label) + "</a>"; }).join("") + "</div>" +
      '<h3 style="margin:16px 0 8px">עוד מקורות</h3><div class="sources">' +
      '<a href="' + esc(e.heWiki) + '" target="_blank" rel="noopener">הערך על הבחירות בוויקיפדיה העברית (רשימות, אותיות, מועמדים)</a>' +
      '<a href="' + esc(e.enWiki) + '" target="_blank" rel="noopener">הערך על הבחירות בוויקיפדיה האנגלית</a>' +
      '<a href="' + esc(e.outgoing.src) + '" target="_blank" rel="noopener">' + esc(e.outgoing.name) + " (הממשלה היוצאת)</a>" +
      '<a href="' + esc(e.pollSrc) + '" target="_blank" rel="noopener">טבלאות הסקרים</a></div></div>' +
      '<div><h3 style="margin-bottom:8px">הערות</h3><ul class="notes">' + e.notes.map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("") + "</ul></div></div>" +
      "</div></section>";

    main.innerHTML = head + avg + table + blocs + polls + sources;
    main.querySelector("[data-open-polls]").addEventListener("click", function () { window.PollsView.open(key); });
  }
})();
