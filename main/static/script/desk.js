// === Height Slider with Simplified Ergonomic Health Recommendations ===
const slider = document.getElementById('heightSlider');
const valueLabel = document.getElementById('heightValue');
const popup = document.getElementById('healthPopup');
const message = document.getElementById('healthMessage');
const acceptBtn = document.getElementById('acceptBtn');
const ignoreBtn = document.getElementById('ignoreBtn');
const toggleHealth = document.getElementById('toggleHealth');

// Hardcoded user height (in cm)
const USER_HEIGHT_CM = 176;

// Simplified ergonomic formulas
function getSittingHeight(heightCm) {
  return heightCm / 2.48;
}
function getStandingHeight(heightCm) {
  return heightCm / 1.58;
}

const sittingHeight = Math.round(getSittingHeight(USER_HEIGHT_CM)); // ≈ 71 cm
const standingHeight = Math.round(getStandingHeight(USER_HEIGHT_CM)); // ≈ 111 cm
const MARGIN = 4;

let highMarginSitting = sittingHeight + MARGIN;
let lowMarginSitting = sittingHeight - MARGIN;
let highMarginStanding = standingHeight + MARGIN;
let lowMarginStanding = standingHeight - MARGIN;

let currentRecommendation = null;
let sittingTimer = null;
let sittingTimeSeconds = 0;
const SITTING_ALERT_DELAY = 10; // seconds for demo
const STANDING_TARGET_PERCENT = 40;

// --- Slider Logic ---
slider.addEventListener('input', () => {
  const height = parseInt(slider.value);
  valueLabel.textContent = height;

  if (!toggleHealth.checked) {
    hidePopup();
    clearInterval(sittingTimer);
    sittingTimer = null;
    sittingTimeSeconds = 0;
    return;
  }

  popup.classList.remove("low", "high", "correct", "standing", "sitting");

  if (height < sittingHeight - MARGIN) {
    message.textContent = `⚠️ Desk is too low for your height (${USER_HEIGHT_CM} cm). Recommended sitting height: ${lowMarginSitting} - ${highMarginSitting} cm.`;
    setPopupButtons("Adjust", "Ignore");
    popup.classList.add("low");
    currentRecommendation = "low";
    showPopup();
    resetSittingTimer();

  } else if (height <= sittingHeight + MARGIN) {
    message.textContent = "✅ Desk height looks good for sitting posture!";
    setPopupButtons("OK", "");
    popup.classList.add("correct");
    currentRecommendation = "correct";
    showPopup();
    startSittingTimer();

  } else if (height <= standingHeight + MARGIN) {
    message.textContent = `⁉️ Desk height is closer to standing range. Choose your preferred position:`;
    setPopupButtons("Sitting", "Standing");
    popup.classList.add("standing");
    currentRecommendation = "standingChoice";
    showPopup();
    resetSittingTimer();

  } else {
    message.textContent = `⚠️ Desk is too high even for standing. Recommended standing height: ${lowMarginStanding} - ${highMarginStanding} cm.`;
    setPopupButtons("Adjust", "Ignore");
    popup.classList.add("high");
    currentRecommendation = "high";
    showPopup();
    resetSittingTimer();
  }
});

// --- Helper for popup buttons ---
function setPopupButtons(leftText, rightText) {
  acceptBtn.textContent = leftText || "Accept";
  ignoreBtn.textContent = rightText || "Ignore";

  // Hide button if text empty
  acceptBtn.style.display = leftText ? "inline-block" : "none";
  ignoreBtn.style.display = rightText ? "inline-block" : "none";
}

// --- Sitting Timer ---
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

function showSittingReminder() {
  const hoursSat = 4.2; // placeholder until API integration
  message.textContent = `🪑 Consider standing more: You've been sitting for ${hoursSat.toFixed(1)} hours today. Try to increase standing time to ${STANDING_TARGET_PERCENT}%.`;
  setPopupButtons("Stand up", "Cancel");

  popup.classList.remove("low", "high", "correct", "standing");
  popup.classList.add("sitting");

  currentRecommendation = "sittingReminder";
  showPopup();
}

// --- Popup control ---
function showPopup() {
  popup.classList.add("show");
}

function hidePopup() {
  popup.classList.remove("show", "low", "high", "correct", "standing", "sitting");
  currentRecommendation = null;
  setPopupButtons("Accept", "Ignore");
}

