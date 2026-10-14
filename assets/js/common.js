/* Shared helpers: data access, formatting, colours, header/footer, portraits, ballot slips, hemicycle. */
(function () {
  "use strict";

  var ELECTIONS = window.ELECTIONS || [];
  var PEOPLE = window.PEOPLE || {};
  var META = window.META || {};
  var byKey = Object.create(null);   // no prototype: "?e=__proto__" finds nothing
  ELECTIONS.forEach(function (e) { byKey[e.key] = e; });

  /* ---------------------------------------------------------------- basics */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  // Read a query parameter. Malformed escapes and oversized values are ignored;
  // the value is only ever used as a lookup key, never inserted as markup.
  function qs(name, maxLen) {
    var m = new RegExp("[?&]" + name + "=([^&#]*)").exec(location.search);
    if (!m || m[1].length > (maxLen || 100)) return null;
    try { return decodeURIComponent(m[1].replace(/\+/g, " ")); } catch (err) { return null; }
  }
  function parseISO(iso) {
    var p = iso.split("-").map(Number);
    return new Date(p[0], p[1] - 1, p[2]);
  }
  function fmtDate(iso, opts) {
    return parseISO(iso).toLocaleDateString("he-IL", opts || { day: "numeric", month: "long", year: "numeric" });
  }
  function fmtMonth(iso) { return fmtDate(iso, { month: "long", year: "numeric" }); }
  function fmtInt(n) { return n == null ? "—" : Number(n).toLocaleString("he-IL"); }
  function fmtSeats(v, digits) {
    if (v == null || v === "") return "—";
    if (Number.isInteger(v)) return String(v);
    return Number(v).toFixed(digits == null ? 1 : digits);
  }
  function pctOf(a, b) { return (100 * a / b).toFixed(2) + "%"; }

  /* ---------------------------------------------------------------- political colour */
  // Axis from the English Wikipedia infobox: -3 far-left ... 3 far-right.
  var STOPS = [
    [-3, [142, 22, 40]], [-2, [196, 42, 60]], [-1, [223, 116, 128]], [0, [125, 115, 152]],
    [1, [111, 147, 216]], [2, [35, 80, 184]], [3, [22, 51, 122]]
  ];
  function axisMid(pos) { return pos && pos.lo != null ? (pos.lo + pos.hi) / 2 : null; }
  function colorAt(x) {
    if (x == null) return "#a7adb7";
    for (var i = 0; i < STOPS.length - 1; i++) {
      var a = STOPS[i], b = STOPS[i + 1];
      if (x >= a[0] && x <= b[0]) {
        var t = (x - a[0]) / (b[0] - a[0]);
        var c = a[1].map(function (v, k) { return Math.round(v + (b[1][k] - v) * t); });
        return "rgb(" + c.join(",") + ")";
      }
    }
    return x < -3 ? "rgb(142,22,40)" : "rgb(22,51,122)";
  }
  function partyColor(list) { return colorAt(axisMid(list.position)); }
  var AXIS_HE = { "-3": "שמאל קיצוני", "-2": "שמאל", "-1": "מרכז-שמאל", "0": "מרכז", "1": "מרכז-ימין", "2": "ימין", "3": "ימין קיצוני" };

  // left-to-right seating order: by axis position, unknown positions at the left edge
  function seatingOrder(lists, byBloc) {
    var BO = { O: 0, N: 1, X: 1, C: 2 };
    return lists.filter(function (l) { return l.seats > 0; }).slice().sort(function (a, b) {
      if (byBloc && BO[a.bloc] !== BO[b.bloc]) return BO[a.bloc] - BO[b.bloc];
      var ma = axisMid(a.position), mb = axisMid(b.position);
      if (ma == null && mb != null) return -1;
      if (mb == null && ma != null) return 1;
      if (ma != null && ma !== mb) return ma - mb;
      var ba = a.bloc === "C" ? 1 : 0, bb = b.bloc === "C" ? 1 : 0;
      if (ba !== bb) return ba - bb;
      return b.seats - a.seats;
    });
  }

  /* ---------------------------------------------------------------- links */
  // Online the addresses are clean ("/election?e=2022"; Netlify serves election.html,
  // see _redirects). Opened from the folder (file://) they must name the file.
  var CLEAN = location.protocol === "http:" || location.protocol === "https:";
  function pageHref(name, query) {
    var base = CLEAN ? (name === "index" ? "/" : "/" + name) : name + ".html";
    return base + (query ? "?" + query : "");
  }
  function electionHref(key) { return pageHref("election", "e=" + encodeURIComponent(key)); }
  function partyHref(key, id) { return pageHref("party", "e=" + encodeURIComponent(key) + "&p=" + encodeURIComponent(id)); }
  function pollsHref(key) { return pageHref("polls", key ? "e=" + encodeURIComponent(key) : ""); }
  function electionTitle(e) { return "הבחירות לכנסת ה-" + e.knesset; }
  function shortWhen(e) { return fmtMonth(e.date); }

  /* ---------------------------------------------------------------- pieces */
  function slip(list, size) {
    return '<span class="slip ' + (size || "") + '" style="--pc:' + partyColor(list) + '" aria-label="אותיות הפתק: ' +
      esc(list.letters) + '"><span class="l">' + esc(list.letters) + "</span></span>";
  }
  function initials(title) {
    var words = title.replace(/\(.*?\)/g, "").replace(/["'״׳]/g, "").trim().split(/\s+/);
    return words.slice(0, 2).map(function (w) { return w.charAt(0); }).join(".");
  }
  function displayName(title) { return title.replace(/\s*\(.*?\)\s*$/, ""); }
  function portrait(title, color) {
    var p = PEOPLE[title] || {};
    var credit = p.file ? "צילום: " + (p.artist || "לא צוין") + ", רישיון " + (p.license || "לא צוין") + " (ויקישיתוף)" : "אין תמונה חופשית זמינה";
    var img = p.img ? '<img src="' + esc(p.img) + '" alt="' + esc(displayName(title)) + '" loading="lazy" decoding="async" referrerpolicy="no-referrer">' : "";
    return '<span class="ph' + (p.img ? "" : " failed") + '" style="--pc:' + (color || "#a7adb7") + '" title="' + esc(credit) + '">' + img +
      '<span class="ini" aria-hidden="true">' + esc(initials(title)) + "</span></span>";
  }
  function blocChip(e, code) {
    return '<span class="chip ' + code + '">' + esc(e.blocLabels[code]) + "</span>";
  }
  function recText(list) {
    if (!list.rec) return "לא נכנסה לכנסת";
    var c = (META.candidates || {})[list.rec] || list.rec;
    return list.rec === "-" ? c : "המליצה על " + c;
  }

  // A portrait that fails to load shows initials. Wikimedia Commons sometimes refuses
  // when a page asks for many thumbnails at once, so a failed portrait is retried
  // (twice, spread out in time) and replaces the initials when it arrives.
  // One pair of listeners for the whole page (no inline onerror attributes, so the
  // CSP can forbid inline script).
  var RETRIES = 2;
  function isPortrait(t) {
    return t && t.tagName === "IMG" && t.parentNode && t.parentNode.classList && t.parentNode.classList.contains("ph");
  }
  document.addEventListener("error", function (ev) {
    var t = ev.target;
    if (!isPortrait(t)) return;
    t.parentNode.classList.add("failed");
    var n = Number(t.getAttribute("data-retry") || 0);
    if (n >= RETRIES) return;
    var base = t.getAttribute("data-src") || t.getAttribute("src");
    t.setAttribute("data-src", base);
    t.setAttribute("data-retry", String(n + 1));
    setTimeout(function () {
      t.src = base + (base.indexOf("?") >= 0 ? "&" : "?") + "retry=" + (n + 1);
    }, 1500 * (n + 1) + Math.random() * 2500);
  }, true);
  document.addEventListener("load", function (ev) {
    if (isPortrait(ev.target)) ev.target.parentNode.classList.remove("failed");
  }, true);

  /* ---------------------------------------------------------------- hemicycle */
  var layoutCache = {};
  function seatLayout(n) {
    if (layoutCache[n]) return layoutCache[n];
    var rows = n > 100 ? 7 : 5, r0 = 0.38, radii = [], i, j;
    for (i = 0; i < rows; i++) radii.push(r0 + (1 - r0) * i / (rows - 1));
    var tot = radii.reduce(function (a, b) { return a + b; }, 0);
    var counts = radii.map(function (r) { return Math.round(n * r / tot); });
    counts[rows - 1] += n - counts.reduce(function (a, b) { return a + b; }, 0);
    var seats = [];
    radii.forEach(function (r, ri) {
      var k = counts[ri];
      for (j = 0; j < k; j++) {
        var a = Math.PI - (k === 1 ? Math.PI / 2 : j * Math.PI / (k - 1));
        seats.push({ x: r * Math.cos(a), y: -r * Math.sin(a), a: a, row: ri });
      }
    });
    seats.sort(function (p, q) { return (q.a - p.a) || (p.row - q.row); });
    layoutCache[n] = seats;
    return seats;
  }
  function seatFill(list, mode) {
    if (mode === "bloc") return { C: "#18203a", O: "#b9bfcc", N: "#e1e4ea", X: "#eceef2" }[list.bloc];
    return partyColor(list);
  }
  // returns an SVG string; seats carry data-id so the page can highlight a list
  function hemicycle(e, opts) {
    opts = opts || {};
    var mode = opts.mode || "position";
    var order = seatingOrder(e.lists, mode === "bloc");
    var seats = seatLayout(120), S = 200, rr = 0.043 * S, out = [], k = 0;
    order.forEach(function (l) {
      for (var s = 0; s < l.seats; s++, k++) {
        var p = seats[k];
        var stroke = mode === "bloc" && l.bloc === "N" ? ' stroke="#9aa1b0" stroke-width="1"' : "";
        out.push('<circle class="seat" data-id="' + esc(l.id) + '" cx="' + (p.x * S).toFixed(1) + '" cy="' + (p.y * S).toFixed(1) +
          '" r="' + rr.toFixed(1) + '" fill="' + seatFill(l, mode) + '"' + stroke + "><title>" + esc(l.name) + " – " + l.seats + " מושבים</title></circle>");
      }
    });
    var label = "";
    if (opts.center !== false) {
      if (mode === "bloc") {
        var c = e.blocs.final.C, o = e.blocs.final.O;
        label = '<text class="sum" x="0" y="-20" font-size="30" font-weight="900" direction="ltr">' + o + "–" + c + "</text>" +
          '<text x="0" y="-2" text-anchor="middle" font-size="11" fill="#6b7385">' + esc(e.blocLabels.C) + " מול " + esc(e.blocLabels.O) + "</text>";
      } else {
        label = '<text class="sum" x="0" y="-18" font-size="32" font-weight="900">120</text>' +
          '<text x="0" y="-2" text-anchor="middle" font-size="11" fill="#6b7385">מושבים</text>';
      }
    }
    var vb = (-S * 1.06).toFixed(0) + " " + (-S * 1.06).toFixed(0) + " " + (S * 2.12).toFixed(0) + " " + (S * 1.1).toFixed(0);
    return '<svg viewBox="' + vb + '" role="img" aria-label="' + esc(opts.label || ("חלוקת המושבים, " + electionTitle(e))) + '">' + out.join("") + label + "</svg>";
  }

  /* ---------------------------------------------------------------- stacked bloc bar */
  function blocBar(e, values, total) {
    total = total || 120;
    return '<div class="bar">' + e.blocOrder.map(function (b) {
      var v = values[b] || 0;
      if (v <= 0) return "";
      var w = (100 * v / total).toFixed(3);
      return '<span class="' + b + '" style="width:' + w + '%" title="' + esc(e.blocLabels[b]) + ": " + fmtSeats(v) + '">' + (v >= 6 ? fmtSeats(v) : "") + "</span>";
    }).join("") + "</div>";
  }
  function blocLegend(e) {
    return '<div class="legend">' + e.blocOrder.map(function (b) {
      return '<span class="' + b + '"><i></i>' + esc(e.blocLabels[b]) + "</span>";
    }).join("") + "</div>";
  }

  /* ---------------------------------------------------------------- page chrome */
  function header(active) {
    var nav = [
      ["index", "מערכות הבחירות", "home"],
      ["polls", "ארכיון הסקרים", "polls"],
      ["accuracy", "דיוק הסוקרים", "accuracy"],
      ["coalition", "בונה קואליציות", "coalition"],
      ["about", "על האתר", "about"]
    ].map(function (n) {
      return '<a href="' + pageHref(n[0]) + '"' + (n[2] === active ? ' aria-current="page"' : "") + (n[2] === "polls" ? ' class="nav-polls"' : "") + ">" + n[1] + "</a>";
    }).join("");
    return '<header class="site-head"><div class="wrap"><a class="brand" href="' + pageHref("index") + '">היסטוריית הסקרים של ישראל</a>' +
      '<nav class="nav" aria-label="ניווט ראשי">' + nav + "</nav></div></header>";
  }
  function footer() {
    return '<footer class="site-foot"><div class="wrap">' +
      "<p>הנתונים נאספו מוויקיפדיה (העברית והאנגלית), מכתבות חדשות מליל הבחירות ומפרסומי ועדת הבחירות המרכזית, ונבדקו מול המקור. " +
      'פירוט השיטה, המקורות וזכויות התמונות בעמוד <a href="' + pageHref("about") + '">על האתר ומקורות</a>.</p>' +
      "<p>תמונות חברי הכנסת מוויקישיתוף, ברישיונות חופשיים; שם הצלם והרישיון מופיעים במעבר עכבר על כל תמונה.</p>" +
      '<div class="credit"><span>נבנה על ידי</span><b>יונתן עמרני</b>' +
      '<a class="ig" href="https://www.instagram.com/amrani_yonatan.18/" target="_blank" rel="noopener" aria-label="יונתן עמרני באינסטגרם">' +
      '<span class="ig-l" dir="rtl">אינסטגרם</span>@amrani_yonatan.18</a></div>' +
      "</div></footer>";
  }
  function mount(active) {
    document.body.insertAdjacentHTML("afterbegin", header(active));
    document.body.insertAdjacentHTML("beforeend", footer());
  }
  function notFound(main, msg) {
    main.innerHTML = '<div class="wrap" style="padding:60px 16px"><h1>הדף לא נמצא</h1><p class="lede">' + esc(msg) +
      '</p><p><a class="btn" href="' + pageHref("index") + '">לכל מערכות הבחירות</a></p></div>';
  }

  window.App = {
    ELECTIONS: ELECTIONS, PEOPLE: PEOPLE, META: META, byKey: byKey,
    esc: esc, qs: qs, fmtDate: fmtDate, fmtMonth: fmtMonth, fmtInt: fmtInt, fmtSeats: fmtSeats, pctOf: pctOf, parseISO: parseISO,
    axisMid: axisMid, colorAt: colorAt, partyColor: partyColor, AXIS_HE: AXIS_HE, seatingOrder: seatingOrder,
    pageHref: pageHref, electionHref: electionHref, partyHref: partyHref, pollsHref: pollsHref, electionTitle: electionTitle, shortWhen: shortWhen,
    slip: slip, portrait: portrait, displayName: displayName, blocChip: blocChip, recText: recText,
    hemicycle: hemicycle, blocBar: blocBar, blocLegend: blocLegend,
    mount: mount, notFound: notFound
  };
})();
