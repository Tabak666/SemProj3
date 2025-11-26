// desk.js — unified, robust, auto-refreshing script

// --------------------------- Utilities ---------------------------
function safeGet(id) { return document.getElementById(id); }
function hasClass(el, cls) { return el && el.classList && el.classList.contains(cls); }

// CSRF helper (reads cookie; works even after dynamic HTML replacement)
function getCookie(name) {
  const v = document.cookie.split('; ').find(row => row.startsWith(name + '='));
  return v ? decodeURIComponent(v.split('=')[1]) : null;
}
const CSRF_TOKEN = getCookie('csrftoken');

// --------------------------- Height / Popup ---------------------------
const slider = safeGet("heightSlider");
const valueLabel = safeGet("heightValue");
const popup = safeGet("healthPopup");
const message = safeGet("healthMessage");
const acceptBtn = safeGet("acceptBtn");
const ignoreBtn = safeGet("ignoreBtn");
const toggleHealth = safeGet("toggleHealth");

// USER_HEIGHT_CM must be injected server-side in index.html before this script loads.
// e.g. <script>const USER_HEIGHT_CM = {{ user_height|default:"176" }};</script>
if (typeof USER_HEIGHT_CM === 'undefined') {
  window.USER_HEIGHT_CM = 176;
}

function getSittingHeight(h) { return h / 2.48; }
function getStandingHeight(h) { return h / 1.58; }

const sittingHeight = Math.round(getSittingHeight(USER_HEIGHT_CM));
const standingHeight = Math.round(getStandingHeight(USER_HEIGHT_CM));
const MARGIN = 4;

let currentRecommendation = null;
let sittingTimer = null;
let sittingTimeSeconds = 0;
const SITTING_ALERT_DELAY = 10;

// safety guard: elements may not exist on every page
function ensureElementListeners() {
  if (!slider || !valueLabel || !popup || !acceptBtn || !ignoreBtn || !toggleHealth) return;
  // set initial displayed value
  valueLabel.textContent = slider.value;
}

ensureElementListeners();

// --- Sitting timer helpers ---
function startSittingTimer() {
  if (sittingTimer) return;
  sittingTimeSeconds = 0;
  sittingTimer = setInterval(() => {
    sittingTimeSeconds++;
    if (sittingTimeSeconds === SITTING_ALERT_DELAY) {
      showSittingReminder();
    }
  }, 1000);
}
function resetSittingTimer() {
  clearInterval(sittingTimer);
  sittingTimer = null;
  sittingTimeSeconds = 0;
}

// --- Popup helpers ---
function setPopupButtons(left, right) {
  if (!acceptBtn || !ignoreBtn) return;
  acceptBtn.textContent = left || "Accept";
  ignoreBtn.textContent = right || "Ignore";
  acceptBtn.style.display = left ? "inline-block" : "none";
  ignoreBtn.style.display = right ? "inline-block" : "none";
}
function showPopup() { popup && popup.classList.add("show"); }
function hidePopup() {
  if (!popup) return;
  popup.classList.remove("show", "low", "high", "correct", "standing", "sitting");
  currentRecommendation = null;
  setPopupButtons("Accept", "Ignore");
}
function showSittingReminder() {
  if (!message) return;
  const hoursSat = 4.2;
  message.textContent = `🪑 Consider standing more: You've been sitting for ${hoursSat.toFixed(1)} hours today.`;
  setPopupButtons("Stand up", "Cancel");
  popup.classList.add("sitting");
  currentRecommendation = "sittingReminder";
  showPopup();
}

