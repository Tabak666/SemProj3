// desk.js — unified, robust, auto-refreshing script

// --------------------------- Utilities ---------------------------
function safeGet(id) { return document.getElementById(id); }

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
const deskControls = safeGet("desk-controls");

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

function ensureElementListeners() {
  if (!slider || !valueLabel || !popup || !acceptBtn || !ignoreBtn || !toggleHealth) return;
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

// --- Backend Height Update Helper ---
function updateBackendHeight(deskId, heightVal) {
    const formData = new FormData();
    formData.append("desk_id", deskId);
    formData.append("height", heightVal);

    fetch("/api/set_desk_height/", {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            setStatusMessage(data.message, "error");
        }
    })
    .catch(err => console.error("Height update failed", err));
}

// --- Slider logic ---
if (slider && valueLabel && toggleHealth) {
  let debounceTimer;

  slider.addEventListener("input", () => {
    const height = parseInt(slider.value);
    valueLabel.textContent = height;

    const hasActiveDesk = Object.values(window.desks || {}).some(d => d.status === "booked" || d.status === "paired");
    const deskId = reservationActions?.dataset?.currentDesk;
    
    if (deskId && deskControls && deskControls.style.display !== "none") {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            updateBackendHeight(deskId, height);
        }, 300);
    }

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
  slider.dispatchEvent(new Event('input'));
  hidePopup();
});
ignoreBtn && ignoreBtn.addEventListener("click", () => {
  if (currentRecommendation === "standingChoice") {
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
    slider.dispatchEvent(new Event('input'));
  }
  hidePopup();
});

// --------------------------- Profiles / Config / Status ---------------------------
document.querySelectorAll(".profile-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const h = btn.dataset.height;
    const deskId = reservationActions?.dataset?.currentDesk;

    if (slider && valueLabel) {
      slider.value = h;
      valueLabel.textContent = h;
      slider.dispatchEvent(new Event('input'));
    } else {
        if (deskId && deskControls && deskControls.style.display !== "none") {
            updateBackendHeight(deskId, h);
        }
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

window.desks = window.desks || {};

function activateDeskPanel(deskId) {
  // Visual highlight: Remove from all, add to current
  document.querySelectorAll('.grid-container .btn').forEach(b => b.classList.remove('selected'));
  const activeBtn = document.querySelector(`.grid-container .btn[data-desk-id="${deskId}"]`);
  if (activeBtn) {
      activeBtn.classList.add('selected');
  }

  const selectedDesk = safeGet("selectedDesk");
  if (selectedDesk) selectedDesk.textContent = `Selected Desk: ${deskId}`;

  if (reservationActions) {
      reservationActions.style.display = "block";
      reservationActions.dataset.currentDesk = deskId;
  }

  if (deskControls) deskControls.style.display = "none";

  fetch(`/api/user-status/${encodeURIComponent(deskId)}/`)
    .then(res => res.json())
    .then(data => {
      const isPaired = !!data.is_paired;
      if (pairBtn) pairBtn.disabled = isPaired;
      if (unpairBtn) unpairBtn.disabled = !isPaired;

      if (deskControls) {
          deskControls.style.display = isPaired ? "block" : "none";
      }
      
      if (isPaired) {
          window.desks = window.desks || {};
          window.desks[deskId] = { status: "paired", start: new Date().toLocaleString() };
      }
    })
    .catch(err => {
      console.warn("user-status check failed", err);
    });
}

document.getElementById("main-content")?.addEventListener("click", (e) => {
  const btn = e.target.closest(".btn");
  if (!btn) return;

  const deskId = btn.dataset.deskId;
  if (!deskId) return;

  activateDeskPanel(deskId);
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
      if (deskControls) deskControls.style.display = "block";
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
      if (deskControls) deskControls.style.display = "none";
      if (window.desks && window.desks[deskId]) delete window.desks[deskId];
    }
  })
  .catch(err => setStatusMessage("Unpair request failed.", "error"));
});

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
function initViewButtons() {
  document.querySelectorAll(".view-btn").forEach(button => {
    const clone = button.cloneNode(true);
    button.parentNode.replaceChild(clone, button);
  });

  document.querySelectorAll(".view-btn").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
      button.classList.add("active");

      const view = button.dataset.view;
      let url = `/load_view/${view}/`;

      if (view === 'desks') {
          const storedRoom = sessionStorage.getItem("lastDeskRoom");
          if (storedRoom) {
              url += `?room=Room%20${encodeURIComponent(storedRoom)}`;
          }
      }

      fetch(url)
        .then(res => res.text())
        .then(html => {
          const main = document.getElementById("main-content");
          if (!main) return;
          main.innerHTML = html;
          document.dispatchEvent(new Event("viewChanged"));
          document.dispatchEvent(new Event("overviewLoaded"));
        })
        .catch(err => console.error("Failed to load view:", err));
    });
  });
}
initViewButtons();

