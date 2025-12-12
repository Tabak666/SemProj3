// --------------------------- Utilities ---------------------------
function safeGet(id) { return document.getElementById(id); }

function getCookie(name) {
  const v = document.cookie.split('; ').find(row => row.startsWith(name + '='));
  return v ? decodeURIComponent(v.split('=')[1]) : null;
}
const CSRF_TOKEN = getCookie('csrftoken');

// --------------------------- Height / Popup / Loading ---------------------------
const slider = safeGet("heightSlider");
const valueLabel = safeGet("heightValue");
const popup = safeGet("healthPopup");
const message = safeGet("healthMessage");
const acceptBtn = safeGet("acceptBtn");
const ignoreBtn = safeGet("ignoreBtn");
const toggleHealth = safeGet("toggleHealth");
const deskControls = safeGet("desk-controls");

// New Elements for Confirmation & Loading
const confirmModalEl = safeGet("moveConfirmModal");
const confirmHeightVal = safeGet("confirmHeightVal");
const confirmMoveBtn = safeGet("confirmMoveBtn");
const loadingOverlay = safeGet("deskLoadingOverlay");
const bugModal = document.getElementById('bugReportModal');
const reportBtn = document.getElementById('reportBugBtn');
const closeBugBtn = document.getElementById('closeBugModal');
const bugForm = document.getElementById('bugReportForm');

let pendingMoveHeight = null;
let confirmModal = null;

if (confirmModalEl && typeof bootstrap !== 'undefined') {
    confirmModal = new bootstrap.Modal(confirmModalEl);
}

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

// --- MOVEMENT MONITORING LOGIC ---
function monitorDeskMovement(deskId, targetHeight) {
    let attempts = 0;
    const maxAttempts = 60; // Max 60 seconds timeout

    // Update overlay text to show we are waiting
    if (loadingOverlay) {
        const text = loadingOverlay.querySelector('p');
        if (text) text.textContent = "Moving desk... please wait";
    }

    const poll = setInterval(() => {
        attempts++;
        fetch(`/api/user-status/${encodeURIComponent(deskId)}/`)
        .then(r => r.json())
        .then(data => {
            const currentH = data.current_height;
            const isMoving = data.is_moving;

            // Success Condition 1: Reached target height (exact or +/- 1cm)
            if (currentH !== null && Math.abs(currentH - targetHeight) <= 1) {
                stopLoading(`Desk reached ${targetHeight}cm`, "success", targetHeight);
            } 
            // Stop Condition 2: Desk stopped moving (and it wasn't just starting)
            // We wait > 2 attempts to ensure the simulator had time to start the motor
            else if (isMoving === false && attempts > 2) { 
                stopLoading(`Desk stopped at ${currentH}cm`, "warning", currentH);
            }
            
            // Timeout
            if (attempts >= maxAttempts) {
                stopLoading("Movement timed out", "error", currentH);
            }
        })
        .catch(err => console.error("Polling error", err));
    }, 1000);

    function stopLoading(msg, type, finalHeight) {
        clearInterval(poll);
        if (loadingOverlay) loadingOverlay.classList.remove("active");
        setStatusMessage(msg, type);
        
        // Sync slider to where it actually ended up
        if (finalHeight && slider && valueLabel) {
            slider.value = finalHeight;
            valueLabel.textContent = finalHeight;
        }
    }
}

// 1. Request Movement (Triggers Modal)
function requestDeskMovement(height) {
    if (!confirmModal) {
        if(confirm(`Are you sure you want to move the desk to ${height}cm?`)) {
            executeDeskMovement(height);
        }
        return;
    }
    
    pendingMoveHeight = height;
    if (confirmHeightVal) confirmHeightVal.textContent = height;
    confirmModal.show();
}

// 2. Execute Movement (Triggers API + Loading + Monitoring)
function executeDeskMovement(height) {
    const deskId = reservationActions?.dataset?.currentDesk;
    if (!deskId) return;

    if (loadingOverlay) {
        loadingOverlay.classList.add("active");
        const text = loadingOverlay.querySelector('p');
        if(text) text.textContent = "Sending command...";
    }

    const formData = new FormData();
    formData.append("desk_id", deskId);
    formData.append("height", height);

    fetch("/api/set_desk_height/", {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            if (loadingOverlay) loadingOverlay.classList.remove("active");
            setStatusMessage(data.message, "error");
        } else {
            // ✅ SUCCESS: Now wait for it to actually move
            monitorDeskMovement(deskId, height);
        }
    })
    .catch(err => {
        console.error("Height update failed", err);
        if (loadingOverlay) loadingOverlay.classList.remove("active");
        setStatusMessage("Connection failed", "error");
    });
}

