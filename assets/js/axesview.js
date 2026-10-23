/* The three-axis map (data/axes.js): shared pieces for the map page and the party page. */
(function () {
  "use strict";
  var A = window.App, esc = A.esc, AX = window.AXES;
  if (!AX) { window.AxesView = null; return; }

  var BY_AXIS = Object.create(null);
  AX.axes.forEach(function (a) { BY_AXIS[a.key] = a; });

  // short names for crowded charts
  var SHORT = { "reservists-nep": "המילואימניקים", "rzp": "הציונות הדתית", "joint-list": "המשותפת", "amcha-yisrael": "עמך ישראל", "democrats": "הדמוקרטים" };
  function shortName(l) { return SHORT[l.id] || l.name; }

  function host(u) {
    try { return new URL(u).hostname.replace(/^(www|m)\./, ""); } catch (err) { return u; }
  }
  function anchorFor(a, ind, score) {
    // the anchor text nearest to the score (for the tooltip)
    var at = AX.anchorsAt, best = 0;
    for (var i = 1; i < at.length; i++) if (Math.abs(at[i] - score) < Math.abs(at[best] - score)) best = i;
    return ind.anchors[best];
  }

  // a 0-10 track with a dot (or a dashed track when unknown)
  function track(score, color) {
    if (score == null) return '<span class="ax-track unknown" title="אין מספיק ראיות"></span>';
    return '<span class="ax-track"><span class="ax-dot" style="inset-inline-start:calc(' + (score * 10) + '% - 7px);--pc:' + color + '"></span></span>';
  }
  function scoreText(score) { return score == null ? "לא ידוע" : String(score); }

  /* the party page section */
  function listSection(e, l, color) {
    var d = AX.lists[l.id];
    if (!d || String(e.key) !== String(AX.election)) return "";
    var parts = AX.axes.map(function (a) {
      var ax = d.axes[a.key];
      var inds = a.indicators.map(function (ind) {
        var v = ax.ind[ind.key];
        if (!v) return '<li class="none"><span class="nm">' + esc(ind.he) + '</span><span class="sc">—</span><span class="tx">אין ראיות</span></li>';
        return '<li><span class="nm">' + esc(ind.he) + '</span><span class="sc" title="' + esc("העוגן הקרוב: " + anchorFor(a, ind, v.score)) + '">' + v.score + "</span>" +
          '<span class="tx">' + esc(v.text) + ' <span class="src">' + v.urls.map(function (u) {
            return '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(host(u)) + "</a>";
          }).join(" · ") + "</span></span></li>";
      }).join("");
      return '<div class="ax-card"><div class="ax-head"><h3>' + esc(a.he) + '</h3><span class="ax-score">' + scoreText(ax.score) +
        (ax.score == null ? "" : '<small>/10</small>') + "</span></div>" +
        '<div class="ax-scale"><span>' + esc(a.lo) + "</span>" + track(ax.score, color) + "<span>" + esc(a.hi) + "</span></div>" +
        (ax.score == null ? '<p class="small">ראיות על ' + ax.n + " מדד" + (ax.n === 1 ? "" : "ים") + " בלבד; צריך לפחות שניים.</p>" : "") +
        '<ul class="ax-ind">' + inds + "</ul></div>";
    }).join("");
    return '<section class="block" id="axes"><div class="wrap"><header><h2>שלושת הצירים</h2>' +
      '<p>הערכה של האתר, לפי מדדים ועוגנים קבועים; לכל ציון יש מקור. <a href="' + A.pageHref("axes") + '">מפת הצירים והשיטה</a></p></header>' +
      (d.note ? '<p class="small ax-note">' + esc(d.note) + "</p>" : "") +
      '<div class="ax-cards">' + parts + "</div></div></section>";
  }

  /* the anchors, for the method section */
  function anchorsTables() {
    return AX.axes.map(function (a) {
      return '<div class="ax-anchors"><h3>' + esc(a.he) + ": " + esc(a.lo) + " (0) עד " + esc(a.hi) + " (10)</h3>" +
        '<p class="small">' + esc(a.scope) + "</p>" +
        '<div class="table-scroll"><table><thead><tr><th>מדד</th>' + AX.anchorsAt.map(function (v) { return "<th>" + v + "</th>"; }).join("") + "</tr></thead><tbody>" +
        a.indicators.map(function (ind) {
          return "<tr><th>" + esc(ind.he) + "</th>" + ind.anchors.map(function (t) { return "<td>" + esc(t) + "</td>"; }).join("") + "</tr>";
        }).join("") + "</tbody></table></div></div>";
    }).join("");
  }

  window.AxesView = {
    AX: AX, BY_AXIS: BY_AXIS, shortName: shortName, track: track, scoreText: scoreText,
    listSection: listSection, anchorsTables: anchorsTables
  };
})();
