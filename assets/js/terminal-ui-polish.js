(() => {
  "use strict";

  function mark() {
    document.body.classList.add("terminal-ds-active");

    document.querySelectorAll(".glass, .panel-card").forEach((el) => {
      el.classList.add("terminal-panel");
    });

    document.querySelectorAll("table").forEach((table) => {
      table.classList.add("terminal-data-table");
      table.querySelectorAll("td").forEach((td) => {
        const t = (td.textContent || "").trim();
        if (/^[+-]?(\$|NT\$)?\s?[\d,]+(\.\d+)?%?$/.test(t) || /^[+-]?\d+(\.\d+)?%$/.test(t)) {
          td.classList.add("terminal-number");
        }
      });
    });

    document.querySelectorAll(".text-2xl, .text-3xl, .text-4xl").forEach((el) => {
      if (/[0-9]/.test(el.textContent || "")) el.classList.add("terminal-number");
    });
  }

  const run = () => requestAnimationFrame(mark);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }

  let t = null;
  const obs = new MutationObserver(() => {
    clearTimeout(t);
    t = setTimeout(run, 120);
  });

  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