// --- Slider logic (guarding existence of slider & toggle) ---
if (slider && valueLabel && toggleHealth) {
  slider.addEventListener("input", () => {
    const height = parseInt(slider.value);
    valueLabel.textContent = height;

    // Check for any active desk in the ephemeral frontend state
    const hasActiveDesk = Object.values(window.desks || {}).some(d => d.status === "booked" || d.status === "paired");

    if (!hasActiveDesk || !toggleHealth.checked) {
      hidePopup();
      resetSittingTimer();
      return;
    }

    popup && popup.classList.remove("low", "high", "correct", "standing", "sitting");

    if (height < sittingHeight - MARGIN) {
      message.textContent = `⚠️ Too low. Recommended: ${sittingHeight - MARGIN}–${sittingHeight + MARGIN} cm`;
      popup.classList.add("low");
      currentRecommendation = "low";
      setPopupButtons("Adjust", "Ignore");
      showPopup();
      resetSittingTimer();
    } else if (height <= sittingHeight + MARGIN) {
      message.textContent = "✅ Good sitting height.";
      popup.classList.add("correct");
      currentRecommendation = "correct";
      setPopupButtons("OK", "");
      showPopup();
      startSittingTimer();
    } else if (height <= standingHeight + MARGIN) {
      message.textContent = "⁉️ Near standing. Choose:";
      popup.classList.add("standing");
      currentRecommendation = "standingChoice";
      setPopupButtons("Sitting", "Standing");
      showPopup();
      resetSittingTimer();
    } else {
      message.textContent = `⚠️ Too high. Standing recommended: ${standingHeight - MARGIN}–${standingHeight + MARGIN} cm`;
      popup.classList.add("high");
      currentRecommendation = "high";
      setPopupButtons("Adjust", "Ignore");
      showPopup();
      resetSittingTimer();
    }
  });
}

// Popup action buttons
acceptBtn && acceptBtn.addEventListener("click", () => {
  if (currentRecommendation === "low") {
    slider.value = sittingHeight;
    valueLabel.textContent = sittingHeight;
  } else if (currentRecommendation === "high" || currentRecommendation === "sittingReminder") {
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
  } else if (currentRecommendation === "standingChoice") {
    slider.value = sittingHeight;
    valueLabel.textContent = sittingHeight;
  }
  hidePopup();
});
ignoreBtn && ignoreBtn.addEventListener("click", () => {
  if (currentRecommendation === "standingChoice") {
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
  }
  hidePopup();
});

// --------------------------- Profiles / Config / Status ---------------------------
document.querySelectorAll(".profile-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const h = btn.dataset.height;
    if (slider && valueLabel) {
      slider.value = h;
      valueLabel.textContent = h;
    }
  });
});

function setStatusMessage(msg, type = "info") {
  const box = safeGet("statusMessage");
  if (!box) return;
  box.textContent = msg;
  box.className = "status-message " + type;
  box.style.display = "block";
  clearTimeout(setStatusMessage._t);
  setStatusMessage._t = setTimeout(() => {
    box.style.display = "none";
  }, 4000);
}

// --------------------------- Desk selection / backend pairing ---------------------------
const reservationActions = safeGet("reservationActions");
const pairBtn = safeGet("pairBtn");
const unpairBtn = safeGet("unpairBtn");
const showBooking = safeGet("showBooking");
const bookingForm = safeGet("bookingForm");
const bookBtn = safeGet("bookBtn");
const cancelBooking = safeGet("cancelBooking");
const bookStart = safeGet("bookStart");
const bookEnd = safeGet("bookEnd");

window.desks = window.desks || {}; // ephemeral local state (not authoritative)

// event delegation for desk clicks (works after refreshs because listener attached to #main-content)
document.getElementById("main-content")?.addEventListener("click", (e) => {
  const btn = e.target.closest(".btn");
  if (!btn) return;

  // read desk id from data attribute
  const deskId = btn.dataset.deskId;
  if (!deskId) return; // empty slots

  const selectedDesk = safeGet("selectedDesk");
  selectedDesk && (selectedDesk.textContent = `Selected Desk: ${deskId}`);

  if (reservationActions) reservationActions.style.display = "block";
  if (reservationActions) reservationActions.dataset.currentDesk = deskId;

  // Ask backend whether this user is paired to the desk
  fetch(`/api/user-status/${encodeURIComponent(deskId)}/`)
    .then(res => res.json())
    .then(data => {
      if (pairBtn) pairBtn.disabled = !!data.is_paired;
      if (unpairBtn) unpairBtn.disabled = !data.is_paired;
    })
    .catch(err => {
      // Fail gracefully — keep pair/unpair as-is
      console.warn("user-status check failed", err);
    });
});

