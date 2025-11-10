// === Height Slider & Ergonomic Health Recommendations ===
const slider = document.getElementById("heightSlider");
const valueLabel = document.getElementById("heightValue");
const popup = document.getElementById("healthPopup");
const message = document.getElementById("healthMessage");
const acceptBtn = document.getElementById("acceptBtn");
const ignoreBtn = document.getElementById("ignoreBtn");
const toggleHealth = document.getElementById("toggleHealth");

const USER_HEIGHT_CM = 176;

// --- Ergonomic height formulas ---
function getSittingHeight(heightCm) {
  return heightCm / 2.48;
}
function getStandingHeight(heightCm) {
  return heightCm / 1.58;
}

const sittingHeight = Math.round(getSittingHeight(USER_HEIGHT_CM));
const standingHeight = Math.round(getStandingHeight(USER_HEIGHT_CM));
const MARGIN = 4;

let currentRecommendation = null;
let sittingTimer = null;
let sittingTimeSeconds = 0;
const SITTING_ALERT_DELAY = 10; // seconds (demo)
const STANDING_TARGET_PERCENT = 40;

// --- Sitting Timer Control ---
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

// --- Health Popup Helpers ---
function setPopupButtons(leftText, rightText) {
  acceptBtn.textContent = leftText || "Accept";
  ignoreBtn.textContent = rightText || "Ignore";
  acceptBtn.style.display = leftText ? "inline-block" : "none";
  ignoreBtn.style.display = rightText ? "inline-block" : "none";
}

function showPopup() {
  popup.classList.add("show");
}

function hidePopup() {
  popup.classList.remove("show", "low", "high", "correct", "standing", "sitting");
  currentRecommendation = null;
  setPopupButtons("Accept", "Ignore");
}

function showSittingReminder() {
  const hoursSat = 4.2;
  message.textContent = `🪑 Consider standing more: You've been sitting for ${hoursSat.toFixed(
    1
  )} hours today. Try to increase standing time to ${STANDING_TARGET_PERCENT}%.`;
  setPopupButtons("Stand up", "Cancel");
  popup.classList.remove("low", "high", "correct", "standing");
  popup.classList.add("sitting");
  currentRecommendation = "sittingReminder";
  showPopup();
}

// --- Slider Logic ---
slider.addEventListener("input", () => {
  const height = parseInt(slider.value);
  valueLabel.textContent = height;

  // ✅ Check if any desk is booked or paired
  const hasActiveDesk = Object.values(window.desks || {}).some(
    d => d.status === "booked" || d.status === "paired"
  );

  // 🔇 If no desks are active → disable popup logic entirely
  if (!hasActiveDesk) {
    hidePopup();
    resetSittingTimer();
    return;
  }

  if (!toggleHealth.checked) {
    hidePopup();
    resetSittingTimer();
    return;
  }

  popup.classList.remove("low", "high", "correct", "standing", "sitting");

  if (height < sittingHeight - MARGIN) {
    message.textContent = `⚠️ Desk too low for your height (${USER_HEIGHT_CM} cm). Recommended sitting height: ${
      sittingHeight - MARGIN
    } - ${sittingHeight + MARGIN} cm.`;
    popup.classList.add("low");
    currentRecommendation = "low";
    setPopupButtons("Adjust", "Ignore");
    showPopup();
    resetSittingTimer();

  } else if (height <= sittingHeight + MARGIN) {
    message.textContent = "✅ Desk height looks good for sitting posture!";
    popup.classList.add("correct");
    currentRecommendation = "correct";
    setPopupButtons("OK", "");
    showPopup();
    startSittingTimer();

  } else if (height <= standingHeight + MARGIN) {
    message.textContent = "⁉️ Desk height is close to standing range. Choose your position:";
    popup.classList.add("standing");
    currentRecommendation = "standingChoice";
    setPopupButtons("Sitting", "Standing");
    showPopup();
    resetSittingTimer();

  } else {
    message.textContent = `⚠️ Desk too high even for standing. Recommended standing height: ${
      standingHeight - MARGIN
    } - ${standingHeight + MARGIN} cm.`;
    popup.classList.add("high");
    currentRecommendation = "high";
    setPopupButtons("Adjust", "Ignore");
    showPopup();
    resetSittingTimer();
  }
});


// --- Popup Buttons Logic ---
acceptBtn.addEventListener("click", () => {
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

ignoreBtn.addEventListener("click", () => {
  if (currentRecommendation === "standingChoice") {
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
  }
  hidePopup();
});

// === Quick Profiles ===
document.querySelectorAll(".profile-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const h = btn.getAttribute("data-height");
    slider.value = h;
    valueLabel.textContent = h;
  });
});

