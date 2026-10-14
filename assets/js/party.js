/* A list's "ID card" for one election. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc;
  A.mount("home");
  var main = document.getElementById("main");
  var key = A.qs("e"), id = A.qs("p");
  var e = A.byKey[key];
  var l = e && e.lists.filter(function (x) { return x.id === id; })[0];
  if (!l) { A.notFound(main, "לא נמצאה רשימה כזו במערכת הבחירות הזו."); return; }
  var color = A.partyColor(l);
  document.title = l.name + ", " + A.shortWhen(e) + " | היסטוריית הסקרים של ישראל";

  var official = e.links.filter(function (x) { return /רשימות המועמדים/.test(x.label); })[0];

  /* ---------------------------------------------------------------- axis */
  function axis(pos) {
    var W = 560, H = 74, m = 34, step = (W - 2 * m) / 6;
    function x(v) { return m + (v + 3) * step; }
    var g = ['<line x1="' + m + '" x2="' + (W - m) + '" y1="26" y2="26" stroke="#d8dce4" stroke-width="6" stroke-linecap="round"/>'];
    for (var v = -3; v <= 3; v++) {
      g.push('<line x1="' + x(v) + '" x2="' + x(v) + '" y1="19" y2="33" stroke="#b9bfcc"/>');
      g.push('<text x="' + x(v) + '" y="58" font-size="11.5" text-anchor="middle" fill="#4a5268">' + esc(A.AXIS_HE[String(v)]) + "</text>");
    }
    if (pos.lo != null) {
      if (pos.lo === pos.hi) g.push('<circle cx="' + x(pos.lo) + '" cy="26" r="10" fill="' + color + '" stroke="#fff" stroke-width="3"/>');
      else g.push('<line x1="' + x(pos.lo) + '" x2="' + x(pos.hi) + '" y1="26" y2="26" stroke="' + color + '" stroke-width="16" stroke-linecap="round"/>');
    }
    return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="מיקום פוליטי: ' + esc(pos.he) + '" direction="ltr">' + g.join("") + "</svg>";
  }

  /* ---------------------------------------------------------------- numbers */
  var f = [];
  if (e.upcoming) {
    f.push(["ממוצע הסקרים", '<dd class="big">' + A.fmtSeats(Math.round(l.polls.overall * 10) / 10) + "</dd>"]);
    f.push(["ראש הרשימה", "<dd>" + esc(A.displayName(l.leader)) + "</dd>"]);
    f.push(["גוש לפני הבחירות", "<dd>" + A.blocChip(e, l.bloc) + "</dd>"]);
    f.push(["מועמדים ברשימה (בוויקיפדיה)", "<dd>" + l.candidates.length + "</dd>"]);
  } else {
  f.push(["מושבים", '<dd class="big">' + l.seats + "</dd>"]);
  f.push(["קולות", "<dd>" + A.fmtInt(l.votes) + "</dd>"]);
  f.push(["אחוז מהקולות הכשרים", "<dd>" + esc(l.pct) + "</dd>"]);
  f.push(["ראש הרשימה", "<dd>" + esc(A.displayName(l.leader)) + "</dd>"]);
  f.push(["מעמד אחרי הבחירות", "<dd>" + A.blocChip(e, l.bloc) + "</dd>"]);
  f.push(["המלצה לנשיא", "<dd>" + esc(A.recText(l)) + "</dd>"]);
  f.push(["ממוצע הסקרים", "<dd>" + (l.polls ? A.fmtSeats(l.polls.overall) : "—") + "</dd>"]);
  f.push(["ממוצע המדגמים", "<dd>" + A.fmtSeats(l.exitAvg) + "</dd>"]);
  }

  var card =
    '<section class="id-wrap"><div class="wrap">' +
    '<div class="crumbs"><a href="' + A.pageHref("index") + '">כל מערכות הבחירות</a> / <a href="' + A.electionHref(key) + '">' + esc(A.electionTitle(e)) + ", " + esc(A.shortWhen(e)) + "</a></div>" +
    '<article class="idcard" style="--pc:' + color + '">' +
    '<div class="face">' + A.slip(l, "xl") + '<div class="ballot-name">' + esc(l.ballot) + "</div></div>" +
    "<div><h1>" + esc(l.name) + '</h1><p class="sub">תעודת זהות, ' + esc(A.electionTitle(e)) + " (" + esc(A.fmtDate(e.date)) + ")" +
    (e.upcoming ? ' <span class="chip pre">לפני הבחירות</span> <span class="small">עודכן ב-' + esc(A.fmtDate(e.asOf)) + "</span>" : "") + "</p>" +
    '<dl class="fields">' + f.map(function (x) { return "<div><dt>" + x[0] + "</dt>" + x[1] + "</div>"; }).join("") + "</dl>" +
    '<div class="axis"><div class="cap" style="margin-bottom:6px"><b>מיקום פוליטי:</b> ' + esc(l.position.he) +
    (l.position.en ? ' <span class="small" dir="ltr">(“' + esc(l.position.en) + '”)</span>' : "") + "</div>" + axis(l.position) +
    '<p class="small" style="margin-top:4px">' + (l.position.url ? 'מקור: <a href="' + esc(l.position.url) + '" target="_blank" rel="noopener">תיבת המידע של ' + esc(l.position.article) + " בוויקיפדיה האנגלית</a>. " : "") +
    (l.position.url ? "התיאור לקוח מהערך הכללי על המפלגה או הברית, ואינו ספציפי למערכת זו." : "") + (l.position.note ? " " + esc(l.position.note) : "") + "</p></div>" +
    "</div>" +
    '<div class="leader">' + A.portrait(l.leader, color) + '<span class="role">ראש הרשימה</span><span class="name">' + esc(A.displayName(l.leader)) + "</span>" +
    ((A.PEOPLE[l.leader] || {}).wiki ? '<a class="small" href="' + esc(A.PEOPLE[l.leader].wiki) + '" target="_blank" rel="noopener">בוויקיפדיה</a>' : "") + "</div>" +
    "</article></div></section>";

  /* ---------------------------------------------------------------- members */
  var members;
  if (e.upcoming) {
    members =
      '<section class="block"><div class="wrap"><header><h2>המועמדים</h2><p>לפי הסדר ברשימה, כפי שמופיע בוויקיפדיה העברית (' + l.candidates.length + " המקומות הראשונים)</p></header>" +
      '<div class="members">' + l.candidates.map(function (m, i) {
        var p = A.PEOPLE[m] || {};
        var inner = A.portrait(m, color) + '<span class="nm">' + esc(A.displayName(m)) + '</span><span class="tag">מקום ' + (i + 1) + (i === 0 ? ", ראש הרשימה" : "") + "</span>";
        return p.wiki ? '<a class="member' + (i === 0 ? " lead" : "") + '" style="--pc:' + color + '" href="' + esc(p.wiki) + '" target="_blank" rel="noopener">' + inner + "</a>" :
          '<span class="member' + (i === 0 ? " lead" : "") + '" style="--pc:' + color + '">' + inner + "</span>";
      }).join("") + "</div>" +
      '<p class="small" style="margin-top:14px">מועמדים בלי ערך בוויקיפדיה העברית מוצגים בלי קישור ובלי תמונה.' +
      (official ? ' לרשימה המלאה: <a href="' + esc(official.url) + '" target="_blank" rel="noopener">' + esc(official.label) + "</a>." : "") + "</p>" +
      "</div></section>";
  } else if (l.seats) {
    members =
      '<section class="block"><div class="wrap"><header><h2>נבחרי הרשימה</h2><p>' + l.seats + " חברי הכנסת שנכנסו מהרשימה בתחילת הכנסת ה-" + esc(e.knesset) + "</p></header>" +
      '<div class="members">' + l.members.map(function (m, i) {
        var p = A.PEOPLE[m] || {};
        var note = l.memberNotes && l.memberNotes[m];
        return '<a class="member' + (i === 0 ? " lead" : "") + '" style="--pc:' + color + '" href="' + esc(p.wiki || "#") + '" target="_blank" rel="noopener">' +
          A.portrait(m, color) + '<span class="nm">' + esc(A.displayName(m)) + "</span>" +
          (i === 0 ? '<span class="tag">ראש הרשימה</span>' : "") + (note ? '<span class="tag">' + esc(note) + "</span>" : "") + "</a>";
      }).join("") + "</div>" +
      '<p class="small" style="margin-top:14px">ראש הרשימה ראשון; שאר הנבחרים לפי סדר הסיעות בכנסת, שאינו בהכרח המקום ברשימה. ' +
      "חברי כנסת שנכנסו מאוחר יותר (במקום מתפטרים או בחוק הנורבגי) אינם מוצגים." +
      (official ? ' לסדר המלא ולכל המועמדים: <a href="' + esc(official.url) + '" target="_blank" rel="noopener">' + esc(official.label) + "</a>." : "") + "</p>" +
      "</div></section>";
  } else {
    members =
      '<section class="block"><div class="wrap"><header><h2>נבחרי הרשימה</h2></header>' +
      '<p class="lede">הרשימה לא עברה את אחוז החסימה (' + esc(e.info.threshold.replace(/\s*\(.*\)/, "")) + ") ולא נכנסה לכנסת.</p>" +
      (official ? '<p class="small"><a href="' + esc(official.url) + '" target="_blank" rel="noopener">' + esc(official.label) + "</a></p>" : "") +
      "</div></section>";
  }

  /* ---------------------------------------------------------------- in the polls */
  var rows = [], max = l.seats || 0;
  if (l.polls) {
    Object.keys(A.META.outlets).forEach(function (o) {
      var d = l.polls.outlets[o];
      if (d && d.n) { rows.push(["", window.PollsView.outletName(e, o) + " (" + d.n + ")", d.mean]); max = Math.max(max, d.mean); }
    });
    rows.push(["", "ממוצע הגופים", l.polls.overall]);
  }
  if (!e.upcoming) {
    rows.push(["sep"]);
    e.exitPolls.forEach(function (x) { var v = x.seats[l.name]; rows.push(["exit", "מדגם " + x.actual, v]); max = Math.max(max, v || 0); });
    rows.push(["exit", "ממוצע המדגמים", l.exitAvg]);
    rows.push(["sep"]);
    rows.push(["result", "תוצאה", l.seats]);
  }
  max = Math.max(max, 1);
  var bars = '<div class="mini-bars" style="--pc:' + color + '">' + rows.map(function (r) {
    if (r[0] === "sep") return '<div class="sep"></div>';
    return '<div class="row ' + r[0] + '"><span>' + esc(r[1]) + '</span><span class="track"><span class="fill" style="width:' + (100 * (r[2] || 0) / max).toFixed(2) + '%"></span></span><span class="v">' + A.fmtSeats(r[2]) + "</span></div>";
  }).join("") + "</div>";
  var pollsSec =
    '<section class="block"><div class="wrap"><header><h2>' + (e.upcoming ? "בסקרים" : "בסקרים ובמדגמים") + "</h2><p>" +
    (e.upcoming ? "ממוצע הסקרים בחלון עד תאריך העדכון, לפי גוף (בסוגריים: מספר הסקרים)" : "ממוצע שלושת החודשים האחרונים לפי גוף (בסוגריים: מספר הסקרים), מדגמי ליל הבחירות והתוצאה") + "</p></header>" +
    (l.polls ? "" : '<p class="small">הרשימה לא נכללה במעקב הסקרים של האתר (נסקרו רק הרשימות המרכזיות בכל מערכת), ולכן מוצגים רק המדגמים והתוצאה.</p>') +
    bars + '<p style="margin-top:16px"><button class="btn" type="button" data-open-polls>פתיחת חלונית הסקרים של מערכת זו</button></p></div></section>';

  /* ---------------------------------------------------------------- history */
  var others = A.ELECTIONS.map(function (x) {
    var m = x.lists.filter(function (y) { return y.id === l.id; })[0];
    return m ? [x, m] : null;
  }).filter(Boolean);
  var hist = others.length > 1 ?
    '<section class="block"><div class="wrap"><header><h2>אותה רשימה במערכות אחרות</h2><p>תעודת זהות נפרדת לכל מערכת בחירות</p></header><div class="history">' +
    others.map(function (pair) {
      var x = pair[0], m = pair[1];
      var s = x.upcoming ? A.fmtSeats(Math.round(m.polls.overall * 10) / 10) : m.seats;
      return '<a href="' + A.partyHref(x.key, m.id) + '"' + (x.key === key ? ' aria-current="page"' : "") + "><span>" + esc(A.shortWhen(x)) + '</span><span class="s">' + s + "</span>" +
        (x.upcoming ? '<span class="small">בסקרים</span>' : "") + '<span class="small">' + esc(A.displayName(m.leader)) + "</span></a>";
    }).join("") + "</div></div></section>" : "";

  /* ---------------------------------------------------------------- sources */
  var src =
    '<section class="block"><div class="wrap"><header><h2>מקורות</h2></header><div class="sources">' +
    '<a href="' + esc(l.heWiki) + '" target="_blank" rel="noopener">' + (e.upcoming ? "הפרק על הרשימה בערך על הבחירות (ויקיפדיה העברית)" : "הערך על הרשימה בוויקיפדיה העברית") + "</a>" +
    (l.position.url ? '<a href="' + esc(l.position.url) + '" target="_blank" rel="noopener">הערך בוויקיפדיה האנגלית (מיקום פוליטי)</a>' : "") +
    (e.upcoming ? '<a href="' + esc(e.pollSrc) + '" target="_blank" rel="noopener">טבלאות הסקרים (ויקיפדיה האנגלית)</a>' :
      '<a href="' + esc(e.heWiki) + '" target="_blank" rel="noopener">תוצאות הבחירות, אותיות וראש הרשימה (ויקיפדיה העברית)</a>' +
      '<a href="' + esc(e.govSrc) + '" target="_blank" rel="noopener">הרכב הממשלה / ההמלצות</a>') +
    (official ? '<a href="' + esc(official.url) + '" target="_blank" rel="noopener">' + esc(official.label) + "</a>" : "") +
    "</div>" + (l.blocNote ? '<p class="small" style="margin-top:10px"><b>הערה על השיוך לגוש:</b> ' + esc(l.blocNote) + "</p>" : "") +
    (l.recNote ? '<p class="small"><b>הערה על ההמלצה:</b> ' + esc(l.recNote) + "</p>" : "") + "</div></section>";

  main.innerHTML = card + members + pollsSec + hist + src;
  main.querySelector("[data-open-polls]").addEventListener("click", function () { window.PollsView.open(key); });
})();
