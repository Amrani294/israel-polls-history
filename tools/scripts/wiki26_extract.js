// Browser extract of the 2026 Wikipedia poll tables (for tools/data/wiki26_tables_raw.txt and
// tools/data/wiki26_refs_raw.txt). Run it in the browser console on
// https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Israeli_legislative_election
// It returns both texts and their djb2 hashes; save the texts without a trailing newline and put
// the hashes in TABLES_HASH / REFS_HASH in make_raw_2026.py (which checks them again).
//
// Rules (they reproduce the extracts of 14 and 20 Oct 2026 line for line):
// - the five poll tables are the 2nd to 6th "wikitable" on the page (the 1st lists the pollsters);
// - a cell's text is its textContent without footnote markers and <style>/<link> elements,
//   whitespace collapsed; '^cN' / '^rN' mark colspan / rowspan;
// - header rows (all <th>): the first two are H<t>1 and H<t>2, a later one with any text is X<t>;
// - a row with a cell spanning 15+ columns (outside a rowspan group) is an event row, E<t>;
// - every other row is a poll row, R<t>; scenario rows of a rowspan group start with the list cells;
// - citation line per poll row: 2026|date|firm|publisher|first external link of the first footnote
//   in the row that has one (scenario rows without a footnote take the group's), without https://.
(function () {
  var T = [].slice.call(document.querySelectorAll("table.wikitable"), 1, 6);
  function clean(c) {
    var k = c.cloneNode(true);
    k.querySelectorAll("sup.reference,style,link").forEach(function (s) { s.remove(); });
    return k.textContent.replace(/\s+/g, " ").trim();
  }
  function fmt(c) {
    var t = clean(c);
    if (c.colSpan > 1) t += "^c" + c.colSpan;
    if (c.rowSpan > 1) t += "^r" + c.rowSpan;
    return t;
  }
  function refUrl(row) {
    var as = row.querySelectorAll("sup.reference a");
    for (var i = 0; i < as.length; i++) {
      var li = document.getElementById(decodeURIComponent(as[i].getAttribute("href").slice(1)));
      var ex = li && li.querySelector("a.external");
      if (ex) return ex.href.replace(/^https?:\/\//, "");
    }
    return null;
  }
  var out = ["SOURCE|" + location.origin + location.pathname + "|rev " + mw.config.get("wgRevisionId")];
  var refs = [];
  T.forEach(function (t, ti) {
    var hn = 0, lead = null, left = 0;
    [].forEach.call(t.rows, function (r) {
      var cells = [].slice.call(r.cells);
      if (cells.every(function (c) { return c.tagName === "TH"; })) {
        hn++;
        if (hn <= 2) out.push("H" + ti + hn + "|" + cells.map(fmt).join("|"));
        else if (cells.some(function (c) { return clean(c); })) out.push("X" + ti + "|" + cells.map(fmt).join("|"));
        return;
      }
      if (left === 0 && cells.some(function (c) { return c.colSpan >= 15; })) {
        out.push("E" + ti + "|" + cells.map(fmt).join("|"));
        return;
      }
      out.push("R" + ti + "|" + cells.map(fmt).join("|"));
      var u = refUrl(r);
      if (left > 0) { left--; refs.push(["2026"].concat(lead.meta, [u || lead.u]).join("|")); }
      else {
        var m = cells.slice(0, 3).map(clean);
        left = cells[0].rowSpan - 1;
        lead = { meta: m, u: u };
        refs.push(["2026"].concat(m, [u]).join("|"));
      }
    });
  });
  function djb2(s) { var h = 5381; for (var ch of s) h = (h * 33 + ch.codePointAt(0)) % 1000000007; return h; }
  var tables = out.join("\n"), citations = refs.join("\n");
  return { tables: tables, tablesHash: djb2(tables), refs: citations, refsHash: djb2(citations) };
})();
