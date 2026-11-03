/* The political compass: one question per indicator of the axis map (data/axes.js -> compass),
   matched against the scores of the 2026 lists. Nothing is sent or stored; the answers can be
   kept in the address (?a=...) so a result can be shared. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc, V = window.AxesView;
  A.mount("compass");
  var main = document.getElementById("main");
  if (!V || !V.AX.compass) { A.notFound(main, "נתוני המצפן לא נטענו."); return; }
  var AX = V.AX, Q = AX.compass.questions, N = Q.length, AT = AX.anchorsAt;
  var e = A.byKey[AX.election];
  var MIN_ANSWERS = 3;     // fewer answers = no result
  var MIN_COVER = 0.5;     // a list enters the top three only if it has scores on half the answered weight

  var IND = Object.create(null);   // indicator key -> { he, anchors }
  AX.axes.forEach(function (a) { a.indicators.forEach(function (ind) { IND[ind.key] = ind; }); });

  var LISTS = e.lists.filter(function (l) { return AX.lists[l.id]; }).map(function (l) {
    var d = AX.lists[l.id], sc = Object.create(null);
    AX.axes.forEach(function (a) {
      Object.keys(d.axes[a.key].ind).forEach(function (k) {
        var v = d.axes[a.key].ind[k];
        if (v) sc[k] = v.score;
      });
    });
    return { l: l, color: A.partyColor(l), href: A.partyHref(e.key, l.id) + "#axes", poll: l.polls ? l.polls.overall || 0 : 0, sc: sc };
  });

  /* ------------------------------------------------------------ state */
  // ans[i] = null (skipped / not answered) or { o: answer index 0-4, imp: true/false }
  var ans = [], cur = 0, i;
  for (i = 0; i < N; i++) ans.push(null);
  var CODES = "abcde";
  function encode() {
    return ans.map(function (a) {
      if (!a) return "-";
      var c = CODES.charAt(a.o);
      return a.imp ? c.toUpperCase() : c;
    }).join("");
  }
  function decode(s) {
    if (!s || s.length !== N || !/^[a-eA-E-]+$/.test(s)) return false;
    for (var k = 0; k < N; k++) {
      var c = s.charAt(k);
      ans[k] = c === "-" ? null : { o: CODES.indexOf(c.toLowerCase()), imp: c !== c.toLowerCase() };
    }
    return true;
  }
  function setAddress(withAnswers) {
    try { history.replaceState(null, "", A.pageHref("compass", withAnswers ? "a=" + encode() : "")); } catch (err) { /* file:// */ }
  }
  function answered() { return ans.filter(function (a) { return a; }).length; }

  /* ------------------------------------------------------------ the match */
  function compute() {
    var user = [], totalW = 0;
    ans.forEach(function (a, k) {
      if (!a) return;
      var w = a.imp ? 2 : 1;
      user.push({ q: Q[k], v: AT[a.o], w: w, imp: a.imp, o: a.o });
      totalW += w;
    });
    var rows = LISTS.map(function (p) {
      var dist = 0, w = 0, n = 0;
      user.forEach(function (u) {
        var s = p.sc[u.q.ind];
        if (s == null) return;
        dist += u.w * Math.abs(u.v - s); w += u.w; n++;
      });
      return { p: p, n: n, cover: totalW ? w / totalW : 0, match: w ? 1 - dist / (10 * w) : null };
    });
    rows.forEach(function (r) { r.ok = r.match != null && r.cover >= MIN_COVER; });
    rows.sort(function (a, b) {
      if (a.ok !== b.ok) return a.ok ? -1 : 1;
      if (a.match == null || b.match == null) return a.match == null ? 1 : -1;
      return (b.match - a.match) || (b.cover - a.cover) || (b.p.poll - a.p.poll);
    });
    // the respondent's place on each axis: plain mean of the answered indicators (importance
    // changes the match, not the position); fewer than two = unknown, as on the map
    var pos = Object.create(null);
    AX.axes.forEach(function (a) {
      var vs = user.filter(function (u) { return u.q.axis === a.key; }).map(function (u) { return u.v; });
      pos[a.key] = vs.length < 2 ? null : vs.reduce(function (s, v) { return s + v; }, 0) / vs.length;
    });
    return { user: user, rows: rows, pos: pos };
  }
  function pct(m) { return Math.round(100 * m) + "%"; }
  function one(v) { return v == null ? "לא ידוע" : (Math.round(v * 10) / 10).toString(); }

  /* ------------------------------------------------------------ the page frame */
  main.innerHTML =
    '<section class="e-head"><div class="wrap"><div class="bg-num" aria-hidden="true">%</div><h1>מצפן פוליטי</h1>' +
    '<p class="lede" style="margin-top:8px">' + N + " שאלות על שלושת הצירים של מפת הצירים: ביטחוני, חברתי וכלכלי. בסוף: שלוש הרשימות של הבחירות לכנסת ה-26 שהעמדות שלהן הכי קרובות לשלכם, באחוזי התאמה.</p></div></section>" +
    '<section class="block" style="padding-top:18px"><div class="wrap"><div class="cp" data-cp aria-live="polite"></div></div></section>' +
    '<section class="block" id="method"><div class="wrap"><header><h2>איך זה מחושב</h2><p>אותם מדדים ועוגנים כמו במפת הצירים</p></header>' +
    '<ol class="ax-rules">' +
    "<li>" + esc(AX.compass.intro) + "</li>" +
    "<li>כל תשובה מקבלת את הציון של העוגן שלה (0, 3, 5, 7 או 10), בדיוק כמו שדורגו הרשימות. בכל שאלה התשובות מסודרות מקצה לקצה; הכיוון מתחלף משאלה לשאלה, כדי שהמיקום על המסך לא ימשוך לצד אחד.</li>" +
    "<li>ההתאמה לרשימה: 100% פחות המרחק הממוצע בין התשובה שלכם לציון של הרשימה, על השאלות שעניתם ושיש לרשימה עליהן ציון. מרחק של 10 נקודות (קצה מול קצה) = 0% בשאלה הזו. שאלה שסימנתם כחשובה נספרת פעמיים.</li>" +
    "<li>רשימה שאין לה ציון על חצי מהשאלות שעניתם או יותר לא נכנסת לשלוש הראשונות, כי ההתאמה שלה מבוססת על מעט מדי. היא מופיעה ברשימה המלאה עם סימון.</li>" +
    "<li>המיקום שלכם על כל ציר הוא ממוצע התשובות בציר, ונדרשות לפחות שתי תשובות בציר (כמו במפה).</li>" +
    "<li>החישוב משתמש רק בתשובות. אין שאלות על מגזר, גיל או מקום מגורים: שני אנשים שעונים אותו דבר מקבלים אותה תוצאה.</li>" +
    "<li>התשובות לא נשלחות לשום מקום ולא נשמרות. בעמוד התוצאה הן נכנסות לכתובת בדפדפן, כדי שאפשר יהיה לשתף; מי שמקבל את הקישור רואה את התשובות.</li>" +
    "</ol>" +
    '<p class="small">זו לא המלצת הצבעה. הציונים של הרשימות הם הערכה של האתר (עם מקור לכל ציון) ל-' + LISTS.length + " הרשימות שדורגו ב-2026. " +
    '<a href="' + A.pageHref("axes") + '#method">השיטה והעוגנים במפת הצירים</a></p></div></section>';
  var box = main.querySelector("[data-cp]");

  /* ------------------------------------------------------------ a question */
  function showQuestion(focus) {
    var q = Q[cur], a = ans[cur], ax = V.BY_AXIS[q.axis];
    var order = [0, 1, 2, 3, 4];
    if (cur % 2 === 1) order.reverse();
    var last = cur === N - 1, n = answered();
    box.innerHTML =
      '<div class="cp-prog"><span>שאלה ' + (cur + 1) + " מתוך " + N + '</span><span class="chip">ציר ' + esc(ax.he) + "</span>" +
      '<span class="cp-bar" aria-hidden="true"><span style="width:' + (100 * (cur + 1) / N).toFixed(1) + '%"></span></span></div>' +
      '<h2 class="cp-q" tabindex="-1">' + esc(q.q) + "</h2>" +
      '<div class="cp-opts" role="group" aria-label="תשובות">' + order.map(function (o) {
        return '<button type="button" class="cp-opt" data-o="' + o + '" aria-pressed="' + (a && a.o === o ? "true" : "false") + '">' + esc(q.answers[o]) + "</button>";
      }).join("") + "</div>" +
      '<button type="button" class="cp-imp" data-imp aria-pressed="' + (a && a.imp ? "true" : "false") + '"' + (a ? "" : " disabled") + ">חשוב לי במיוחד (נספר פעמיים)</button>" +
      '<div class="cp-nav">' +
      (cur > 0 ? '<button type="button" class="btn ghost" data-go="prev">הקודמת</button>' : "") +
      '<button type="button" class="btn ghost" data-go="skip">' + (a ? "ביטול התשובה ומעבר" : "דילוג") + "</button>" +
      '<button type="button" class="btn" data-go="next"' + (a ? "" : " disabled") + ">" + (last ? "לתוצאות" : "הבאה") + "</button>" +
      (!last && n >= MIN_ANSWERS ? '<button type="button" class="cp-link" data-go="done">לסיים עכשיו ולראות תוצאות</button>' : "") +
      "</div>" +
      (last && n < MIN_ANSWERS ? '<p class="small">צריך לענות על ' + MIN_ANSWERS + " שאלות לפחות כדי לקבל תוצאה.</p>" : "");
    box.querySelectorAll(".cp-opt").forEach(function (b) {
      b.addEventListener("click", function () {
        var o = Number(b.getAttribute("data-o"));
        ans[cur] = { o: o, imp: ans[cur] ? ans[cur].imp : false };
        showQuestion(false);
        var nb = box.querySelector('.cp-opt[data-o="' + o + '"]');
        if (nb) nb.focus();
      });
    });
    box.querySelector("[data-imp]").addEventListener("click", function () {
      if (!ans[cur]) return;
      ans[cur].imp = !ans[cur].imp;
      showQuestion(false);
      box.querySelector("[data-imp]").focus();
    });
    box.querySelectorAll("[data-go]").forEach(function (b) {
      b.addEventListener("click", function () {
        var g = b.getAttribute("data-go");
        if (g === "prev") { cur--; showQuestion(true); return; }
        if (g === "skip") ans[cur] = null;
        if (g === "done" || cur === N - 1) {
          if (answered() >= MIN_ANSWERS) { showResult(); return; }
          if (g === "skip") { showQuestion(true); return; }
        }
        if (cur < N - 1) cur++;
        showQuestion(true);
      });
    });
    if (focus) {
      box.querySelector(".cp-q").focus({ preventScroll: true });
      if (box.getBoundingClientRect().top < 0) box.scrollIntoView({ block: "start" });
    }
  }

  /* ------------------------------------------------------------ the result */
  // a 0-10 track with the respondent (ring) and the list (dot)
  function pair(u, s, color) {
    var dot = function (v, cls, st) { return '<span class="' + cls + '" style="inset-inline-start:calc(' + (v * 10) + '% - 8px);' + st + '"></span>'; };
    return '<span class="cp-track">' + (s == null ? "" : dot(s, "cp-them", "--pc:" + color)) + dot(u, "cp-you", "") + "</span>";
  }
  function compare(r, res) {
    return '<details class="cp-cmp"><summary>השוואה לפי שאלה</summary><ul>' + res.user.map(function (u) {
      var s = r.p.sc[u.q.ind], ind = IND[u.q.ind], ax = V.BY_AXIS[u.q.axis];
      return '<li><span class="nm">' + esc(ind.he) + (u.imp ? ' <span class="chip">חשוב</span>' : "") + "</span>" +
        '<span class="cp-scale"><span>' + esc(ax.lo) + "</span>" + pair(u.v, s, r.p.color) + "<span>" + esc(ax.hi) + "</span></span>" +
        '<span class="tx">אתם: ' + u.v + " · הרשימה: " + (s == null ? "אין ציון" : s) + "</span></li>";
    }).join("") + '</ul><p class="small"><a href="' + esc(r.p.href) + '">הנימוקים והמקורות של ' + esc(r.p.l.name) + "</a></p></details>";
  }
  function showResult() {
    var res = compute(), top = res.rows.filter(function (r) { return r.ok; }).slice(0, 3);
    setAddress(true);
    var nq = res.user.length;
    var cards = top.map(function (r, k) {
      return '<div class="cp-card" style="--pc:' + r.p.color + '"><div class="cp-rank">' + (k + 1) + "</div>" +
        '<div class="cp-who">' + A.slip(r.p.l) + '<a href="' + esc(r.p.href) + '">' + esc(r.p.l.name) + "</a></div>" +
        '<div class="cp-pct">' + pct(r.match) + "</div>" +
        '<p class="small">על סמך ' + r.n + " מתוך " + nq + " התשובות שלכם</p>" + compare(r, res) + "</div>";
    }).join("");
    var pos = AX.axes.map(function (a) {
      var v = res.pos[a.key];
      return '<div class="ax-card"><div class="ax-head"><h3>' + esc(a.he) + '</h3><span class="ax-score">' + one(v) + (v == null ? "" : "<small>/10</small>") + "</span></div>" +
        '<div class="ax-scale"><span>' + esc(a.lo) + "</span>" +
        (v == null ? '<span class="ax-track unknown"></span>' : '<span class="ax-track"><span class="ax-dot" style="inset-inline-start:calc(' + (v * 10).toFixed(1) + '% - 7px);--pc:var(--ink)"></span></span>') +
        "<span>" + esc(a.hi) + "</span></div>" +
        (v == null ? '<p class="small">צריך לפחות שתי תשובות בציר הזה.</p>' : "") + "</div>";
    }).join("");
    var all = res.rows.map(function (r) {
      var w = r.match == null ? 0 : 100 * r.match;
      return '<li class="' + (r.ok ? "" : "few") + '"><a href="' + esc(r.p.href) + '">' + esc(r.p.l.name) + "</a>" +
        '<span class="cp-meter"><span style="width:' + w.toFixed(1) + "%;--pc:" + r.p.color + '"></span></span>' +
        "<b>" + (r.match == null ? "—" : pct(r.match)) + "</b>" +
        (r.ok ? "" : '<span class="small">' + (r.match == null ? "אין ציון על אף אחת מהתשובות" : "ציון רק על " + r.n + " מהתשובות") + "</span>") + "</li>";
    }).join("");
    box.innerHTML =
      '<h2 class="cp-q" tabindex="-1">הרשימות הכי קרובות אליכם</h2>' +
      (top.length ? '<div class="cp-cards">' + cards + "</div>" : '<p>אין מספיק תשובות שיש עליהן ציון לרשימות. נסו לענות על עוד שאלות.</p>') +
      '<p class="small cp-warn">לא המלצת הצבעה: ההתאמה מבוססת רק על ' + nq + " תשובות ועל הערכה של האתר לעמדות הרשימות.</p>" +
      '<h3 class="cp-sub">המיקום שלכם על הצירים</h3><div class="ax-cards">' + pos + "</div>" +
      '<h3 class="cp-sub">כל הרשימות</h3><ol class="cp-all">' + all + "</ol>" +
      '<div class="cp-nav"><button type="button" class="btn ghost" data-go="edit">שינוי תשובות</button>' +
      '<button type="button" class="btn ghost" data-go="reset">להתחיל מחדש</button>' +
      '<button type="button" class="btn" data-go="copy">העתקת קישור לתוצאה</button><span class="small" data-copied role="status"></span></div>';
    box.querySelector('[data-go="edit"]').addEventListener("click", function () { cur = 0; setAddress(false); showQuestion(true); });
    box.querySelector('[data-go="reset"]').addEventListener("click", function () {
      for (var k = 0; k < N; k++) ans[k] = null;
      cur = 0; setAddress(false); showQuestion(true);
    });
    box.querySelector('[data-go="copy"]').addEventListener("click", function () {
      var out = box.querySelector("[data-copied]");
      var done = function () { out.textContent = "הקישור הועתק"; };
      var fail = function () { out.textContent = "לא הצלחנו להעתיק; אפשר להעתיק את הכתובת מהדפדפן"; };
      try { navigator.clipboard.writeText(location.href).then(done, fail); } catch (err) { fail(); }
    });
    box.querySelector(".cp-q").focus({ preventScroll: true });
    if (box.getBoundingClientRect().top < 0) box.scrollIntoView({ block: "start" });
  }

  /* ------------------------------------------------------------ start */
  if (decode(A.qs("a", 20)) && answered() >= MIN_ANSWERS) showResult();
  else {
    for (i = 0; i < N; i++) ans[i] = null;
    showQuestion(false);
  }
})();
