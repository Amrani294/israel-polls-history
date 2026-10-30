/* Coalition builder: pick lists and see whether they reach 61 seats,
   by the official result, the poll average or the exit-poll average. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc;
  A.mount("coalition");
  var main = document.getElementById("main");

  var MODES = {
    result: { label: "תוצאות רשמיות", short: "תוצאה" },
    polls: { label: "ממוצע הסקרים", short: "ממוצע סקרים" },
    exit: { label: "ממוצע המדגמים", short: "ממוצע מדגמים" }
  };
  function hasResults(e) { return e.lists.some(function (l) { return l.seats > 0; }); }
  function modesOf(e) {
    var m = [];
    if (hasResults(e)) m.push("result");
    if (e.lists.some(function (l) { return l.polls && l.polls.overall != null; })) m.push("polls");
    if (e.exitPolls && e.exitPolls.length) m.push("exit");
    return m;
  }
  function value(l, mode) {
    if (mode === "result") return l.seats;
    if (mode === "polls") return l.polls && l.polls.overall != null ? l.polls.overall : null;
    return l.exitAvg;
  }

  /* ------------------------------------------------------------ state (kept in the address, so a coalition can be shared) */
  var state = { e: null, mode: null, picked: {} };
  function readState() {
    var e = A.byKey[A.qs("e")] || A.ELECTIONS[0];
    var ms = modesOf(e), m = A.qs("m");
    state.e = e;
    state.mode = ms.indexOf(m) >= 0 ? m : ms[0];
    state.picked = Object.create(null);
    var ids = (A.qs("l", 400) || "").split(",");
    e.lists.forEach(function (l) { if (ids.indexOf(l.id) >= 0) state.picked[l.id] = true; });
  }
  function writeState() {
    var ids = state.e.lists.filter(function (l) { return state.picked[l.id]; }).map(function (l) { return l.id; });
    var q = "e=" + encodeURIComponent(state.e.key) + "&m=" + state.mode + (ids.length ? "&l=" + ids.map(encodeURIComponent).join(",") : "");
    try { history.replaceState(null, "", A.pageHref("coalition", q)); } catch (err) { /* file:// */ }
  }

  /* ------------------------------------------------------------ pieces */
  function rows(e, mode) {
    return e.lists.map(function (l) { return { l: l, v: value(l, mode) }; })
      .filter(function (r) { return r.v != null && (r.v > 0 || state.picked[r.l.id]); })
      .sort(function (a, b) { return b.v - a.v || (A.axisMid(b.l.position) || 0) - (A.axisMid(a.l.position) || 0); });
  }
  function meter(e, mode) {
    var rs = rows(e, mode), sel = rs.filter(function (r) { return state.picked[r.l.id]; });
    var total = sel.reduce(function (s, r) { return s + r.v; }, 0);
    total = Math.round(total * 10) / 10;
    var need = 61 - total, ok = need <= 0;
    var segs = sel.map(function (r) {
      return '<span style="width:' + (100 * r.v / 120).toFixed(3) + "%;--pc:" + A.partyColor(r.l) + '" title="' + esc(r.l.name + ": " + A.fmtSeats(r.v)) + '"></span>';
    }).join("");
    var status = !sel.length ? "בחרו רשימות כדי להתחיל" :
      ok ? "יש רוב: " + A.fmtSeats(total) + " מתוך 120" + (total - 61 >= 1 ? ", " + A.fmtSeats(Math.round((total - 61) * 10) / 10) + " מעל הרף" : "") :
        "חסרים " + A.fmtSeats(Math.round(need * 10) / 10) + " מושבים לרוב";
    return '<div class="co-total' + (ok ? " ok" : "") + '"><span class="big">' + A.fmtSeats(total) + '</span><span class="of">/ 61</span></div>' +
      '<p class="co-status" role="status">' + esc(status) + "</p>" +
      '<div class="co-bar" aria-hidden="true">' + segs + '<i class="line" style="inset-inline-start:' + (100 * 61 / 120).toFixed(3) + '%"></i></div>' +
      '<div class="co-scale" aria-hidden="true"><span>0</span><span style="inset-inline-start:' + (100 * 61 / 120).toFixed(3) + '%">61</span><span class="end">120</span></div>';
  }
  function chips(e, mode) {
    return rows(e, mode).map(function (r) {
      var on = !!state.picked[r.l.id];
      return '<button type="button" class="co-chip" aria-pressed="' + on + '" data-id="' + esc(r.l.id) + '" style="--pc:' + A.partyColor(r.l) + '">' +
        A.slip(r.l, "sm") + '<span class="nm">' + esc(r.l.name) + '</span><span class="v">' + A.fmtSeats(Math.round(r.v * 10) / 10) + "</span></button>";
    }).join("");
  }
  function presets(e) {
    var hasC = e.lists.some(function (l) { return l.bloc === "C" && (e.upcoming || l.seats > 0); });
    var label = e.upcoming || e.kind === "rec" || e.kind === "pre" ? e.blocLabels.C : "הקואליציה שקמה בפועל";
    return (hasC ? '<button type="button" class="btn ghost" data-preset="C">' + esc(label) + "</button>" : "") +
      '<button type="button" class="btn ghost" data-preset="none">ניקוי</button>';
  }

  function render() {
    var e = state.e, mode = state.mode, ms = modesOf(e);
    var note = e.upcoming ? "לפני הבחירות: ממוצע הגופים של כל רשימה, בסקרים עד " + A.fmtDate(e.asOf) + ". רשימות עם ממוצע 0 לא מופיעות." :
      mode === "polls" ? "ממוצע הגופים של כל רשימה שבמעקב הסקרים, בשלושת החודשים שלפני הבחירות. רשימות שלא היו במעקב לא מופיעות." :
      mode === "exit" ? "ממוצע מדגמי ליל הבחירות של ערוצי הטלוויזיה." : "התוצאות הרשמיות של ועדת הבחירות המרכזית.";
    main.querySelector("[data-body]").innerHTML =
      '<div class="co-controls"><div class="toggle" role="group" aria-label="לפי מה לספור">' + ms.map(function (m) {
        return '<button type="button" data-mode="' + m + '" aria-pressed="' + (m === mode) + '">' + esc(MODES[m].label) + "</button>";
      }).join("") + '</div><div class="co-presets">' + presets(e) + "</div></div>" +
      '<p class="small">' + esc(note) + ' <a href="' + A.electionHref(e.key) + '">' + esc(A.electionTitle(e)) + "</a></p>" +
      '<div class="co-grid"><div class="co-chips" role="group" aria-label="רשימות">' + chips(e, mode) + "</div>" +
      '<aside class="co-meter" aria-live="polite">' + meter(e, mode) + "</aside></div>";
    main.querySelectorAll(".e-switch a").forEach(function (a) {
      if (a.getAttribute("data-key") === e.key) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    document.title = "בונה קואליציות, " + A.shortWhen(e) + " | היסטוריית הסקרים של ישראל";
  }

  /* ------------------------------------------------------------ page */
  main.innerHTML =
    '<section class="e-head"><div class="wrap"><div class="bg-num" aria-hidden="true">61</div><h1>בונה קואליציות</h1>' +
    '<p class="lede" style="margin-top:8px">בחרו רשימות וראו אם הן מגיעות ל-61 מושבים: לפי התוצאות, לפי ממוצע הסקרים או לפי המדגמים. הכתובת בדפדפן נשמרת עם הבחירה, כך שאפשר לשתף קואליציה.</p>' +
    '<nav class="e-switch" aria-label="בחירת מערכת">' + A.ELECTIONS.map(function (e) {
      return '<a href="' + A.pageHref("coalition", "e=" + encodeURIComponent(e.key)) + '" data-key="' + esc(e.key) + '">' + esc(A.shortWhen(e)) + "</a>";
    }).join("") + "</nav></div></section>" +
    '<section class="block" style="padding-top:18px"><div class="wrap" data-body></div></section>';

  main.addEventListener("click", function (ev) {
    var t = ev.target.closest("a[data-key], button[data-mode], button[data-id], button[data-preset]");
    if (!t || !main.contains(t)) return;
    if (t.hasAttribute("data-key")) {
      ev.preventDefault();
      var e = A.byKey[t.getAttribute("data-key")];
      if (!e) return;
      state.e = e;
      state.picked = Object.create(null);
      if (modesOf(e).indexOf(state.mode) < 0) state.mode = modesOf(e)[0];
    } else if (t.hasAttribute("data-mode")) {
      if (modesOf(state.e).indexOf(t.getAttribute("data-mode")) >= 0) state.mode = t.getAttribute("data-mode");
    } else if (t.hasAttribute("data-id")) {
      var id = t.getAttribute("data-id");
      if (state.picked[id]) delete state.picked[id]; else state.picked[id] = true;
    } else {
      state.picked = Object.create(null);
      if (t.getAttribute("data-preset") === "C") {
        state.e.lists.forEach(function (l) { if (l.bloc === "C" && (state.e.upcoming || l.seats > 0)) state.picked[l.id] = true; });
      }
    }
    writeState();
    var focusId = t.getAttribute("data-id"), focusMode = t.getAttribute("data-mode");
    render();
    var back = focusId ? main.querySelector('button[data-id="' + focusId.replace(/["\\]/g, "") + '"]') :
      focusMode ? main.querySelector('button[data-mode="' + focusMode.replace(/["\\]/g, "") + '"]') : null;
    if (back) back.focus();
  });

  readState();
  render();
})();
