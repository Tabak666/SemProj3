function initOverview() {
  console.log("✅ initOverview() initialized");

  const roomButtons = document.querySelectorAll(".overview-grid button");
  
  roomButtons.forEach(button => {
    button.replaceWith(button.cloneNode(true));
  });

  const freshButtons = document.querySelectorAll(".overview-grid button");

  freshButtons.forEach(button => {
    button.addEventListener("click", () => {
      console.log(`🟢 Room button clicked: ${button.dataset.label}`);

      const roomLabel = button.dataset.label; // e.g. "Room C"
      const roomId = roomLabel.replace("Room ", ""); // "C"
      
      // ✅ Get the selected floor from the dropdown
      const floorSelect = document.getElementById("floorSelect");
      const selectedFloor = floorSelect ? floorSelect.options[floorSelect.selectedIndex].text : "Floor 1";
      
      // ✅ Save both room AND floor to sessionStorage
      sessionStorage.setItem("lastDeskRoom", roomId);
      sessionStorage.setItem("lastDeskFloor", selectedFloor);

      console.log(`[overview] Selected: ${selectedFloor} - Room ${roomId}`);

      // Force sidebar to update visually
      document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
      const desksBtn = document.querySelector('.view-btn[data-view="desks"]');
      if (desksBtn) desksBtn.classList.add("active");

      const rect = button.getBoundingClientRect();

      // Animation overlay
      const overlay = document.createElement("div");
      overlay.classList.add("zoom-overlay");
      Object.assign(overlay.style, {
        position: "fixed",
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        backgroundImage: window.getComputedStyle(button).backgroundImage,
        backgroundSize: "cover",
        backgroundPosition: "center",
        borderRadius: "12px",
        zIndex: "9999",
        transition: "all 0.8s ease-in-out"
      });
      document.body.appendChild(overlay);

      const fadeOverlay = document.createElement("div");
      fadeOverlay.classList.add("fade-overlay");
      document.body.appendChild(fadeOverlay);

      requestAnimationFrame(() => {
        overlay.style.left = "0";
        overlay.style.top = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.borderRadius = "0";
        fadeOverlay.classList.add("fade-in");
      });

      setTimeout(() => {
        // ✅ Dispatch custom event so index.html knows room was selected
        document.dispatchEvent(new CustomEvent('roomSelected', { 
          detail: { room: roomId, floor: selectedFloor } 
        }));

        fadeOverlay.classList.remove("fade-in");
        setTimeout(() => fadeOverlay.remove(), 500);
        overlay.remove();
      }, 800);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const floorSelect = document.getElementById("floorSelect");
  const corridorLabel = document.getElementById("corridorLabel");

  if (floorSelect && corridorLabel) {
    floorSelect.addEventListener("change", () => {
      const floorValue = floorSelect.options[floorSelect.selectedIndex].text;
      corridorLabel.textContent = `${floorValue} – LINAK Corridor`;
      // ✅ Save floor when changed
      sessionStorage.setItem("lastDeskFloor", floorValue);
    });
  }
});

document.addEventListener("DOMContentLoaded", initOverview);
document.addEventListener("overviewLoaded", initOverview);