// === Load Configuration ===
document.getElementById("loadConfig").addEventListener("click", () => {
  const config = document.getElementById("configSelect").value;
  if (config) setStatusMessage(`Loaded configuration: ${config}`);
});

// === Global Status Message Helper ===
function setStatusMessage(msg, type = "info") {
  const statusMessage = document.getElementById("statusMessage");
  if (!statusMessage) return;
  statusMessage.textContent = msg;
  statusMessage.className = "status-message " + type;
  statusMessage.style.display = "block";
  clearTimeout(setStatusMessage._t);
  setStatusMessage._t = setTimeout(() => {
    statusMessage.style.display = "none";
  }, 4000);
}

// =====================================================================
// === Desk Reservation Logic (event delegation, always active) ========
// =====================================================================

// Use a persistent global object for desk states
window.desks = window.desks || {};

// --- Handle clicks on dynamically loaded desk buttons ---
document.getElementById("main-content").addEventListener("click", (e) => {
  const btn = e.target.closest(".btn");
  if (!btn) return;

  const deskId = btn.textContent.trim();
  const selectedDeskLabel = document.getElementById("selectedDesk");
  const reservationActions = document.getElementById("reservationActions");
  const bookingForm = document.getElementById("bookingForm");
  const pairBtn = document.getElementById("pairBtn");
  const unpairBtn = document.getElementById("unpairBtn");

  selectedDeskLabel.textContent = `Selected Desk: ${deskId}`;
  reservationActions.style.display = "block";
  bookingForm.style.display = "none";
  reservationActions.dataset.currentDesk = deskId;

  const d = window.desks[deskId];
  if (d && d.status === "paired") {
    pairBtn.disabled = true;
    unpairBtn.disabled = false;
  } else {
    pairBtn.disabled = false;
    unpairBtn.disabled = true;
  }
});

// --- Side panel reservation buttons ---
const pairBtn = document.getElementById("pairBtn");
const unpairBtn = document.getElementById("unpairBtn");
const showBooking = document.getElementById("showBooking");
const bookingForm = document.getElementById("bookingForm");
const bookBtn = document.getElementById("bookBtn");
const cancelBooking = document.getElementById("cancelBooking");
const bookStart = document.getElementById("bookStart");
const bookEnd = document.getElementById("bookEnd");
const reservationActions = document.getElementById("reservationActions");

if (pairBtn) {
  pairBtn.addEventListener("click", () => {
    const deskId = reservationActions.dataset.currentDesk;
    if (!deskId) return;
    window.desks[deskId] = { status: "paired", start: new Date().toLocaleString() };
    pairBtn.disabled = true;
    unpairBtn.disabled = false;
    setStatusMessage(`Desk ${deskId} paired.`);
  });
}

if (unpairBtn) {
  unpairBtn.addEventListener("click", () => {
    const deskId = reservationActions.dataset.currentDesk;
    if (deskId && window.desks[deskId]) {
      delete window.desks[deskId];
      setStatusMessage(`Desk ${deskId} unpaired.`);
    }
    pairBtn.disabled = false;
    unpairBtn.disabled = true;
  });
}

if (showBooking) {
  showBooking.addEventListener("click", () => {
    bookingForm.style.display = "block";
  });
}

if (cancelBooking) {
  cancelBooking.addEventListener("click", () => {
    bookingForm.style.display = "none";
    bookStart.value = "";
    bookEnd.value = "";
  });
}

if (bookBtn) {
  bookBtn.addEventListener("click", () => {
    const deskId = reservationActions.dataset.currentDesk;
    const start = bookStart.value;
    const end = bookEnd.value;

    if (!deskId) {
      setStatusMessage("Select a desk first.", "error");
      return;
    }
    if (!start || !end) {
      setStatusMessage("Please select both start and end date/time.", "error");
      return;
    }

    window.desks[deskId] = { status: "booked", start, end };
    setStatusMessage(`Desk ${deskId} booked from ${start} to ${end}`);
    bookingForm.style.display = "none";
    bookStart.value = "";
    bookEnd.value = "";
    pairBtn.disabled = true;
    unpairBtn.disabled = false;
  });
}

// =====================================================================
// === Side Panel View Buttons (Dynamic Switching) =====================
// =====================================================================
document.querySelectorAll(".view-btn").forEach(button => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;

    fetch(`/load_view/${view}/`)
      .then(response => response.text())
      .then(html => {
        const mainContent = document.getElementById("main-content");
        mainContent.innerHTML = html;

        if (view === "overview") {
          document.dispatchEvent(new Event("overviewLoaded"));
        }

        // No reinit needed, event delegation handles new desks automatically
      })
      .catch(err => console.error("❌ Failed to load view:", err));
  });
});