document.addEventListener("DOMContentLoaded", () => {
  ensureElementListeners();
  
  if (!document.querySelector(".view-btn.active")) {
    const btn = document.querySelector('.view-btn[data-view="desks"]');
    if (btn) btn.classList.add("active");
  }

  if (typeof INITIAL_DESK_ID !== 'undefined' && INITIAL_DESK_ID) {
      activateDeskPanel(INITIAL_DESK_ID);
  }
});

function syncStateWithContent() {
    const roomWrapper = document.querySelector(".room-wrapper");
    if (roomWrapper) {
        const desksBtn = document.querySelector('.view-btn[data-view="desks"]');
        if (desksBtn && !desksBtn.classList.contains("active")) {
            document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
            desksBtn.classList.add("active");
        }
        const roomId = roomWrapper.id.replace(/^room-/, "");
        if (roomId) {
            sessionStorage.setItem("lastDeskRoom", roomId);
        }
    }
}
setInterval(syncStateWithContent, 1000);

// --------------------------- Auto-refresh logic ---------------------------
async function autoRefreshDesks() {
  const activeViewBtn = document.querySelector(".view-btn.active");
  const activeView = activeViewBtn ? activeViewBtn.dataset.view : null;
  if (activeView !== "desks") return;

  const currentRoomWrapper = document.querySelector(".room-wrapper");
  const roomId = currentRoomWrapper ? currentRoomWrapper.id.replace(/^room-/, "") : null;

  let url = "/load_view/desks/";
  if (roomId) url += `?room=Room%20${encodeURIComponent(roomId)}`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    const html = await res.text();
    const main = document.getElementById("main-content");
    if (!main) return;

    if (main.innerHTML.trim() === html.trim()) {
      return;
    }

    main.innerHTML = html;
    initViewButtons();
    document.dispatchEvent(new Event("overviewLoaded"));

    // ✅ FIX: Re-apply selection visual state after HTML replacement
    const selectedDeskId = reservationActions?.dataset?.currentDesk;
    if (selectedDeskId) {
        const activeBtn = document.querySelector(`.grid-container .btn[data-desk-id="${selectedDeskId}"]`);
        if (activeBtn) {
            activeBtn.classList.add('selected');
        }

      fetch(`/api/user-status/${encodeURIComponent(selectedDeskId)}/`)
        .then(r => r.json())
        .then(data => {
          if (pairBtn) pairBtn.disabled = !!data.is_paired;
          if (unpairBtn) unpairBtn.disabled = !data.is_paired;
          if (deskControls) {
              deskControls.style.display = data.is_paired ? "block" : "none";
          }
        })
        .catch(() => {});
    }
  } catch (err) {
    console.error("Auto-refresh error:", err);
  }
}

setInterval(autoRefreshDesks, 3000);

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

document.addEventListener("DOMContentLoaded", refreshDeskStatus);
setInterval(refreshDeskStatus, 3000);