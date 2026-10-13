/* The polls archive: a separate panel, one election at a time. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc;
  A.mount("polls");
  var main = document.getElementById("main");
  var key = A.qs("e");
  if (!A.byKey[key]) key = A.ELECTIONS[0].key;

  main.innerHTML =
    '<section class="e-head"><div class="wrap"><h1>ארכיון הסקרים</h1>' +
    '<p class="lede" style="margin-top:8px">כל הסקרים שפורסמו בשלושת החודשים שלפני כל מערכת בחירות בכאן 11, חדשות 12, חדשות 13, מעריב והארץ, ומדגמי ליל הבחירות של ערוצי הטלוויזיה.</p>' +
    '<p style="margin-top:10px"><a class="btn ghost" href="downloads/polls-2009-2022.xlsx" download>הורדת כל הנתונים כקובץ אקסל</a></p>' +
    '<nav class="e-switch" aria-label="בחירת מערכת">' + A.ELECTIONS.map(function (e) {
      return '<a href="' + A.pollsHref(e.key) + '" data-key="' + e.key + '">' + esc(A.shortWhen(e)) + "</a>";
    }).join("") + "</nav></div></section>" +
    '<section class="block" style="padding-top:18px"><div class="wrap"><p class="small" style="margin-bottom:14px" data-back></p><div data-panel></div></div></section>';

  var panel = main.querySelector("[data-panel]");
  function show(k) {
    key = k;
    main.querySelectorAll(".e-switch a").forEach(function (a) {
      if (a.getAttribute("data-key") === k) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    main.querySelector("[data-back]").innerHTML = 'לתוצאות ולרשימות: <a href="' + A.electionHref(k) + '">' + esc(A.electionTitle(A.byKey[k])) + "</a>";
    window.PollsView.render(panel, k);
    document.title = "ארכיון הסקרים, " + A.shortWhen(A.byKey[k]) + " | היסטוריית הסקרים של ישראל";
  }
  main.querySelectorAll(".e-switch a").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      var k = a.getAttribute("data-key");
      try { history.replaceState(null, "", A.pollsHref(k)); } catch (err) { /* file:// in some browsers */ }
      show(k);
    });
  });
  show(key);
})();
