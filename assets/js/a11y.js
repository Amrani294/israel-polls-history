/* Accessibility settings (Yonatan, 10.11.2026): display theme (light / dark / follow the device),
   text size, high contrast, readable headings font, highlighted links, stopped motion, text spacing.

   Loaded in <head> of every page, before the body is drawn, so saved settings apply before the
   first paint (no flash of the light theme). The settings are classes and data attributes on
   <html>; main.css does the rest. The panel itself is opened from the button that
   App.mount() puts in the header (A11y.button() / A11y.bind()).

   Storage: the only browser storage on the site. One localStorage key ("a11y") holding these
   display preferences and nothing else; removed when everything is back to the defaults.
   Every read and write is wrapped in try/catch (storage can be blocked or full). */
(function () {
  "use strict";

  var KEY = "a11y";
  var THEMES = ["light", "dark", "auto"];
  var SIZES = [100, 115, 130, 150];           // percent of the browser's own text size
  var FLAGS = ["contrast", "font", "links", "still", "spacing"];
  var root = document.documentElement;
  var darkMedia = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  var motionMedia = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;

  // Whatever is stored is untrusted: keep only known values.
  function clean(s) {
    s = s && typeof s === "object" ? s : {};
    var out = {
      theme: THEMES.indexOf(s.theme) >= 0 ? s.theme : "light",
      size: (typeof s.size === "number" && s.size >= 0 && s.size < SIZES.length) ? Math.floor(s.size) : 0
    };
    FLAGS.forEach(function (f) { out[f] = s[f] === true; });
    return out;
  }
  function isDefault(s) {
    return s.theme === "light" && s.size === 0 && FLAGS.every(function (f) { return !s[f]; });
  }
  function load() {
    try { return clean(JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (err) { return clean({}); }
  }
  function save() {
    try {
      if (isDefault(state)) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, JSON.stringify(state));
    } catch (err) { /* blocked storage: the settings still apply to this page */ }
  }

  var state = load();

  function isDark() { return state.theme === "dark" || (state.theme === "auto" && !!darkMedia && darkMedia.matches); }
  function apply() {
    root.setAttribute("data-theme", isDark() ? "dark" : "light");
    if (state.size) root.setAttribute("data-size", String(state.size)); else root.removeAttribute("data-size");
    FLAGS.forEach(function (f) { root.classList.toggle("a11y-" + f, state[f]); });
  }
  // Pages that animate in script (the axes cube, the compass slides) ask this, and listen
  // for "a11ychange" to stop an animation that is already running.
  function reducedMotion() { return state.still || (!!motionMedia && motionMedia.matches); }
  function changed() {
    apply();
    save();
    sync();
    document.dispatchEvent(new CustomEvent("a11ychange", { detail: { reducedMotion: reducedMotion() } }));
  }

  apply();
  if (darkMedia && darkMedia.addEventListener) {
    darkMedia.addEventListener("change", function () { if (state.theme === "auto") changed(); });
  }
  // another tab changed the settings
  window.addEventListener("storage", function (ev) {
    if (ev.key === KEY || ev.key === null) { state = load(); apply(); sync(); }
  });

  /* ---------------------------------------------------------------- the panel */
  var THEME_HE = { light: "בהירה", dark: "כהה", auto: "לפי המכשיר" };
  var FLAG_HE = {
    contrast: ["ניגודיות גבוהה", "טקסט כהה יותר וקווים בולטים"],
    font: ["גופן קריא לכותרות", "כותרות בגופן הרגיל במקום הגופן הצר"],
    links: ["הדגשת קישורים", "קו תחתון לכל קישור ומסגרת בולטת במעבר מקלדת"],
    still: ["עצירת אנימציות", "בלי תנועה, החלקות וסיבוב הקובייה"],
    spacing: ["ריווח טקסט", "יותר רווח בין שורות, מילים ואותיות"]
  };
  var ICON = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">' +
    '<circle cx="12" cy="4.2" r="2.2" fill="currentColor"/>' +
    '<path d="M4 8.2c2.6.8 5.3 1.2 8 1.2s5.4-.4 8-1.2M12 9.4v5.2m0 0-3.3 7m3.3-7 3.3 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function button() {
    // the wrapper anchors the panel under the button
    return '<div class="a11y"><button type="button" class="a11y-btn" aria-expanded="false" aria-controls="a11y-panel">' + ICON +
      '<span class="a11y-btn-t">נגישות</span></button></div>';
  }
  function panelHTML() {
    var themes = THEMES.map(function (t) {
      return '<button type="button" data-theme-opt="' + t + '" aria-pressed="false">' + THEME_HE[t] + "</button>";
    }).join("");
    var sizes = SIZES.map(function (p, i) {
      return '<button type="button" data-size-opt="' + i + '" aria-pressed="false" aria-label="גודל טקסט ' + p + '%">' +
        '<span aria-hidden="true">א</span></button>';
    }).join("");
    var flags = FLAGS.map(function (f) {
      return '<button type="button" class="a11y-sw" role="switch" aria-checked="false" data-flag="' + f + '">' +
        '<span class="a11y-sw-t"><b>' + FLAG_HE[f][0] + "</b><small>" + FLAG_HE[f][1] + "</small></span>" +
        '<span class="a11y-track" aria-hidden="true"><span></span></span></button>';
    }).join("");
    return '<div class="a11y-panel" id="a11y-panel" role="dialog" aria-labelledby="a11y-title" hidden>' +
      '<div class="a11y-head"><h2 id="a11y-title">הגדרות נגישות</h2>' +
      '<button type="button" class="a11y-x" data-close>סגירה</button></div>' +
      '<div class="a11y-group" role="group" aria-labelledby="a11y-g-theme"><div class="a11y-gt" id="a11y-g-theme">תצוגה</div>' +
      '<div class="a11y-seg">' + themes + "</div></div>" +
      '<div class="a11y-group" role="group" aria-labelledby="a11y-g-size"><div class="a11y-gt" id="a11y-g-size">גודל טקסט <span class="a11y-val" aria-live="polite"></span></div>' +
      '<div class="a11y-seg a11y-sizes">' + sizes + "</div></div>" +
      '<div class="a11y-flags">' + flags + "</div>" +
      '<div class="a11y-foot"><button type="button" class="a11y-reset" data-reset>איפוס ההגדרות</button>' +
      '<p>ההגדרות נשמרות בדפדפן הזה בלבד.</p></div>' +
      "</div>";
  }

  var btn = null, panel = null;
  function sync() {
    if (!panel) return;
    panel.querySelectorAll("[data-theme-opt]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-theme-opt") === state.theme));
    });
    panel.querySelectorAll("[data-size-opt]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(Number(b.getAttribute("data-size-opt")) === state.size));
    });
    panel.querySelector(".a11y-val").textContent = SIZES[state.size] + "%";
    panel.querySelectorAll("[data-flag]").forEach(function (b) {
      b.setAttribute("aria-checked", String(state[b.getAttribute("data-flag")]));
    });
    panel.querySelector("[data-reset]").disabled = isDefault(state);
  }
  function isOpen() { return panel && !panel.hidden; }
  function open() {
    panel.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    var first = panel.querySelector('[aria-pressed="true"]') || panel.querySelector("button");
    if (first) first.focus();
  }
  function close(returnFocus) {
    if (!isOpen()) return;
    panel.hidden = true;
    btn.setAttribute("aria-expanded", "false");
    if (returnFocus) btn.focus();
  }

  // Called by App.mount() once the header is in the page.
  function bind(head) {
    btn = head.querySelector(".a11y-btn");
    if (!btn) return;
    btn.insertAdjacentHTML("afterend", panelHTML());
    panel = head.querySelector("#a11y-panel");
    sync();
    btn.addEventListener("click", function () { if (isOpen()) close(false); else open(); });
    panel.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b || !panel.contains(b)) return;
      if (b.hasAttribute("data-close")) { close(true); return; }
      if (b.hasAttribute("data-reset")) { state = clean({}); changed(); btn.focus(); close(false); return; }
      var t = b.getAttribute("data-theme-opt");
      if (t) { state.theme = t; changed(); return; }
      var s = b.getAttribute("data-size-opt");
      if (s != null) { state.size = Number(s); changed(); return; }
      var f = b.getAttribute("data-flag");
      if (f) { state[f] = !state[f]; changed(); }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && isOpen()) { ev.preventDefault(); close(true); }
    });
    // a click or tap anywhere else closes it
    document.addEventListener("pointerdown", function (ev) {
      if (isOpen() && !panel.contains(ev.target) && !btn.contains(ev.target)) close(false);
    });
    // keyboard focus leaving the panel closes it
    panel.addEventListener("focusout", function (ev) {
      var to = ev.relatedTarget;
      if (to && !panel.contains(to) && to !== btn) close(false);
    });
  }

  window.A11y = { button: button, bind: bind, reducedMotion: reducedMotion, isDark: isDark };
})();
