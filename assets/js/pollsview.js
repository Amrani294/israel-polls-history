/* The polls panel: used as a full page (polls.html) and as the slide-in drawer on election/party pages. */
(function () {
  "use strict";
  var A = window.App;
  var esc = A.esc;
  var POLLS = window.POLLS || [];

  function outletName(e, o) {
    var M = A.META;
    if ((M.oldElections || []).indexOf(e.key) >= 0 && M.predecessors && M.predecessors[o]) return M.predecessors[o];
    return (M.outlets || {})[o] || o;
  }
  function listByName(e, name) {
    for (var i = 0; i < e.lists.length; i++) if (e.lists[i].name === name) return e.lists[i];
    return null;
  }
  // size used for ordering: the result, or (before an election) the poll average
  function size(l) { return l.seats != null ? l.seats : (l.polls && l.polls.overall) || 0; }
  function trackedLists(e) {
    return e.tracked.map(function (n) { return listByName(e, n); }).filter(Boolean)
      .sort(function (a, b) { return size(b) - size(a); });
  }
  function outlets() { return Object.keys(A.META.outlets || {}); }

  /* ------------------------------------------------------------ time chart */
  function chart(e, polls) {
    var lists = trackedLists(e);
    var W = 860, H = 380, m = { l: 40, r: 70, t: 18, b: 34 };
    var t0 = A.parseISO(e.windowStart).getTime(), t1 = A.parseISO(e.date).getTime();
    var maxV = 0;
    polls.forEach(function (p) { lists.forEach(function (l) { var v = p.values[l.name]; if (v != null && v > maxV) maxV = v; }); });
    lists.forEach(function (l) { maxV = Math.max(maxV, l.seats || 0, l.exitAvg || 0); });
    maxV = Math.ceil((maxV + 2) / 5) * 5;
    function x(t) { return m.l + (W - m.l - m.r) * (t - t0) / (t1 - t0); }
    function y(v) { return H - m.b - (H - m.t - m.b) * v / maxV; }
    var g = [];
    for (var v = 0; v <= maxV; v += 5) {
      g.push('<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#e8eaef"/>');
      g.push('<text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" font-size="11" fill="#6b7385" text-anchor="end">' + v + "</text>");
    }
    // month ticks
    var d = A.parseISO(e.windowStart);
    d = new Date(d.getFullYear(), d.getMonth() + 1, 1);
    while (d.getTime() < t1) {
      var xx = x(d.getTime());
      g.push('<line x1="' + xx + '" x2="' + xx + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#eef0f4"/>');
      g.push('<text x="' + xx + '" y="' + (H - m.b + 18) + '" font-size="11" fill="#6b7385" text-anchor="middle">' +
        esc(d.toLocaleDateString("he-IL", { day: "numeric", month: "short" })) + "</text>");
      d = new Date(d.getFullYear(), d.getMonth() + 1, 1);
    }
    var xe = x(t1);
    g.push('<line x1="' + xe + '" x2="' + xe + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#18203a" stroke-dasharray="3 3"/>');
    g.push('<text x="' + xe + '" y="' + (H - m.b + 18) + '" font-size="11" fill="#18203a" text-anchor="middle" font-weight="600">יום הבחירות</text>');
    var pts = [];
    polls.forEach(function (p) {
      var t = A.parseISO(p.end).getTime();
      lists.forEach(function (l) {
        var v = p.values[l.name];
        if (v == null) return;
        pts.push('<circle data-p="' + esc(l.id) + '" cx="' + x(t).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="3.2" fill="' + A.partyColor(l) + '" fill-opacity="0.75"><title>' +
          esc(l.name + ": " + A.fmtSeats(v) + " | " + outletName(e, p.outlet) + ", " + A.fmtDate(p.end)) + "</title></circle>");
      });
    });
    var ends = [];
    if (e.upcoming) {
      var xa = x(A.parseISO(e.asOf).getTime());
      g.push('<line x1="' + xa + '" x2="' + xa + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#b9bfcc"/>');
      g.push('<text x="' + xa + '" y="' + (m.t + 10) + '" font-size="11" fill="#6b7385" text-anchor="end" dx="-4">עדכון אחרון</text>');
    }
    lists.forEach(function (l) {
      if (l.seats == null) return;
      var c = A.partyColor(l), yy = y(l.seats);
      ends.push('<rect data-p="' + esc(l.id) + '" x="' + (xe - 6) + '" y="' + (yy - 6) + '" width="12" height="12" transform="rotate(45 ' + xe + " " + yy + ')" fill="' + c + '" stroke="#fff" stroke-width="1.5"><title>' +
        esc(l.name + ": תוצאה " + l.seats) + "</title></rect>");
      if (l.exitAvg != null) {
        var ye = y(l.exitAvg);
        ends.push('<rect data-p="' + esc(l.id) + '" x="' + (xe + 10) + '" y="' + (ye - 5) + '" width="10" height="10" fill="#fff" stroke="' + c + '" stroke-width="2"><title>' +
          esc(l.name + ": ממוצע המדגמים " + A.fmtSeats(l.exitAvg)) + "</title></rect>");
      }
      ends.push('<text data-p="' + esc(l.id) + '" x="' + (xe + 26) + '" y="' + (yy + 4) + '" font-size="11" fill="' + c + '" font-weight="700">' + l.seats + "</text>");
    });
    var legend = lists.map(function (l) { return '<button type="button" aria-pressed="false" data-p="' + esc(l.id) + '" style="--pc:' + A.partyColor(l) + '">' + esc(l.name) + "</button>"; }).join("");
    return '<figure class="tsc" style="margin:0"><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="כל הסקרים בשלושת החודשים שלפני הבחירות, לפי מפלגה">' +
      g.join("") + pts.join("") + ends.join("") + "</svg>" +
      '<div class="lg">' + legend + '</div><figcaption class="small" style="margin-top:6px">כל נקודה היא סקר; לחיצה על שם רשימה מבליטה אותה. ' +
      (e.upcoming ? "הבחירות עוד לא התקיימו: הקו האפור הוא תאריך העדכון האחרון של הנתונים." : "ביום הבחירות: מעוין מלא = התוצאה, ריבוע חלול = ממוצע המדגמים.") + "</figcaption></figure>";
  }

  /* ------------------------------------------------------------ outlet table */
  function outletTable(e) {
    var lists = trackedLists(e), os = outlets();
    var head = "<tr><th>רשימה</th>" + os.map(function (o) { return '<th class="n">' + esc(outletName(e, o)) + "</th>"; }).join("") +
      '<th class="n">ממוצע הגופים</th>' + (e.upcoming ? "" : '<th class="n">ממוצע המדגמים</th><th class="n">תוצאה</th>') + "</tr>";
    var body = lists.map(function (l) {
      var p = l.polls || { outlets: {} };
      return "<tr><td><span class=\"party-cell\">" + A.slip(l, "sm") + esc(l.name) + "</span></td>" + os.map(function (o) {
        var d = p.outlets[o];
        return '<td class="n">' + (d && d.mean != null ? A.fmtSeats(d.mean) + ' <span class="small">(' + d.n + ")</span>" : "—") + "</td>";
      }).join("") + '<td class="n"><b>' + A.fmtSeats(p.overall) + "</b></td>" +
        (e.upcoming ? "" : '<td class="n">' + A.fmtSeats(l.exitAvg) + '</td><td class="n"><b>' + l.seats + "</b></td>") + "</tr>";
    }).join("");
    return '<div class="table-scroll"><table class="data"><thead>' + head + "</thead><tbody>" + body + "</tbody></table></div>" +
      '<p class="small" style="margin-top:6px">בסוגריים: מספר הסקרים בממוצע. ממוצע הגופים = ממוצע של ממוצעי הגופים (כל גוף במשקל שווה).</p>';
  }

  function blocTable(e) {
    var os = Object.keys(e.blocs.pollsByOutlet);
    var head = "<tr><th>גוף</th>" + e.blocOrder.map(function (b) { return '<th class="n">' + esc(e.blocLabels[b]) + "</th>"; }).join("") + '<th class="n">סקרים</th></tr>';
    var body = os.map(function (o) {
      var d = e.blocs.pollsByOutlet[o];
      return "<tr><td>" + esc(outletName(e, o)) + "</td>" + e.blocOrder.map(function (b) { return '<td class="n">' + A.fmtSeats(d[b]) + "</td>"; }).join("") + '<td class="n">' + d.n + "</td></tr>";
    }).join("");
    body += "<tr><td><b>ממוצע הגופים</b></td>" + e.blocOrder.map(function (b) { return '<td class="n"><b>' + A.fmtSeats(e.blocs.polls[b]) + "</b></td>"; }).join("") + '<td class="n">' + e.blocs.pollsUsed + "</td></tr>";
    if (!e.upcoming) {
      body += "<tr><td>ממוצע המדגמים</td>" + e.blocOrder.map(function (b) { return '<td class="n">' + A.fmtSeats(e.blocs.exit[b]) + "</td>"; }).join("") + '<td class="n">' + e.exitPolls.length + "</td></tr>";
      body += "<tr><td>תוצאה</td>" + e.blocOrder.map(function (b) { return '<td class="n"><b>' + e.blocs.final[b] + "</b></td>"; }).join("") + "<td></td></tr>";
    }
    return '<div class="table-scroll"><table class="data"><thead>' + head + "</thead><tbody>" + body + "</tbody></table></div>" +
      '<p class="small" style="margin-top:6px">בגושים נכללו רק סקרים שמסתכמים ב-120 מנדטים. השיוך לגוש לפי ' +
      (e.kind === "rec" ? "ההמלצות לנשיא (לא הוקמה ממשלה)." : e.kind === "pre" ? "מפלגות " + esc(e.outgoing.name) + " (הממשלה היוצאת) מול כל שאר הרשימות, עד שתקום ממשלה חדשה." :
        "הרכב הממשלה הראשונה שהושבעה אחרי הבחירות.") + "</p>";
  }

  /* ------------------------------------------------------------ poll source link */
  // The numbers' source (tools/data/primary_polls.txt): read from the outlet's own publication
  // ("במקור"), from another report of the poll ("דיווח משני"), or only from Wikipedia. Without a
  // check record: the citation Wikipedia gives for the poll, marked "ויקיפדיה".
  var CHECK_TAG = { src: ["src-tag ok", "נבדק במקור", "המספרים נקראו מהפרסום של הגוף עצמו"],
    sec: ["src-tag sec", "נבדק בדיווח משני", "הפרסום המקורי לא נמצא; המספרים נבדקו מול דיווח אחר על הסקר"],
    none: ["src-tag", "ויקיפדיה", "לא נמצא פרסום זמין לבדיקה; המספרים מוויקיפדיה"] };
  function sourceLink(p) {
    var c = p.check;
    if (c) {
      var t = CHECK_TAG[c.k], url = c.url || (p.ref && /^https?:\/\//i.test(p.ref.url) ? p.ref.url : p.src);
      var host = url.replace(/^https?:\/\/(www\.)?/i, "").split("/")[0];
      return '<a href="' + esc(url) + '" target="_blank" rel="noopener" title="' + esc(t[2]) + '">' + esc(p.publisher) + '</a> <span class="src-host">' + esc(host) + "</span>" +
        ' <span class="' + t[0] + '" title="' + esc(t[2]) + '">' + t[1] + "</span>" + (c.added ? ' <span class="src-tag sec">עוד לא בוויקיפדיה</span>' : "");
    }
    var r = p.ref;
    if (r && !/^https?:\/\//i.test(r.url)) r = null;   // only plain web links
    if (!r) return '<a href="' + esc(p.src) + '" target="_blank" rel="noopener">' + esc(p.publisher) + '</a> <span class="src-tag">ויקיפדיה</span>';
    var tag = r.original ? (r.archived ? "ארכיון" : "") : "דיווח משני";
    return '<a href="' + esc(r.url) + '" target="_blank" rel="noopener" title="' + esc((r.original ? "הפרסום המקורי" : "דיווח משני על הסקר") + ": " + r.host + (r.archived ? " (עותק בארכיון האינטרנט)" : "")) + '">' +
      esc(p.publisher) + '</a> <span class="src-host">' + esc(r.host) + "</span>" + (tag ? ' <span class="src-tag' + (r.original ? "" : " sec") + '">' + tag + "</span>" : "");
  }

  /* ------------------------------------------------------------ poll rows */
  function pollRows(e, polls) {
    var lists = trackedLists(e);
    var head = '<tr><th>תאריך</th><th>גוף</th><th>מפרסם במקור</th><th>מכון</th>' +
      lists.map(function (l) { return '<th class="n" title="' + esc(l.name) + '">' + esc(l.name) + "</th>"; }).join("") +
      e.blocOrder.map(function (b) { return '<th class="n">' + esc(e.blocLabels[b]) + "</th>"; }).join("") + '<th class="n">סכום</th><th>הערות</th></tr>';
    var body = polls.map(function (p) {
      var notes = [];
      var cells = lists.map(function (l) {
        var v = p.values[l.name], n = p.valueNotes[l.name];
        var d = p.check && p.check.diffs.filter(function (x) { return x[0] === l.name; })[0];
        if (d) return '<td class="n flag" title="' + esc("לפי הפרסום המקורי; בוויקיפדיה " + A.fmtSeats(d[1])) + '">' + A.fmtSeats(v) + '<span class="note-mark">*</span></td>';
        if (n) { notes.push(l.name + ": " + n); return '<td class="n flag" title="' + esc(n) + '">' + A.fmtSeats(v) + '<span class="note-mark">*</span></td>'; }
        return '<td class="n">' + A.fmtSeats(v) + "</td>";
      }).join("");
      if (p.outletNote) notes.push(p.outletNote);
      (p.blocNotes || []).forEach(function (n) { notes.push(n); });
      if (p.check) {
        p.check.diffs.forEach(function (d) { notes.push(d[0] + ": לפי הפרסום המקורי " + A.fmtSeats(d[2]) + ", בוויקיפדיה " + A.fmtSeats(d[1])); });
        if (p.check.note) notes.push(p.check.note);
      }
      var off = p.total !== 120;
      if (off) notes.push("הסכום אינו 120 – הסקר לא נכלל במפת הגושים");
      return "<tr><td>" + esc(A.fmtDate(p.end, { day: "numeric", month: "numeric", year: "2-digit" })) + "</td><td>" + esc(outletName(e, p.outlet)) +
        "</td><td>" + sourceLink(p) + "</td><td>" + esc(p.firm || "—") + "</td>" + cells +
        e.blocOrder.map(function (b) { return '<td class="n">' + A.fmtSeats(p.blocs[b]) + "</td>"; }).join("") +
        '<td class="n' + (off ? " flag" : "") + '">' + A.fmtSeats(p.total) + '</td><td class="wrapcell small">' + esc(notes.join("; ")) + "</td></tr>";
    }).join("");
    return '<div class="table-scroll" style="max-height:70vh"><table class="data"><thead>' + head + "</thead><tbody>" + body + "</tbody></table></div>";
  }

  function exitTable(e) {
    var lists = e.lists.slice().sort(function (a, b) { return b.seats - a.seats; });
    var head = "<tr><th>רשימה</th>" + e.exitPolls.map(function (x) { return '<th class="n">' + esc(x.actual) + "</th>"; }).join("") +
      '<th class="n">ממוצע</th><th class="n">תוצאה</th></tr>';
    var body = lists.map(function (l) {
      return "<tr" + (l.seats ? "" : ' class="below"') + '><td><span class="party-cell">' + A.slip(l, "sm") + esc(l.name) + "</span></td>" +
        e.exitPolls.map(function (x) { return '<td class="n">' + A.fmtSeats(x.seats[l.name]) + "</td>"; }).join("") +
        '<td class="n">' + A.fmtSeats(l.exitAvg) + '</td><td class="n"><b>' + l.seats + "</b></td></tr>";
    }).join("");
    var foot = e.exitPolls.map(function (x) {
      var flag = x.version.indexOf("עדכון לילי") !== 0;
      return "<li><b>" + esc(x.actual) + "</b>: " + esc(x.version) + (x.time ? ", " + esc(x.time) : "") + (x.note ? ". " + esc(x.note) : "") +
        ' <a href="' + esc(x.source) + '" target="_blank" rel="noopener">מקור</a>' +
        (x.more || []).map(function (u, i) { return ' <a href="' + esc(u) + '" target="_blank" rel="noopener">מקור ' + (i + 2) + "</a>"; }).join("") + (flag ? ' <span class="chip" style="background:var(--flag)">לא העדכון הלילי</span>' : "") + "</li>";
    }).join("");
    return '<div class="table-scroll"><table class="data"><thead>' + head + "</thead><tbody>" + body + '</tbody></table></div><ul class="notes" style="margin-top:10px">' + foot + "</ul>";
  }

  /* ------------------------------------------------------------ CSV */
  function csv(e, polls) {
    var lists = trackedLists(e);
    var rows = [["מערכת", "תאריך סיום", "תאריך במקור", "גוף", "מפרסם במקור", "מכון"].concat(lists.map(function (l) { return l.name; }))
      .concat(e.blocOrder.map(function (b) { return e.blocLabels[b]; })).concat(["סכום", "הערות", "מקור"])];
    polls.forEach(function (p) {
      var notes = lists.filter(function (l) { return p.valueNotes[l.name]; }).map(function (l) { return l.name + ": " + p.valueNotes[l.name]; });
      if (p.outletNote) notes.push(p.outletNote);
      rows.push([A.electionTitle(e), p.end, p.dateText, outletName(e, p.outlet), p.publisher, p.firm]
        .concat(lists.map(function (l) { var v = p.values[l.name]; return v == null ? "" : v; }))
        .concat(e.blocOrder.map(function (b) { return p.blocs[b]; })).concat([p.total, notes.join("; "), p.check && p.check.url ? p.check.url : p.ref ? p.ref.url : p.src]));
    });
    return "﻿" + rows.map(function (r) {
      return r.map(function (c) {
        c = String(c == null ? "" : c);
        // a text cell starting with = + - @ would run as a formula in Excel: prefix it with '
        if (typeof c === "string" && /^[=+\-@\t\r]/.test(c) && !/^-?\d+(\.\d+)?$/.test(c)) c = "'" + c;
        return /[",\n\r]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c;
      }).join(",");
    }).join("\r\n");
  }

  /* ------------------------------------------------------------ render */
  function render(root, key, opts) {
    opts = opts || {};
    var e = A.byKey[key];
    if (!e) { root.innerHTML = '<p class="lede">לא נמצאה מערכת בחירות בשם הזה.</p>'; return; }
    var all = POLLS.filter(function (p) { return p.e === key; });
    var os = outlets().filter(function (o) { return all.some(function (p) { return p.outlet === o; }); });
    var h = opts.headingTag || "h2";
    root.innerHTML =
      '<div class="panel-intro"><p>' + (e.upcoming ? "<b>לפני הבחירות.</b> הנתונים עודכנו ב-" + esc(A.fmtDate(e.asOf)) + "; הסקר האחרון שנכלל: " + esc(A.fmtDate(e.lastPoll)) + ". " : "") +
      "סקרי שלושת החודשים שלפני " + esc(A.electionTitle(e)) + " (" + esc(A.fmtDate(e.windowStart)) + " – " + esc(A.fmtDate(e.date)) +
      "), של כאן 11, חדשות 12, חדשות 13, מעריב והארץ" + ((A.META.oldElections || []).indexOf(key) >= 0 ? " (ובמקום הערוצים: ערוץ 1, ערוץ 2 וערוץ 10)" : "") +
      ". כל סקר משויך לתאריך סיום העבודה עליו. " + all.length + ' סקרים. <a href="' + esc(e.pollSrc) + '" target="_blank" rel="noopener">מקור הטבלאות</a>.</p></div>' +
      "<" + h + ">כל הסקרים</" + h + ">" + '<div style="margin:12px 0 26px">' + chart(e, all) + "</div>" +
      "<" + h + ">ממוצע לפי גוף</" + h + '><div style="margin:12px 0 26px">' + outletTable(e) + "</div>" +
      "<" + h + ">גושים בסקרים</" + h + '><div style="margin:12px 0 26px">' + blocTable(e) + "</div>" +
      (e.upcoming ? "" : "<" + h + ">מדגמי ליל הבחירות</" + h + '><div style="margin:12px 0 26px">' + exitTable(e) + "</div>") +
      "<" + h + ">סקר אחר סקר</" + h + ">" +
      '<div class="filters"><label for="pf-' + key + '">גוף</label><select id="pf-' + key + '"><option value="">כל הגופים</option>' +
      os.map(function (o) { return '<option value="' + o + '">' + esc(outletName(e, o)) + "</option>"; }).join("") + "</select>" +
      '<button class="btn ghost" type="button" data-csv>הורדה כ-CSV</button>' +
      '<span class="small">לחיצה על שם המפרסם פותחת את הפרסום של הסקר (כשאין פרסום מקורי זמין: דיווח משני, מסומן). תא צהוב = ערך שעבר טיפול (סכימה לפני איחוד, אמצע טווח, תרחיש וכו\'), עם הסבר בעמודת ההערות.</span></div>' +
      '<div data-rows>' + pollRows(e, all) + "</div>" +
      (e.notes && e.notes.length ? "<" + h + ' style="margin-top:26px">הערות למערכת זו</' + h + '><ul class="notes">' + e.notes.map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("") + "</ul>" : "");
    var fig = root.querySelector(".tsc");
    fig.querySelectorAll(".lg button").forEach(function (b) {
      b.addEventListener("click", function () {
        var on = b.getAttribute("aria-pressed") !== "true";
        fig.querySelectorAll(".lg button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", String(on));
        var id = on ? b.getAttribute("data-p") : null;
        fig.querySelectorAll("svg [data-p]").forEach(function (n) {
          n.style.opacity = !id || n.getAttribute("data-p") === id ? "" : "0.08";
        });
      });
    });
    var sel = root.querySelector("select");
    var cur = all;
    sel.addEventListener("change", function () {
      cur = sel.value ? all.filter(function (p) { return p.outlet === sel.value; }) : all;
      root.querySelector("[data-rows]").innerHTML = pollRows(e, cur);
    });
    root.querySelector("[data-csv]").addEventListener("click", function () {
      var blob = new Blob([csv(e, cur)], { type: "text/csv;charset=utf-8" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "polls-" + key + (sel.value ? "-" + sel.value : "") + ".csv";
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
  }

  /* ------------------------------------------------------------ drawer */
  var drawer, backdrop, lastFocus;
  function openDrawer(key) {
    var e = A.byKey[key];
    if (!drawer) {
      backdrop = document.createElement("div");
      backdrop.className = "drawer-backdrop";
      drawer = document.createElement("aside");
      drawer.className = "drawer";
      drawer.setAttribute("role", "dialog");
      drawer.setAttribute("aria-modal", "true");
      drawer.setAttribute("aria-labelledby", "drawer-title");
      drawer.innerHTML = '<div class="d-head"><h2 id="drawer-title"></h2><a class="small" style="color:#dfe3ee" data-full>לעמוד הסקרים המלא</a><button class="x" type="button">סגירה</button></div><div class="d-body"></div>';
      document.body.appendChild(backdrop);
      document.body.appendChild(drawer);
      backdrop.addEventListener("click", closeDrawer);
      drawer.querySelector(".x").addEventListener("click", closeDrawer);
      document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && drawer.classList.contains("open")) closeDrawer(); });
    }
    lastFocus = document.activeElement;
    drawer.querySelector("#drawer-title").textContent = "הסקרים – " + A.electionTitle(e);
    drawer.querySelector("[data-full]").setAttribute("href", A.pollsHref(key));
    render(drawer.querySelector(".d-body"), key, { headingTag: "h3" });
    drawer.classList.add("open");
    backdrop.classList.add("open");
    document.body.style.overflow = "hidden";
    drawer.querySelector(".x").focus();
  }
  function closeDrawer() {
    drawer.classList.remove("open");
    backdrop.classList.remove("open");
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  window.PollsView = { render: render, open: openDrawer, outletName: outletName, sourceLink: sourceLink };
})();
