/* The political compass: one question per indicator of the axis map (data/axes.js -> compass),
   matched against the scores of the 2026 lists. Nothing is sent or stored; the answers can be
   kept in the address (?a=...) so a result can be shared.
   The questions are slides: an answer moves on by itself, and one can swipe (or use the buttons
   and the arrow keys) back and forth between questions already reached. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc, V = window.AxesView;
  A.mount("compass");
  var main = document.getElementById("main");
  if (!V || !V.AX.compass) { A.notFound(main, "נתוני המצפן לא נטענו."); return; }
  var AX = V.AX, Q = AX.compass.questions, N = Q.length, AT = AX.anchorsAt;
  var e = A.byKey[AX.election];
  var MIN_ANSWERS = 3;     // fewer answers = no result
  var MIN_COVER = 0.5;     // a list enters the top three only if it has scores on half the answers
  var ADVANCE_MS = 260;    // the chosen answer stays visible this long before the next slide
  var REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

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
  // ans[i] = null (skipped / not answered) or the answer index 0-4 (the order of the anchors)
  // view = 0..N-1 (a question) or N (the result); far = the furthest question reached
  var ans = [], view = 0, far = 0, busy = false, i;
  for (i = 0; i < N; i++) ans.push(null);
  var CODES = "abcde";
  function encode() { return ans.map(function (a) { return a == null ? "-" : CODES.charAt(a); }).join(""); }
  function decode(s) {
    // capitals came from the first version (an "important" mark, since removed): read as plain answers
    if (!s || s.length !== N || !/^[a-eA-E-]+$/.test(s)) return false;
    for (var k = 0; k < N; k++) {
      var c = s.charAt(k).toLowerCase();
      ans[k] = c === "-" ? null : CODES.indexOf(c);
    }
    return true;
  }
  function setAddress(withAnswers) {
    try { history.replaceState(null, "", A.pageHref("compass", withAnswers ? "a=" + encode() : "")); } catch (err) { /* file:// */ }
  }
  function answered() { return ans.filter(function (a) { return a != null; }).length; }

  /* ------------------------------------------------------------ the match */
  function compute() {
    var user = [];
    ans.forEach(function (a, k) { if (a != null) user.push({ q: Q[k], v: AT[a] }); });
    var rows = LISTS.map(function (p) {
      var dist = 0, n = 0;
      user.forEach(function (u) {
        var s = p.sc[u.q.ind];
        if (s == null) return;
        dist += Math.abs(u.v - s); n++;
      });
      return { p: p, n: n, cover: user.length ? n / user.length : 0, match: n ? 1 - dist / (10 * n) : null };
    });
    rows.forEach(function (r) { r.ok = r.match != null && r.cover >= MIN_COVER; });
    // ordered by the match; lists with too few scores are shown apart, below the ranking
    rows.sort(function (a, b) {
      if (a.match == null || b.match == null) return (a.match == null) - (b.match == null);
      return (b.match - a.match) || (b.cover - a.cover) || (b.p.poll - a.p.poll);
    });
    // the respondent's place on each axis: mean of the answers on it; fewer than two = unknown, as on the map
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
    '<section class="block" style="padding-top:18px"><div class="wrap"><div class="cp cp-stage" data-cp aria-live="polite"></div></div></section>' +
    '<section class="block" id="method"><div class="wrap"><header><h2>איך זה מחושב</h2><p>אותם מדדים ועוגנים כמו במפת הצירים</p></header>' +
    '<ol class="ax-rules">' +
    "<li>" + esc(AX.compass.intro) + "</li>" +
    "<li>כל תשובה מקבלת את הציון של העוגן שלה (0, 3, 5, 7 או 10), בדיוק כמו שדורגו הרשימות. בכל שאלה התשובות מסודרות מקצה לקצה; הכיוון מתחלף משאלה לשאלה, כדי שהמיקום על המסך לא ימשוך לצד אחד.</li>" +
    "<li>ההתאמה לרשימה: 100% פחות המרחק הממוצע בין התשובה שלכם לציון של הרשימה, על השאלות שעניתם ושיש לרשימה עליהן ציון. כל נקודה של מרחק מורידה 10%, ומרחק של 10 נקודות (קצה מול קצה) = 0% בשאלה הזו. כל שאלה שווה.</li>" +
    "<li>100% רק למי שעונה בדיוק כמו הציונים של הרשימה. חלק מהציונים נמצאים בין העוגנים (למשל 6), כי הרשימה עצמה נמצאת בין שתי עמדות; אז גם התשובה הקרובה ביותר רחוקה ממנה בנקודה.</li>" +
    "<li>רשימה שיש לה ציון על פחות מחצי מהשאלות שעניתם לא נכנסת לשלוש הראשונות, כי ההתאמה שלה מבוססת על מעט מדי. היא מופיעה ברשימה נפרדת מתחת לדירוג.</li>" +
    "<li>המיקום שלכם על כל ציר הוא ממוצע התשובות בציר, ונדרשות לפחות שתי תשובות בציר (כמו במפה).</li>" +
    "<li>החישוב משתמש רק בתשובות. אין שאלות על מגזר, גיל או מקום מגורים: שני אנשים שעונים אותו דבר מקבלים אותה תוצאה.</li>" +
    "<li>התשובות לא נשלחות לשום מקום ולא נשמרות. בעמוד התוצאה הן נכנסות לכתובת בדפדפן, כדי שאפשר יהיה לשתף; מי שמקבל את הקישור רואה את התשובות.</li>" +
    "</ol>" +
    '<p class="small">זו לא המלצת הצבעה. הציונים של הרשימות הם הערכה של האתר (עם מקור לכל ציון) ל-' + LISTS.length + " הרשימות שדורגו ב-2026. " +
    '<a href="' + A.pageHref("axes") + '#method">השיטה והעוגנים במפת הצירים</a></p></div></section>';
  var stage = main.querySelector("[data-cp]");

  /* ------------------------------------------------------------ a question slide */
  function questionHTML(k) {
    var q = Q[k], a = ans[k], ax = V.BY_AXIS[q.axis];
    var order = [0, 1, 2, 3, 4];
    if (k % 2 === 1) order.reverse();
    var last = k === N - 1, n = answered();
    var fwd = a != null ? (last ? "לתוצאות" : "הבאה") : (last ? "דילוג ולתוצאות" : "דילוג");
    return '<div class="cp-prog"><span>שאלה ' + (k + 1) + " מתוך " + N + '</span><span class="chip">ציר ' + esc(ax.he) + "</span>" +
      '<span class="cp-bar" aria-hidden="true"><span style="width:' + (100 * (k + 1) / N).toFixed(1) + '%"></span></span></div>' +
      '<h2 class="cp-q" tabindex="-1">' + esc(q.q) + "</h2>" +
      '<div class="cp-opts" role="group" aria-label="תשובות">' + order.map(function (o) {
        return '<button type="button" class="cp-opt" data-o="' + o + '" aria-pressed="' + (a === o ? "true" : "false") + '">' + esc(q.answers[o]) + "</button>";
      }).join("") + "</div>" +
      '<div class="cp-nav">' +
      (k > 0 ? '<button type="button" class="btn ghost" data-go="prev">הקודמת</button>' : "") +
      '<button type="button" class="btn ghost" data-go="next">' + fwd + "</button>" +
      (!last && n >= MIN_ANSWERS ? '<button type="button" class="cp-link" data-go="done">לסיים עכשיו ולראות תוצאות</button>' : "") +
      "</div>" +
      (last && n < MIN_ANSWERS ? '<p class="small">צריך לענות על ' + MIN_ANSWERS + " שאלות לפחות כדי לקבל תוצאה.</p>" : "") +
      '<p class="small cp-hint">אפשר גם להחליק ימינה ושמאלה בין השאלות.</p>';
  }

  /* ------------------------------------------------------------ the result slide */
  // a 0-10 track with the respondent (ring) and the list (dot)
  function pair(u, s, color) {
    var dot = function (v, cls, st) { return '<span class="' + cls + '" style="inset-inline-start:calc(' + (v * 10) + '% - 8px);' + st + '"></span>'; };
    return '<span class="cp-track">' + (s == null ? "" : dot(s, "cp-them", "--pc:" + color)) + dot(u, "cp-you", "") + "</span>";
  }
  function compare(r, res) {
    return '<details class="cp-cmp"><summary>השוואה לפי שאלה</summary><ul>' + res.user.map(function (u) {
      var s = r.p.sc[u.q.ind], ind = IND[u.q.ind], ax = V.BY_AXIS[u.q.axis];
      return '<li><span class="nm">' + esc(ind.he) + "</span>" +
        '<span class="cp-scale"><span>' + esc(ax.lo) + "</span>" + pair(u.v, s, r.p.color) + "<span>" + esc(ax.hi) + "</span></span>" +
        '<span class="tx">אתם: ' + u.v + " · הרשימה: " + (s == null ? "אין ציון" : s) + "</span></li>";
    }).join("") + '</ul><p class="small"><a href="' + esc(r.p.href) + '">הנימוקים והמקורות של ' + esc(r.p.l.name) + "</a></p></details>";
  }
  function resultHTML() {
    var res = compute(), top = res.rows.filter(function (r) { return r.ok; }).slice(0, 3), nq = res.user.length;
    var cards = top.map(function (r, k) {
      return '<div class="cp-card" style="--pc:' + r.p.color + '"><div class="cp-rank">' + (k + 1) + "</div>" +
        '<div class="cp-who">' + A.slip(r.p.l) + '<a href="' + esc(r.p.href) + '">' + esc(r.p.l.name) + "</a></div>" +
        '<div class="cp-pct">' + pct(r.match) + "</div>" +
        '<p class="small">יש לרשימה ציון על ' + r.n + " מתוך " + nq + " השאלות שעניתם</p>" + compare(r, res) + "</div>";
    }).join("");
    var pos = AX.axes.map(function (a) {
      var v = res.pos[a.key];
      return '<div class="ax-card"><div class="ax-head"><h3>' + esc(a.he) + '</h3><span class="ax-score">' + one(v) + (v == null ? "" : "<small>/10</small>") + "</span></div>" +
        '<div class="ax-scale"><span>' + esc(a.lo) + "</span>" +
        (v == null ? '<span class="ax-track unknown"></span>' : '<span class="ax-track"><span class="ax-dot" style="inset-inline-start:calc(' + (v * 10).toFixed(1) + '% - 7px);--pc:var(--ink)"></span></span>') +
        "<span>" + esc(a.hi) + "</span></div>" +
        (v == null ? '<p class="small">צריך לפחות שתי תשובות בציר הזה.</p>' : "") + "</div>";
    }).join("");
    function row(r) {
      var w = r.match == null ? 0 : 100 * r.match;
      return '<li class="' + (r.ok ? "" : "few") + '"><a href="' + esc(r.p.href) + '">' + esc(r.p.l.name) + "</a>" +
        '<span class="cp-meter"><span style="width:' + w.toFixed(1) + "%;--pc:" + r.p.color + '"></span></span>' +
        "<b>" + (r.match == null ? "—" : pct(r.match)) + "</b>" +
        (r.ok ? "" : '<span class="small">' + (r.match == null ? "אין ציון על אף אחת מהשאלות שעניתם" : "נפסלה: יש לה ציון רק על " + r.n + " מתוך " + nq + " השאלות שעניתם") + "</span>") + "</li>";
    }
    var all = res.rows.filter(function (r) { return r.ok; }).map(row).join("");
    var few = res.rows.filter(function (r) { return !r.ok; });
    return '<h2 class="cp-q" tabindex="-1">הרשימות הכי קרובות אליכם</h2>' +
      (top.length ? '<div class="cp-cards">' + cards + "</div>" : "<p>אין מספיק תשובות שיש עליהן ציון לרשימות. נסו לענות על עוד שאלות.</p>") +
      '<p class="small cp-warn">לא המלצת הצבעה: ההתאמה מבוססת רק על ' + nq + " תשובות ועל הערכה של האתר לעמדות הרשימות.</p>" +
      '<h3 class="cp-sub">המיקום שלכם על הצירים</h3><div class="ax-cards">' + pos + "</div>" +
      '<h3 class="cp-sub">כל הרשימות</h3><ol class="cp-all">' + all + "</ol>" +
      (few.length ? '<h3 class="cp-sub">נפסלו מהדירוג</h3>' +
        '<p class="small">לרשימות האלה יש ציון על פחות מחצי מהשאלות שעניתם, ולכן הן נפסלו מהדירוג: האחוז מוצג, אבל הוא מבוסס על מעט מדי שאלות.</p>' +
        '<ul class="cp-all">' + few.map(row).join("") + "</ul>" : "") +
      '<div class="cp-nav"><button type="button" class="btn ghost" data-go="edit">חזרה לשאלות</button>' +
      '<button type="button" class="btn ghost" data-go="reset">להתחיל מחדש</button>' +
      '<button type="button" class="btn" data-go="copy">העתקת קישור לתוצאה</button><span class="small" data-copied role="status"></span></div>';
  }

  /* ------------------------------------------------------------ slides */
  function slideHTML(v) { return v === N ? resultHTML() : questionHTML(v); }
  function current() { return stage.querySelector(".cp-slide:not(.out)"); }
  function focusSlide(sl) {
    var h = sl.querySelector(".cp-q");
    if (h) h.focus({ preventScroll: true });
    if (stage.getBoundingClientRect().top < 0) stage.scrollIntoView({ block: "start", behavior: REDUCED ? "auto" : "smooth" });
  }
  // dir: 1 = forward (in a right-to-left page the next slide comes in from the left), -1 = back, 0 = no animation
  function show(v, dir) {
    if (v < 0 || v > N) return;
    if (v === N && answered() < MIN_ANSWERS) v = N - 1;
    view = v;
    if (v < N) far = Math.max(far, v);
    setAddress(v === N);
    var old = current();
    var sl = document.createElement("div");
    sl.className = "cp-slide";
    sl.innerHTML = slideHTML(v);
    wire(sl);
    if (!old || !dir || REDUCED || !sl.animate) {
      if (old) old.remove();
      stage.appendChild(sl);
      if (old) focusSlide(sl);
      return;
    }
    busy = true;
    var from = old.style.transform || "translateX(0px)";
    old.classList.add("out");
    stage.appendChild(sl);
    var ease = { duration: 320, easing: "cubic-bezier(.2,.7,.2,1)", fill: "forwards" };
    old.animate([{ transform: from, opacity: 1 }, { transform: "translateX(" + (dir * 100) + "%)", opacity: 0 }], ease);
    var anim = sl.animate([{ transform: "translateX(" + (-dir * 100) + "%)", opacity: 0 }, { transform: "translateX(0)", opacity: 1 }], ease);
    var done = false;
    var finish = function () {
      if (done) return;
      done = true; old.remove(); busy = false; focusSlide(sl);
    };
    anim.onfinish = finish;
    setTimeout(finish, 600);
  }
  function canForward() { return view < N && (ans[view] != null || view < far); }
  function forward() {
    if (view === N - 1) show(N, 1);
    else show(view + 1, 1);
  }

  function wire(sl) {
    sl.querySelectorAll(".cp-opt").forEach(function (b) {
      b.addEventListener("click", function () {
        if (busy || justSwiped()) return;
        ans[view] = Number(b.getAttribute("data-o"));
        sl.querySelectorAll(".cp-opt").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        busy = true;
        setTimeout(function () { busy = false; forward(); }, REDUCED ? 0 : ADVANCE_MS);
      });
    });
    sl.querySelectorAll("[data-go]").forEach(function (b) {
      b.addEventListener("click", function () {
        if (busy || justSwiped()) return;
        var g = b.getAttribute("data-go");
        if (g === "prev") show(view - 1, -1);
        else if (g === "next") {
          if (view === N - 1 && answered() < MIN_ANSWERS) return;
          forward();
        }
        else if (g === "done") show(N, 1);
        else if (g === "edit") show(N - 1, -1);
        else if (g === "reset") {
          for (var k = 0; k < N; k++) ans[k] = null;
          far = 0; show(0, -1);
        } else if (g === "copy") {
          var out = sl.querySelector("[data-copied]");
          var ok = function () { out.textContent = "הקישור הועתק"; };
          var fail = function () { out.textContent = "לא הצלחנו להעתיק; אפשר להעתיק את הכתובת מהדפדפן"; };
          try { navigator.clipboard.writeText(location.href).then(ok, fail); } catch (err) { fail(); }
        }
      });
    });
  }

  /* ------------------------------------------------------------ swipe and keys */
  // Swiping right moves forward (the reading direction of a right-to-left page), left moves back.
  // Forward only to a question already reached or past an answered one; the slide follows the finger.
  var drag = null, swiped = 0;
  function justSwiped() { return Date.now() - swiped < 400; }
  stage.addEventListener("pointerdown", function (ev) {
    if (busy || ev.pointerType === "mouse" || view === N) return;
    drag = { x: ev.clientX, y: ev.clientY, dx: 0, on: false, id: ev.pointerId };
  });
  stage.addEventListener("pointermove", function (ev) {
    if (!drag || ev.pointerId !== drag.id) return;
    var dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    if (!drag.on) {
      if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
      if (Math.abs(dy) > Math.abs(dx)) { drag = null; return; }      // a vertical scroll
      drag.on = true;
      try { stage.setPointerCapture(ev.pointerId); } catch (err) { /* old browsers */ }
    }
    var allowed = dx > 0 ? canForward() : view > 0;
    drag.dx = allowed ? dx : dx / 4;                                   // resistance at the edges
    var sl = current();
    if (sl) sl.style.transform = "translateX(" + drag.dx + "px)";
  });
  function release(ev) {
    if (!drag || (ev && ev.pointerId !== drag.id)) return;
    var d = drag; drag = null;
    if (!d.on) return;
    swiped = Date.now();                                               // a swipe is not a click on the answer under the finger
    var sl = current(), far_ = Math.abs(d.dx) > Math.min(90, stage.clientWidth * 0.22);
    if (far_ && d.dx > 0 && canForward()) { forward(); return; }
    if (far_ && d.dx < 0 && view > 0) { show(view - 1, -1); return; }
    if (sl) {
      if (sl.animate && !REDUCED) sl.animate([{ transform: sl.style.transform }, { transform: "translateX(0)" }], { duration: 180, easing: "ease-out" });
      sl.style.transform = "";
    }
  }
  stage.addEventListener("pointerup", release);
  stage.addEventListener("pointercancel", release);
  document.addEventListener("keydown", function (ev) {
    if (busy || view === N || ev.altKey || ev.ctrlKey || ev.metaKey) return;
    if (!stage.contains(document.activeElement) && document.activeElement !== document.body) return;
    if (ev.key === "ArrowLeft" && canForward()) { ev.preventDefault(); forward(); }
    else if (ev.key === "ArrowRight" && view > 0) { ev.preventDefault(); show(view - 1, -1); }
  });

  /* ------------------------------------------------------------ start */
  if (decode(A.qs("a", 20)) && answered() >= MIN_ANSWERS) { far = N - 1; show(N, 0); }
  else {
    for (i = 0; i < N; i++) ans[i] = null;
    show(0, 0);
  }
})();
