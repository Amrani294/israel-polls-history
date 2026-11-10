/* The political compass: one question per indicator of the axis map (data/axes.js -> compass),
   matched against the scores of the 2026 lists. Nothing is sent or stored; the answers can be
   kept in the address (?a=...) so a result can be shared.
   The questions are slides: an answer moves on by itself, and one can swipe (or use the buttons
   and the arrow keys) back and forth between questions already reached.
   Once started, the questionnaire takes over the screen (focus mode: the rest of the page is dimmed
   and inert, Esc or "יציאה" leaves it); the result is shown back in the page.
   The result can be shared as a PNG drawn here on a canvas (the top list and the main numbers)
   together with a short message and a link to the questionnaire (Web Share API; elsewhere the
   image is downloaded and the message copied). */
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
  // reduced motion: the device setting or "stop animations" in the accessibility panel (asked each time,
  // so switching it on mid-questionnaire takes effect at once)
  function reduced() {
    return window.A11y ? window.A11y.reducedMotion() : !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

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
  // view = START (the start card), 0..N-1 (a question) or N (the result); far = the furthest question reached
  var START = -1;
  var ans = [], view = START, far = 0, busy = false, i;
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
    '<section class="block cp-sec" id="cp-sec" style="padding-top:18px" aria-label="שאלון המצפן הפוליטי"><div class="wrap cp-shell">' +
    '<div class="cp-top"><span class="cp-top-t">מצפן פוליטי</span><button type="button" class="cp-close" data-close>יציאה <span aria-hidden="true">✕</span></button></div>' +
    '<div class="cp cp-stage" data-cp aria-live="polite"></div></div></section>' +
    '<section class="block" id="method"><div class="wrap"><header><h2>איך זה מחושב</h2><p>אותם מדדים ועוגנים כמו במפת הצירים</p></header>' +
    '<ol class="ax-rules">' +
    "<li>" + esc(AX.compass.intro) + "</li>" +
    "<li>כל תשובה מקבלת את הציון של העוגן שלה (0, 3, 5, 7 או 10), בדיוק כמו שדורגו הרשימות. בכל שאלה התשובות מסודרות מקצה לקצה; הכיוון מתחלף משאלה לשאלה, כדי שהמיקום על המסך לא ימשוך לצד אחד.</li>" +
    "<li>ההתאמה לרשימה: 100% פחות המרחק הממוצע בין התשובה שלכם לציון של הרשימה, על השאלות שעניתם ושיש לרשימה עליהן ציון. כל נקודה של מרחק מורידה 10%, ומרחק של 10 נקודות (קצה מול קצה) = 0% בשאלה הזו. כל שאלה שווה.</li>" +
    "<li>100% רק למי שעונה בדיוק כמו הציונים של הרשימה. חלק מהציונים נמצאים בין העוגנים (למשל 6), כי הרשימה עצמה נמצאת בין שתי עמדות; אז גם התשובה הקרובה ביותר רחוקה ממנה בנקודה.</li>" +
    "<li>רשימה שיש לה ציון על פחות מחצי מהשאלות שעניתם לא נכנסת לשלוש הראשונות, כי ההתאמה שלה מבוססת על מעט מדי. היא מופיעה ברשימה נפרדת מתחת לדירוג.</li>" +
    "<li>המיקום שלכם על כל ציר הוא ממוצע התשובות בציר, ונדרשות לפחות שתי תשובות בציר (כמו במפה).</li>" +
    "<li>החישוב משתמש רק בתשובות. אין שאלות על מגזר, גיל או מקום מגורים: שני אנשים שעונים אותו דבר מקבלים אותה תוצאה.</li>" +
    "<li>התשובות לא נשלחות לשום מקום ולא נשמרות. בעמוד התוצאה הן נכנסות לכתובת בדפדפן; מי שמקבל את הכתובת הזו רואה את התשובות. כפתור השיתוף שולח, דרך האפליקציה שתבחרו, תמונה של התוצאה והודעה קצרה עם קישור לשאלון עצמו, בלי התשובות. התמונה נוצרת בדפדפן שלכם.</li>" +
    "</ol>" +
    '<p class="small">זו לא המלצת הצבעה. הציונים של הרשימות הם הערכה של האתר (עם מקור לכל ציון) ל-' + LISTS.length + " הרשימות שדורגו ב-2026. " +
    '<a href="' + A.pageHref("axes") + '#method">השיטה והעוגנים במפת הצירים</a></p></div></section>';
  var stage = main.querySelector("[data-cp]"), sec = main.querySelector("#cp-sec");

  /* ------------------------------------------------------------ focus mode */
  // While answering, the questionnaire is the only thing on the screen: the section becomes a
  // full-screen layer over the dimmed page, and everything else is inert (no focus, no clicks).
  var focused = false, inerted = [];
  function enterFocus() {
    if (focused) return;
    focused = true;
    document.body.classList.add("cp-focus");
    sec.setAttribute("role", "dialog");
    sec.setAttribute("aria-modal", "true");
    var keep = function (el) { return el === main || el.contains(sec); };
    [].slice.call(document.body.children).concat([].slice.call(main.children)).forEach(function (el) {
      if (!keep(el) && !el.inert && el.tagName !== "SCRIPT") { el.inert = true; el.setAttribute("aria-hidden", "true"); inerted.push(el); }
    });
    sec.scrollTop = 0;
  }
  function exitFocus() {
    if (!focused) return;
    focused = false;
    document.body.classList.remove("cp-focus");
    sec.removeAttribute("role");
    sec.removeAttribute("aria-modal");
    inerted.forEach(function (el) { el.inert = false; el.removeAttribute("aria-hidden"); });
    inerted = [];
  }
  sec.querySelector("[data-close]").addEventListener("click", function () { if (!busy) show(START, 0); });

  /* ------------------------------------------------------------ the start card */
  function startHTML() {
    var n = answered();
    return '<div class="cp-start">' +
      '<p class="cp-start-k">' + N + " שאלות · ביטחון, חברה וכלכלה · כשתי דקות</p>" +
      '<h2 class="cp-q" tabindex="-1">איזו רשימה הכי קרובה לעמדות שלכם?</h2>' +
      "<p>עונים על השאלות, ובסוף מקבלים את שלוש הרשימות של הבחירות לכנסת ה-" + esc(e.knesset) + " שהכי מתאימות לכם, באחוזי התאמה, ואת המיקום שלכם על שלושת הצירים.</p>" +
      '<div class="cp-nav">' +
      (n ? '<button type="button" class="btn cp-go" data-go="resume">להמשיך מהשאלה ' + (Math.min(far, N - 1) + 1) + "</button>" +
        '<button type="button" class="btn ghost" data-go="reset">להתחיל מחדש</button>' :
        '<button type="button" class="btn cp-go" data-go="begin">להתחיל את השאלון</button>') +
      "</div></div>";
  }

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
    lastRes = { res: res, top: top };
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
      (top.length ? '<button type="button" class="btn" data-share disabled>שיתוף התוצאה</button>' : "") +
      '<span class="small" data-share-out role="status"></span></div>' +
      (top.length ? '<div class="cp-share-prev" data-share-prev hidden><img alt="התמונה שתישלח בשיתוף: ' + esc(top[0].p.l.name) + ", " + pct(top[0].match) + ' התאמה"><p class="small">' +
        'זו התמונה שתישלח, עם הודעה קצרה וקישור לשאלון. <a href="#" data-share-dl download>הורדת התמונה</a></p></div>' : "");
  }

  /* ------------------------------------------------------------ slides */
  var lastRes = null;
  function slideHTML(v) { return v === START ? startHTML() : v === N ? resultHTML() : questionHTML(v); }
  function current() { return stage.querySelector(".cp-slide:not(.out)"); }
  function focusSlide(sl) {
    var h = sl.querySelector(".cp-q");
    if (h) h.focus({ preventScroll: true });
    if (focused) sec.scrollTop = 0;
    else if (stage.getBoundingClientRect().top < 0) stage.scrollIntoView({ block: "start", behavior: reduced() ? "auto" : "smooth" });
  }
  // dir: 1 = forward (in a right-to-left page the next slide comes in from the left), -1 = back, 0 = no animation
  function show(v, dir) {
    if (v < START || v > N) return;
    if (v === N && answered() < MIN_ANSWERS) v = N - 1;
    var wasFocused = focused;
    if (v >= 0 && v < N) enterFocus(); else exitFocus();
    if (focused !== wasFocused) dir = 0;      // entering or leaving the layer: no slide animation
    view = v;
    if (v >= 0 && v < N) far = Math.max(far, v);
    setAddress(v === N);
    var old = current();
    var sl = document.createElement("div");
    sl.className = "cp-slide";
    sl.innerHTML = slideHTML(v);
    wire(sl);
    if (v === N) prepareShare(sl);
    if (!old || !dir || reduced() || !sl.animate) {
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
  function canForward() { return view >= 0 && view < N && (ans[view] != null || view < far); }
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
        setTimeout(function () { busy = false; forward(); }, reduced() ? 0 : ADVANCE_MS);
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
        else if (g === "begin") show(0, 1);
        else if (g === "resume") show(Math.min(far, N - 1), 1);
        else if (g === "reset") {
          for (var k = 0; k < N; k++) ans[k] = null;
          far = 0; show(0, -1);
        }
      });
    });
  }

  /* ------------------------------------------------------------ sharing the result */
  // The link in the message leads to the questionnaire itself (not to the sender's answers).
  var SITE = "https://pollsisraelhistory.netlify.app";
  function quizURL() {
    var base = /^https?:$/.test(location.protocol) ? location.origin : SITE;
    return base + "/compass";
  }
  function shareText(top) {
    return "יצא לי שהמפלגה שהכי מתאימה לי היא: " + top[0].p.l.name + " (" + pct(top[0].match) + " התאמה).\n" +
      "ולכם? " + N + " שאלות קצרות על ביטחון, חברה וכלכלה, ותגלו איזו רשימה הכי קרובה לעמדות שלכם.\n" +
      "היכנסו לשאלון: " + quizURL();
  }

  // colours of the site (main.css :root)
  var INK = "#18203a", INK2 = "#4a5268", MUTE = "#6b7385", PAPER = "#f3f4f7", RULE = "#d8dce4";
  var DISPLAY = "Karantina, 'IBM Plex Sans Hebrew', Arial, sans-serif", SANS = "'IBM Plex Sans Hebrew', Arial, sans-serif";
  function rrect(c, x, y, w, h, r) {
    c.beginPath();
    c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
  // largest font size (down to min) at which text fits in maxW
  function fitFont(c, text, font, size, maxW, min) {
    for (; size > (min || 12); size -= 2) {
      c.font = font(size);
      if (c.measureText(text).width <= maxW) break;
    }
    return size;
  }
  function drawText(c, str, x, y, font, color, align, dir) {
    c.font = font; c.fillStyle = color; c.textAlign = align || "right"; c.direction = dir || "rtl";
    c.fillText(str, x, y);
  }
  // the ballot slip: white, the letters, a coloured edge at the bottom
  function drawSlip(c, x, y, w, h, letters, color) {
    c.save();
    c.shadowColor = "rgba(24,32,58,0.18)"; c.shadowBlur = 18; c.shadowOffsetY = 6;
    rrect(c, x, y, w, h, 8); c.fillStyle = "#fff"; c.fill();
    c.restore();
    c.save();
    rrect(c, x, y, w, h, 8); c.clip();
    c.fillStyle = color; c.fillRect(x, y + h - Math.round(h * 0.09), w, Math.round(h * 0.09));
    c.restore();
    rrect(c, x, y, w, h, 8); c.strokeStyle = RULE; c.lineWidth = 2; c.stroke();
    var size = fitFont(c, letters, function (z) { return "700 " + z + "px " + DISPLAY; }, Math.round(h * 0.78), w - 28, 20);
    drawText(c, letters, x + w / 2, y + h * 0.5 + size * 0.3, "700 " + size + "px " + DISPLAY, INK, "center");
  }
  function drawCard(c, x, y, w, h, r) {
    c.save();
    c.shadowColor = "rgba(24,32,58,0.14)"; c.shadowBlur = 24; c.shadowOffsetY = 8;
    rrect(c, x, y, w, h, r); c.fillStyle = "#fff"; c.fill();
    c.restore();
    rrect(c, x, y, w, h, r); c.strokeStyle = RULE; c.lineWidth = 2; c.stroke();
  }

  // 1080 x 1350 (4:5, fits chats and Instagram). Returns a promise of { blob, url (data:) }.
  function drawImage(res, top) {
    var W = 1080, H = 1350, M = 72;
    var fonts = document.fonts && document.fonts.load ? Promise.all([
      document.fonts.load("700 100px Karantina"), document.fonts.load("400 30px 'IBM Plex Sans Hebrew'"),
      document.fonts.load("600 30px 'IBM Plex Sans Hebrew'"), document.fonts.load("700 30px 'IBM Plex Sans Hebrew'")
    ]).catch(function () { return null; }) : Promise.resolve();
    return fonts.then(function () {
      var cv = document.createElement("canvas");
      cv.width = W; cv.height = H;
      var c = cv.getContext("2d");
      c.fillStyle = PAPER; c.fillRect(0, 0, W, H);

      // header band, as on the site, with the left-centre-right stripe under it
      c.fillStyle = INK; c.fillRect(0, 0, W, 168);
      var sub = "מצפן פוליטי · הכנסת ה-" + e.knesset;
      c.font = "500 30px " + SANS;
      var subW = c.measureText(sub).width;
      drawText(c, sub, M, 106, "500 30px " + SANS, "#dfe3ee", "left");
      var bs = fitFont(c, "היסטוריית הסקרים של ישראל", function (z) { return "700 " + z + "px " + DISPLAY; }, 72, W - 2 * M - subW - 40, 30);
      drawText(c, "היסטוריית הסקרים של ישראל", W - M, 110, "700 " + bs + "px " + DISPLAY, "#fff");
      var stripe = [getCSS("--left", "#c42a3c"), getCSS("--centre", "#7b3fa8"), getCSS("--right", "#2350b8")];
      stripe.forEach(function (col, k) { c.fillStyle = col; c.fillRect(k * W / 3, 168, W / 3 + 1, 12); });

      drawText(c, "יצא לי שהמפלגה שהכי מתאימה לי היא:", W - M, 250, "600 40px " + SANS, INK2);

      // the first list: slip on the right; name, and the match under it
      var r1 = top[0], cy = 280, ch = 360;
      drawCard(c, M, cy, W - 2 * M, ch, 28);
      c.save(); rrect(c, M, cy, W - 2 * M, ch, 28); c.clip(); c.fillStyle = r1.p.color; c.fillRect(M, cy, W - 2 * M, 16); c.restore();
      var sw = 230, sh = 178, sx = W - M - 44 - sw, sy = cy + 64;
      drawSlip(c, sx, sy, sw, sh, r1.p.l.letters, r1.p.color);
      var tx = sx - 40, maxW = tx - (M + 44);
      var ns = fitFont(c, r1.p.l.name, function (z) { return "700 " + z + "px " + DISPLAY; }, 104, maxW, 36);
      drawText(c, r1.p.l.name, tx, cy + 140, "700 " + ns + "px " + DISPLAY, INK);
      var ptxt = pct(r1.match);
      c.font = "600 42px " + SANS;
      var mw = c.measureText("התאמה").width;
      var ps = fitFont(c, ptxt, function (z) { return "700 " + z + "px " + DISPLAY; }, 190, maxW - mw - 24, 60);
      c.font = "700 " + ps + "px " + DISPLAY;
      var pw = c.measureText(ptxt).width;
      drawText(c, ptxt, tx, cy + 300, "700 " + ps + "px " + DISPLAY, r1.p.color, "right", "ltr");
      drawText(c, "התאמה", tx - pw - 24, cy + 290, "600 42px " + SANS, INK2);
      drawText(c, "ציון על " + r1.n + " מתוך " + res.user.length + " השאלות שעניתי", W - M - 44, cy + ch - 26, "400 26px " + SANS, MUTE);

      // the next two
      if (top.length > 1) drawText(c, "ואחריה:", W - M, 700, "600 34px " + SANS, MUTE);
      top.slice(1).forEach(function (r, k) {
        var y = 720 + k * 116, h = 100;
        drawCard(c, M, y, W - 2 * M, h, 20);
        drawSlip(c, W - M - 24 - 110, y + 11, 110, 78, r.p.l.letters, r.p.color);
        var x2 = W - M - 24 - 110 - 26;
        c.font = "700 80px " + DISPLAY;
        var p2 = c.measureText(pct(r.match)).width;
        var s2 = fitFont(c, r.p.l.name, function (z) { return "700 " + z + "px " + SANS; }, 40, x2 - (M + 28 + p2 + 30), 20);
        drawText(c, r.p.l.name, x2, y + 62, "700 " + s2 + "px " + SANS, INK);
        drawText(c, pct(r.match), M + 28, y + 80, "700 80px " + DISPLAY, r.p.color, "left", "ltr");
      });

      // the respondent on the three axes (0 at the right, next to the low end, as on the site)
      var ay = 1000;
      drawText(c, "המיקום שלי על הצירים", W - M, ay, "700 32px " + SANS, INK);
      var tR = W - M - 170, tL = M + 20;
      AX.axes.forEach(function (a, k) {
        var y = ay + 18 + k * 60, v = res.pos[a.key];
        drawText(c, a.he, W - M, y + 30, "600 28px " + SANS, INK2);
        rrect(c, tL, y + 16, tR - tL, 10, 5); c.fillStyle = "#e3e6ec"; c.fill();
        drawText(c, a.lo, tR, y + 52, "400 20px " + SANS, MUTE);
        drawText(c, a.hi, tL, y + 52, "400 20px " + SANS, MUTE, "left");
        if (v == null) { drawText(c, "לא ידוע", (tR + tL) / 2, y + 12, "400 22px " + SANS, MUTE, "center"); return; }
        var x = tR - (tR - tL) * v / 10;
        c.beginPath(); c.arc(x, y + 21, 15, 0, 2 * Math.PI); c.fillStyle = INK; c.fill();
        c.lineWidth = 4; c.strokeStyle = "#fff"; c.stroke();
      });

      // footer band: where to take it
      c.fillStyle = INK; c.fillRect(0, H - 112, W, 112);
      var host = quizURL().replace(/^https?:\/\//, "");
      drawText(c, "גם אתם? " + host, W / 2, H - 58, "600 34px " + SANS, "#fff", "center");
      drawText(c, "לא המלצת הצבעה · עמדות הרשימות: הערכה של האתר, עם מקור לכל ציון", W / 2, H - 22, "400 22px " + SANS, "#c9d0e0", "center");

      var url = cv.toDataURL("image/png");
      return new Promise(function (ok) {
        cv.toBlob(function (blob) { ok({ blob: blob, url: url }); }, "image/png");
      });
    });
  }
  function getCSS(name, fb) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fb;
  }

  // The image is drawn as soon as the result shows, so that the share button can call
  // navigator.share right inside the click (some browsers refuse it after an async step).
  function prepareShare(sl) {
    var btn = sl.querySelector("[data-share]");
    if (!btn || !lastRes || !lastRes.top.length) return;
    var out = sl.querySelector("[data-share-out]"), prev = sl.querySelector("[data-share-prev]");
    var top = lastRes.top, msg = shareText(top), file = null, blobURL = null;
    var name = "matzpen-" + top[0].p.l.id + ".png";
    out.textContent = "מכינים את התמונה…";
    drawImage(lastRes.res, top).then(function (img) {
      if (!img.blob) throw new Error("no image");
      file = new File([img.blob], name, { type: "image/png" });
      blobURL = URL.createObjectURL(img.blob);
      prev.querySelector("img").src = img.url;
      var dl = prev.querySelector("[data-share-dl]");
      dl.href = blobURL; dl.setAttribute("download", name);
      prev.hidden = false;
      btn.disabled = false;
      out.textContent = "";
    }).catch(function () {
      out.textContent = "לא הצלחנו להכין את התמונה בדפדפן הזה.";
    });
    function copyMsg() {
      try { return navigator.clipboard.writeText(msg); } catch (err) { return Promise.reject(err); }
    }
    // no file sharing here (most desktop browsers): download the image and copy the message
    function fallback() {
      var a = document.createElement("a");
      a.href = blobURL; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      copyMsg().then(function () {
        out.textContent = "התמונה ירדה והטקסט של ההודעה הועתק: אפשר להדביק אותם בהודעה.";
      }, function () {
        out.textContent = "התמונה ירדה. הטקסט להודעה: " + msg;
      });
    }
    btn.addEventListener("click", function () {
      if (!file) return;
      var data = { files: [file], text: msg, title: "המצפן הפוליטי" };
      if (navigator.canShare && navigator.share && navigator.canShare(data)) {
        navigator.share(data).then(function () { out.textContent = ""; }, function (err) {
          if (err && err.name === "AbortError") return;       // closed the share sheet
          fallback();
        });
      } else fallback();
    });
  }

  /* ------------------------------------------------------------ swipe and keys */
  // Swiping right moves forward (the reading direction of a right-to-left page), left moves back.
  // Forward only to a question already reached or past an answered one; the slide follows the finger.
  var drag = null, swiped = 0;
  function justSwiped() { return Date.now() - swiped < 400; }
  stage.addEventListener("pointerdown", function (ev) {
    if (busy || ev.pointerType === "mouse" || view === N || view === START) return;
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
      if (sl.animate && !reduced()) sl.animate([{ transform: sl.style.transform }, { transform: "translateX(0)" }], { duration: 180, easing: "ease-out" });
      sl.style.transform = "";
    }
  }
  stage.addEventListener("pointerup", release);
  stage.addEventListener("pointercancel", release);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && focused && !busy) { ev.preventDefault(); show(START, 0); return; }
    if (busy || view === N || view === START || ev.altKey || ev.ctrlKey || ev.metaKey) return;
    if (!stage.contains(document.activeElement) && document.activeElement !== document.body) return;
    if (ev.key === "ArrowLeft" && canForward()) { ev.preventDefault(); forward(); }
    else if (ev.key === "ArrowRight" && view > 0) { ev.preventDefault(); show(view - 1, -1); }
  });

  /* ------------------------------------------------------------ start */
  if (decode(A.qs("a", 20)) && answered() >= MIN_ANSWERS) { far = N - 1; show(N, 0); }
  else {
    for (i = 0; i < N; i++) ans[i] = null;
    show(START, 0);
  }
})();