// Pair desk (POST)
pairBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  const deskId = reservationActions?.dataset?.currentDesk;
  if (!deskId) return setStatusMessage("No desk selected.", "error");

  const formData = new FormData();
  formData.append("desk_id", deskId);

  fetch("/pair_desk/", {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN },
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    setStatusMessage(data.message, data.success ? "success" : "error");
    if (data.success) {
      if (pairBtn) pairBtn.disabled = true;
      if (unpairBtn) unpairBtn.disabled = false;
      // mark ephemeral state
      window.desks = window.desks || {};
      window.desks[deskId] = { status: "paired", start: new Date().toLocaleString() };
    }
  })
  .catch(err => setStatusMessage("Pair request failed.", "error"));
});

// Unpair desk (POST)
unpairBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  const deskId = reservationActions?.dataset?.currentDesk;
  if (!deskId) return setStatusMessage("No desk selected.", "error");

  const formData = new FormData();
  // In your backend unpair_desk_view only checks session user — no desk_id required.
  fetch("/unpair_desk/", {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN },
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    setStatusMessage(data.message, data.success ? "success" : "error");
    if (data.success) {
      if (pairBtn) pairBtn.disabled = false;
      if (unpairBtn) unpairBtn.disabled = true;
      // update ephemeal state
      if (window.desks && window.desks[deskId]) delete window.desks[deskId];
    }
  })
  .catch(err => setStatusMessage("Unpair request failed.", "error"));
});

// Booking UI (local only — backend implementation pending)
showBooking?.addEventListener("click", () => bookingForm && (bookingForm.style.display = "block"));
cancelBooking?.addEventListener("click", () => {
  if (!bookingForm) return;
  bookingForm.style.display = "none";
  if (bookStart) bookStart.value = "";
  if (bookEnd) bookEnd.value = "";
});
bookBtn?.addEventListener("click", () => {
  const deskId = reservationActions?.dataset?.currentDesk;
  if (!deskId) return setStatusMessage("Select a desk first.", "error");
  if (!bookStart?.value || !bookEnd?.value) return setStatusMessage("Please select start and end time.", "error");

  window.desks[deskId] = { status: "booked", start: bookStart.value, end: bookEnd.value };
  bookingForm.style.display = "none";
  setStatusMessage(`Desk ${deskId} booked from ${bookStart.value} to ${bookEnd.value}`);
  if (pairBtn) pairBtn.disabled = true;
  if (unpairBtn) unpairBtn.disabled = false;
  bookStart.value = "";
  bookEnd.value = "";
});

// --------------------------- View switching ---------------------------
// Keep one listener on view buttons and handle "active" class
function initViewButtons() {
  document.querySelectorAll(".view-btn").forEach(button => {
    // avoid double attaching: remove previous handler by cloning technique
    const clone = button.cloneNode(true);
    button.parentNode.replaceChild(clone, button);
  });

  document.querySelectorAll(".view-btn").forEach(button => {
    button.addEventListener("click", () => {
      // toggle active class
      document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
      button.classList.add("active");

      const view = button.dataset.view;
      fetch(`/load_view/${view}/`)
        .then(res => res.text())
        .then(html => {
          const main = document.getElementById("main-content");
          if (!main) return;
          main.innerHTML = html;
          // ensure any overview code re-initializes
          document.dispatchEvent(new Event("viewChanged"));
          document.dispatchEvent(new Event("overviewLoaded"));
        })
        .catch(err => console.error("Failed to load view:", err));
    });
  });
}
initViewButtons();