// 3. Confirm Button Listener
if (confirmMoveBtn) {
    confirmMoveBtn.addEventListener("click", () => {
        if (pendingMoveHeight !== null) {
            executeDeskMovement(pendingMoveHeight);
            confirmModal.hide();
        }
    });
}


// --- Slider logic ---
if (slider && valueLabel && toggleHealth) {
  
  slider.addEventListener("input", () => {
      valueLabel.textContent = slider.value;
  });

  slider.addEventListener("change", () => {
    const height = parseInt(slider.value);
    
    const hasActiveDesk = Object.values(window.desks || {}).some(d => d.status === "booked" || d.status === "paired");
    const deskId = reservationActions?.dataset?.currentDesk;
    
    if (deskId && deskControls && deskControls.style.display !== "none") {
        requestDeskMovement(height);
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

acceptBtn && acceptBtn.addEventListener("click", () => {
  let targetH = slider.value;
  if (currentRecommendation === "low") {
    targetH = sittingHeight;
  } else if (currentRecommendation === "high" || currentRecommendation === "sittingReminder") {
    targetH = standingHeight;
  } else if (currentRecommendation === "standingChoice") {
    targetH = sittingHeight;
  }
  hidePopup();
  requestDeskMovement(targetH);
});

ignoreBtn && ignoreBtn.addEventListener("click", () => {
  if (currentRecommendation === "standingChoice") {
    hidePopup();
    requestDeskMovement(standingHeight);
  } else {
    hidePopup();
  }
});

// --------------------------- Profiles / Config / Status ---------------------------
document.querySelectorAll(".profile-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const h = btn.dataset.height;
    const deskId = reservationActions?.dataset?.currentDesk;

    if (deskId && deskControls && deskControls.style.display !== "none") {
        requestDeskMovement(h);
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
          
          if (isPaired && data.current_height && slider && valueLabel) {
              slider.value = data.current_height;
              valueLabel.textContent = data.current_height;
          }
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

      // --- NEW CODE: Immediately update the UI ---
      const deskBtn = document.querySelector(`.grid-container .btn[data-desk-id="${deskId}"]`);
      if (deskBtn) {
          deskBtn.classList.add("occupied");
          // Optionally set a title, though we might not have the username here immediately
          // unless returned by the API. A generic message or "You" works for immediate feedback.
          deskBtn.title = "Occupied by you"; 
      }
      // ------------------------------------------
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

      // --- NEW CODE: Immediately update the UI ---
      const deskBtn = document.querySelector(`.grid-container .btn[data-desk-id="${deskId}"]`);
      if (deskBtn) {
          deskBtn.classList.remove("occupied");
          deskBtn.title = ""; // Clear the tooltip
      }
      // ------------------------------------------
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

// --------------------------- Sync State Logic ---------------------------
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

    // Re-apply selection visual state after HTML replacement
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
if (reportBtn && bugModal) {
    reportBtn.addEventListener('click', () => {
        bugModal.style.display = 'flex';
    });

    // Close logic
    const closeBug = () => bugModal.style.display = 'none';
    if(closeBugBtn) closeBugBtn.addEventListener('click', closeBug);
    
    // Close on background click
    bugModal.addEventListener('click', (e) => {
        if (e.target === bugModal) closeBug();
    });

    // Handle Submission
    bugForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const deskId = reservationActions?.dataset?.currentDesk;
        
        if (!deskId) {
            setStatusMessage("No desk selected/paired!", "error");
            return;
        }

        const btn = bugForm.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = 'Submitting...';

        const formData = new FormData();
        formData.append('desk_id', deskId);
        formData.append('title', document.getElementById('bugTitle').value);
        formData.append('description', document.getElementById('bugDescription').value);
        formData.append('priority', document.getElementById('bugPriority').value);

        fetch('/submit_bug/', {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                setStatusMessage("Bug reported successfully!", "success");
                closeBug();
                bugForm.reset();
            } else {
                setStatusMessage(data.message, "error");
            }
        })
        .catch(err => {
            console.error(err);
            setStatusMessage("Failed to submit bug report", "error");
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    });
}