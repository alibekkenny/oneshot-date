(() => {
  "use strict";

  const panels = Array.from(document.querySelectorAll(".panel"));
  let i = Math.max(0, panels.findIndex((p) => p.classList.contains("active")));

  const indexOfPanel = (name) => panels.findIndex((p) => p.dataset.panel === name);

  function show(n) {
    if (n < 0 || n >= panels.length) return;
    panels[i].classList.remove("active");
    i = n;
    panels[i].classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  document.querySelectorAll("[data-next]").forEach((b) =>
    b.addEventListener("click", () => show(i + 1))
  );
  document.querySelectorAll("[data-back]").forEach((b) =>
    b.addEventListener("click", () => show(i - 1))
  );

  // Multi-select option cards.
  document.querySelectorAll(".option").forEach((o) =>
    o.addEventListener("click", () => o.classList.toggle("selected"))
  );

  // "Something else…" cards reveal a free-text box for that step.
  document.querySelectorAll("[data-custom]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const step = btn.closest("[data-step-key]");
      const input = step && step.querySelector("[data-custom-input]");
      if (!input) return;
      const on = btn.classList.contains("selected"); // toggled by the handler above
      input.hidden = !on;
      if (on) input.focus();
      else input.value = "";
    })
  );

  // "When" step: single-select chips OR free-text (mutually exclusive).
  let whenChoice = "";
  const whenOther = document.getElementById("when-other");
  document.querySelectorAll("[data-when]").forEach((c) =>
    c.addEventListener("click", () => {
      document.querySelectorAll("[data-when]").forEach((x) => x.classList.remove("selected"));
      c.classList.add("selected");
      whenChoice = c.textContent.trim();
      if (whenOther) whenOther.value = "";
    })
  );
  if (whenOther) {
    whenOther.addEventListener("input", () => {
      if (whenOther.value.trim()) {
        document.querySelectorAll("[data-when]").forEach((x) => x.classList.remove("selected"));
        whenChoice = "";
      }
    });
  }

  const collect = (key) => {
    const step = document.querySelector(`[data-step-key="${key}"]`);
    if (!step) return [];
    // Selected preset options (skip the "Something else…" card itself).
    const values = Array.from(step.querySelectorAll(".option.selected"))
      .filter((o) => !o.hasAttribute("data-custom"))
      .map((o) => o.dataset.value);
    // Add her typed-in idea, if "Something else…" is selected and not empty.
    const customBtn = step.querySelector("[data-custom].selected");
    const customInput = step.querySelector("[data-custom-input]");
    if (customBtn && customInput && customInput.value.trim()) {
      values.push(customInput.value.trim());
    }
    return values;
  };

  const getWhen = () =>
    whenOther && whenOther.value.trim() ? whenOther.value.trim() : whenChoice;

  // Who this page is currently for (from the server-rendered template).
  const GIRL_NAME = (document.getElementById("wizard")?.dataset.girlName || "").trim();

  // The id (transient, used in-page) and opaque token (persisted) of the row
  // created when she first answers yes/no.
  let responseId = null;
  let responseToken = null;

  // Remember only her token + which girl this was for. The actual answers live
  // in the DB and are fetched back by token — Postgres stays the source of truth.
  const STORAGE_KEY = "oneshot_submission";
  function saveSubmission(token) {
    if (!token) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, girl_name: GIRL_NAME }));
    } catch (e) {}
  }
  function loadSubmission() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch (e) {
      return null;
    }
  }
  function clearSubmission() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  }

  function postJSON(url, body) {
    // Fire-and-forget: never block her UI on the network / a notification.
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((res) => res.json())
      .catch(() => null);
  }

  // Step 1: she taps Yes or No on the first page.
  // -> records the answer + sends Telegram message #1 immediately.
  document.querySelectorAll("[data-answer-start]").forEach((b) =>
    b.addEventListener("click", () => {
      const answer = b.dataset.answerStart;
      postJSON("/api/answer", { answer }).then((data) => {
        if (data && data.id) responseId = data.id;
        if (data && data.token) {
          responseToken = data.token;
          // "No" is final, so remember it now; "yes" is saved after the plan.
          if (answer === "no") saveSubmission(responseToken);
        }
      });
      if (answer === "yes") {
        show(indexOfPanel("yay"));
      } else {
        show(indexOfPanel("done-no"));
        launchRain();
      }
    })
  );

  // Final step: after the picks, she taps "all set".
  // -> saves the plan + sends Telegram message #2.
  document.querySelectorAll("[data-plan]").forEach((b) =>
    b.addEventListener("click", () => {
      const payload = {
        id: responseId,
        entertainment: collect("entertainment"),
        eating: collect("eating"),
        drinking: collect("drinking"),
        proposed_when: getWhen() || null,
      };
      postJSON("/api/plan", payload).then((data) => {
        saveSubmission((data && data.token) || responseToken);
      });
      fillRecap(payload);
      show(indexOfPanel("done-yes"));
      launchConfetti();
    })
  );

  function renderRecap(el, p) {
    if (!el) return;
    el.replaceChildren();
    // Build with textContent (not innerHTML) so free-typed values can't inject markup.
    const addRow = (label, val) => {
      const text = Array.isArray(val) ? val.join(", ") : val;
      if (!text) return;
      const row = document.createElement("div");
      row.className = "recap-row";
      const span = document.createElement("span");
      span.textContent = label;
      const b = document.createElement("b");
      b.textContent = text;
      row.append(span, b);
      el.appendChild(row);
    };
    addRow("What", p.entertainment);
    addRow("Eat", p.eating);
    addRow("Drink", p.drinking);
    addRow("When", p.proposed_when);
  }

  function fillRecap(p) {
    renderRecap(document.getElementById("recap-yes"), p);
  }

  function populateAlready(data) {
    const title = document.getElementById("already-title");
    const sub = document.getElementById("already-sub");
    const recap = document.getElementById("recap-already");
    if (data.answer === "no") {
      if (title) title.textContent = "You answered earlier 🙈";
      if (sub) sub.textContent = "You picked “maybe another time.” All good — no pressure.";
      if (recap) recap.replaceChildren();
      return;
    }
    if (title) title.textContent = "You already said yes 💘";
    if (sub) sub.textContent = "Here's the plan you put together:";
    renderRecap(recap, data);
  }

  // Returning visitor: if she already answered on this device, offer to view it.
  (function initReturning() {
    const prior = loadSubmission();
    // No prior answer on this device → nothing to show.
    if (!prior || !prior.token) return;
    // Page has since been repurposed for a different girl → the cache is stale,
    // so drop it (don't leak the previous girl's plan to a new visitor).
    if ((prior.girl_name || "") !== GIRL_NAME) {
      clearSubmission();
      return;
    }

    const btn = document.getElementById("returning-btn");
    if (btn) {
      btn.hidden = false;
      btn.addEventListener("click", () => {
        fetch("/api/response/" + encodeURIComponent(prior.token))
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => {
            if (!data) {
              // Row is gone (e.g. DB reset) → forget it and start fresh.
              clearSubmission();
              location.reload();
              return;
            }
            populateAlready(data);
            show(indexOfPanel("already"));
          })
          .catch(() => {});
      });
    }

    const restart = document.getElementById("restart-btn");
    if (restart) {
      restart.addEventListener("click", () => {
        clearSubmission();
        location.reload();
      });
    }
  })();

  function launchConfetti() {
    const wrap = document.getElementById("confetti");
    if (!wrap) return;
    const colors = ["#ff4d8b", "#ffd166", "#c8a2ff", "#8fe3b0", "#ff9dbd"];
    for (let n = 0; n < 80; n++) {
      const s = document.createElement("i");
      s.style.left = Math.random() * 100 + "%";
      s.style.background = colors[n % colors.length];
      s.style.animationDuration = 4 + Math.random() * 4 + "s";
      s.style.animationDelay = Math.random() * 1.5 + "s";
      if (n % 3 === 0) s.style.borderRadius = "50%";
      wrap.appendChild(s);
    }
  }

  function launchRain() {
    const wrap = document.getElementById("rain");
    if (!wrap || wrap.childElementCount) return;
    for (let n = 0; n < 60; n++) {
      const drop = document.createElement("i");
      drop.style.left = Math.random() * 100 + "%";
      drop.style.animationDuration = 0.6 + Math.random() * 0.9 + "s";
      drop.style.animationDelay = Math.random() * 2 + "s";
      drop.style.height = 12 + Math.random() * 14 + "px";
      wrap.appendChild(drop);
    }
  }
})();