// If no active view is marked on load, mark Desks as active (index shows A by default)
document.addEventListener("DOMContentLoaded", () => {
  if (!document.querySelector(".view-btn.active")) {
    const btn = document.querySelector('.view-btn[data-view="desks"]');
    if (btn) btn.classList.add("active");
  }
});

// --------------------------- Auto-refresh logic ---------------------------
// Try to keep the currently visible room (if any) when refreshing
async function autoRefreshDesks() {
  const activeViewBtn = document.querySelector(".view-btn.active");
  const activeView = activeViewBtn ? activeViewBtn.dataset.view : null;
  if (activeView !== "desks") return; // only when desks view active

  // find currently visible room wrapper id (room-A, room-B, ...)
  const currentRoomWrapper = document.querySelector(".room-wrapper");
  const roomId = currentRoomWrapper ? currentRoomWrapper.id.replace(/^room-/, "") : null;

  let url = "/load_view/desks/";
  if (roomId) url += `?room=Room%20${encodeURIComponent(roomId)}`; // matches your view filter format sometimes "Room A"

  try {
    const res = await fetch(url, { cache: "no-store" });
    const html = await res.text();
    const main = document.getElementById("main-content");
    if (!main) return;

    // quick compare — if identical, skip DOM replacement
    if (main.innerHTML.trim() === html.trim()) {
      return;
    }

    main.innerHTML = html;

    // re-run view button init (they live outside main-content but we ensure everything wired)
    initViewButtons();

    // re-dispatch overviewLoaded so overview navigation logic reattaches listeners
    document.dispatchEvent(new Event("overviewLoaded"));

    // If a desk is currently selected, re-check its pairing status with backend (to sync)
    const selectedDeskId = reservationActions?.dataset?.currentDesk;
    if (selectedDeskId) {
      fetch(`/api/user-status/${encodeURIComponent(selectedDeskId)}/`)
        .then(r => r.json())
        .then(data => {
          if (pairBtn) pairBtn.disabled = !!data.is_paired;
          if (unpairBtn) unpairBtn.disabled = !data.is_paired;
        })
        .catch(() => {});
    }
  } catch (err) {
    console.error("Auto-refresh error:", err);
  }
}

// start auto-refresh loop (3s recommended; adjust as needed)
setInterval(autoRefreshDesks, 3000);

// run once on load to make sure UI state is normalized
document.addEventListener("DOMContentLoaded", () => {
  ensureElementListeners();
  // mark active view if none
  if (!document.querySelector(".view-btn.active")) {
    const btn = document.querySelector('.view-btn[data-view="desks"]');
    if (btn) btn.classList.add("active");
  }
  // initial pairing status checks won't run until user selects a desk
});

function refreshDeskStatus() {
  fetch("/api/desks_status/")
    .then(r => r.json())
    .then(data => {
      document.querySelectorAll(".btn[data-desk-id]").forEach(btn => {
        const deskId = btn.dataset.deskId;
        if (!deskId) return;
        if (data[deskId]) {
          btn.classList.add("occupied");
          btn.title = `Occupied by ${data[deskId].user}`;
        } else {
          btn.classList.remove("occupied");
          btn.title = "";
        }
      });
    });
}

// Run on load and every 3s
document.addEventListener("DOMContentLoaded", refreshDeskStatus);
setInterval(refreshDeskStatus, 3000);

function updateDeskButtons(desksApi) {
    document.querySelectorAll(".desk-btn").forEach(btn => {
        const deskId = btn.dataset.deskId;
        const desk = desksApi[deskId];
        if (!desk) return;

        // Determine state
        if (desk.desk_data.state.status !== "Normal" || desk.desk_data.state.isAntiCollision) {
            btn.classList.add("broken");
            btn.classList.remove("occupied", "normal");
            btn.disabled = true;
        } else if (desk.user) {
            btn.classList.add("occupied");
            btn.classList.remove("broken", "normal");
            btn.disabled = false;
        } else {
            btn.classList.add("normal");
            btn.classList.remove("broken", "occupied");
            btn.disabled = false;
        }
    });
}