// --- Popup Buttons ---
acceptBtn.addEventListener('click', () => {
  if (currentRecommendation === "low") {
    slider.value = sittingHeight;
    valueLabel.textContent = sittingHeight;
  } else if (currentRecommendation === "high" || currentRecommendation === "sittingReminder") {
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
  } else if (currentRecommendation === "standingChoice") {
    // "Sitting" button pressed
    slider.value = sittingHeight;
    valueLabel.textContent = sittingHeight;
  }
  hidePopup();
});

ignoreBtn.addEventListener('click', () => {
  if (currentRecommendation === "standingChoice") {
    // "Standing" button pressed
    slider.value = standingHeight;
    valueLabel.textContent = standingHeight;
  }
  hidePopup();
});



// ------------------------------------------------------------------------

  // === Quick Profiles ===
  document.querySelectorAll('.profile-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const h = btn.getAttribute('data-height');
      slider.value = h;
      valueLabel.textContent = h;
    });
  });

  // === Load Configuration ===
  document.getElementById('loadConfig').addEventListener('click', () => {
    const config = document.getElementById('configSelect').value;
    if (config) setStatusMessage(`Loaded configuration: ${config}`);
  });

  // === Desk Reservation Logic (unchanged) ===
  const deskButtons = document.querySelectorAll('.btn');
  const selectedDeskLabel = document.getElementById('selectedDesk');
  const reservationActions = document.getElementById('reservationActions');
  const pairBtn = document.getElementById('pairBtn');
  const unpairBtn = document.getElementById('unpairBtn');
  const showBooking = document.getElementById('showBooking');
  const bookingForm = document.getElementById('bookingForm');
  const bookBtn = document.getElementById('bookBtn');
  const cancelBooking = document.getElementById('cancelBooking');
  const bookStart = document.getElementById('bookStart');
  const bookEnd = document.getElementById('bookEnd');

  const desks = {};
  const statusMessage = document.getElementById('statusMessage');
  function setStatusMessage(msg, type = 'info') {
    if (!statusMessage) return;
    statusMessage.textContent = msg;
    statusMessage.className = 'status-message ' + type;
    statusMessage.style.display = 'block';
    clearTimeout(setStatusMessage._t);
    setStatusMessage._t = setTimeout(() => {
      statusMessage.style.display = 'none';
    }, 4000);
  }

  deskButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const deskId = btn.textContent.trim();
      selectedDeskLabel.textContent = `Selected Desk: ${deskId}`;
      reservationActions.style.display = 'block';
      bookingForm.style.display = 'none';
      reservationActions.dataset.currentDesk = deskId;

      const d = desks[deskId];
      if (d && d.status === 'paired') {
        pairBtn.disabled = true;
        unpairBtn.disabled = false;
      } else {
        pairBtn.disabled = false;
        unpairBtn.disabled = true;
      }
    });
  });

  pairBtn.addEventListener('click', () => {
    const deskId = reservationActions.dataset.currentDesk;
    desks[deskId] = { status: 'paired', start: new Date().toLocaleString() };
    pairBtn.disabled = true;
    unpairBtn.disabled = false;
  });

  unpairBtn.addEventListener('click', () => {
    const deskId = reservationActions.dataset.currentDesk;
    if (desks[deskId]) {
      delete desks[deskId];
      setStatusMessage(`Desk ${deskId} unpaired.`);
    }
    pairBtn.disabled = false;
    unpairBtn.disabled = true;
  });

  showBooking.addEventListener('click', () => {
    bookingForm.style.display = 'block';
  });

  cancelBooking.addEventListener('click', () => {
    bookingForm.style.display = 'none';
    bookStart.value = '';
    bookEnd.value = '';
  });

  bookBtn.addEventListener('click', () => {
    const deskId = reservationActions.dataset.currentDesk;
    const start = bookStart.value;
    const end = bookEnd.value;

    if (!start || !end) {
      setStatusMessage('Please select both start and end date/time.', 'error');
      return;
    }

    desks[deskId] = { status: 'booked', start, end };
    setStatusMessage(`Desk ${deskId} booked from ${start} to ${end}`);
    bookingForm.style.display = 'none';
    bookStart.value = '';
    bookEnd.value = '';
    pairBtn.disabled = true;
    unpairBtn.disabled = false;
  });
