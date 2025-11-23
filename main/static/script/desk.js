// === Height Slider & Ergonomic Health Recommendations ===
const slider = document.getElementById("heightSlider");
const valueLabel = document.getElementById("heightValue");
const popup = document.getElementById("healthPopup");
const message = document.getElementById("healthMessage");
const acceptBtn = document.getElementById("acceptBtn");
const ignoreBtn = document.getElementById("ignoreBtn");
const toggleHealth = document.getElementById("toggleHealth");

// === Ergonomic Formulas ===
function getSittingHeight(h) { return h / 2.48; }
function getStandingHeight(h) { return h / 1.58; }

const sittingHeight = Math.round(getSittingHeight(USER_HEIGHT_CM));
const standingHeight = Math.round(getStandingHeight(USER_HEIGHT_CM));
const MARGIN = 4;

let currentRecommendation = null;
let sittingTimer = null;
let sittingTimeSeconds = 0;
const SITTING_ALERT_DELAY = 10;

// === Sitting Timer ===
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

// === Popup Helpers ===
function setPopupButtons(left, right) {
  acceptBtn.textContent = left || "Accept";
  ignoreBtn.textContent = right || "Ignore";
  acceptBtn.style.display = left ? "inline-block" : "none";
  ignoreBtn.style.display = right ? "inline-block" : "none";
}

function showPopup() { popup.classList.add("show"); }
function hidePopup() {
  popup.classList.remove("show", "low", "high", "correct", "standing", "sitting");
  currentRecommendation = null;
  setPopupButtons("Accept", "Ignore");
}

function showSittingReminder() {
  const hoursSat = 4.2;
  message.textContent = `🪑 Consider standing more: You've been sitting for ${hoursSat.toFixed(1)} hours today.`;
  setPopupButtons("Stand up", "Cancel");
  popup.classList.add("sitting");
  currentRecommendation = "sittingReminder";
  showPopup();
}

// === Slider Logic ===
slider.addEventListener("input", () => {
  const height = parseInt(slider.value);
  valueLabel.textContent = height;

  const hasActiveDesk = Object.values(window.desks || {}).some(
    d => d.status === "booked" || d.status === "paired"
  );

  if (!hasActiveDesk || !toggleHealth.checked) {
    hidePopup();
    resetSittingTimer();
    return;
  }

  popup.classList.remove("low", "high", "correct", "standing", "sitting");

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

// === Popup Buttons ===
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
    const h = btn.dataset.height;
    slider.value = h;
    valueLabel.textContent = h;
  });
});

// === Global Status Messages ===
function setStatusMessage(msg, type = "info") {
  const box = document.getElementById("statusMessage");
  if (!box) return;
  box.textContent = msg;
  box.className = "status-message " + type;
  box.style.display = "block";
  clearTimeout(setStatusMessage._t);
  setStatusMessage._t = setTimeout(() => {
    box.style.display = "none";
  }, 4000);
}

// =====================================================================
// === DESK SELECTION / PAIRING / BOOKING (Backend integrated) =========
// =====================================================================

const pairBtn = document.getElementById("pairBtn");
const unpairBtn = document.getElementById("unpairBtn");
const showBooking = document.getElementById("showBooking");
const bookingForm = document.getElementById("bookingForm");
const bookBtn = document.getElementById("bookBtn");
const cancelBooking = document.getElementById("cancelBooking");
const bookStart = document.getElementById("bookStart");
const bookEnd = document.getElementById("bookEnd");
const reservationActions = document.getElementById("reservationActions");

window.desks = window.desks || {};

document.getElementById("main-content").addEventListener("click", e => {
  const btn = e.target.closest(".btn");
  if (!btn) return;

  const deskId = btn.dataset.deskId;
  if(!deskId) return;

  const selectedDesk = document.getElementById("selectedDesk");
  selectedDesk.textContent = `Selected Desk: ${deskId}`;
  reservationActions.style.display = "block";
  reservationActions.dataset.currentDesk = deskId;

  // Check if desk is paired for this user
  fetch(`/api/user-status/${deskId}/`)
    .then(res => res.json())
    .then(data => {
      pairBtn.disabled = data.is_paired;
      unpairBtn.disabled = !data.is_paired;
    });
});

// === Pair Desk ===
pairBtn.addEventListener("click", e => {
  e.preventDefault();
  const deskId = reservationActions.dataset.currentDesk;

  const formData = new FormData();
  formData.append("desk_id", deskId);

  fetch("/pair_desk/", {
    method: "POST",
    headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value },
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      setStatusMessage(data.message, data.success ? "success" : "error");
      if (data.success) {
        pairBtn.disabled = true;
        unpairBtn.disabled = false;
      }
    });
});

// === Unpair Desk ===
unpairBtn.addEventListener("click", e => {
  e.preventDefault();

  fetch("/unpair_desk/", {
    method: "POST",
    headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
  })
    .then(res => res.json())
    .then(data => {
      setStatusMessage(data.message, data.success ? "success" : "error");
      if (data.success) {
        pairBtn.disabled = false;
        unpairBtn.disabled = true;
      }
    });
});

// === Show / Cancel Booking ===
showBooking?.addEventListener("click", () => bookingForm.style.display = "block");
cancelBooking?.addEventListener("click", () => {
  bookingForm.style.display = "none";
  bookStart.value = "";
  bookEnd.value = "";
});

// === Book Desk ===
bookBtn?.addEventListener("click", () => {
  const deskId = reservationActions.dataset.currentDesk;
  if (!deskId) return setStatusMessage("Select a desk first.", "error");
  if (!bookStart.value || !bookEnd.value) return setStatusMessage("Please select start and end time.", "error");

  window.desks[deskId] = { status: "booked", start: bookStart.value, end: bookEnd.value };
  bookingForm.style.display = "none";
  setStatusMessage(`Desk ${deskId} booked from ${bookStart.value} to ${bookEnd.value}`);
  pairBtn.disabled = true;
  unpairBtn.disabled = false;

  bookStart.value = "";
  bookEnd.value = "";
});

// === VIEW SWITCHING (dynamic UI) ===
document.querySelectorAll(".view-btn").forEach(button => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;

    fetch(`/load_view/${view}/`)
      .then(res => res.text())
      .then(html => {
        document.getElementById("main-content").innerHTML = html;
        if (view === "overview") document.dispatchEvent(new Event("overviewLoaded"));
      })
      .catch(err => console.error("❌ Failed to load view:", err));
  });
});
