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
      
      // ✅ FIX: Save room immediately so desk.js finds it
      sessionStorage.setItem("lastDeskRoom", roomId);

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
        fetch(`/load_view/desks/?room=${roomLabel}`)
          .then(res => res.text())
          .then(html => {
            const mainContent = document.getElementById("main-content");
            if (!mainContent) return;
            mainContent.innerHTML = html;

            document.dispatchEvent(new Event("overviewLoaded"));

            fadeOverlay.classList.remove("fade-in");
            setTimeout(() => fadeOverlay.remove(), 500);
            overlay.remove();
          })
          .catch(err => console.error("❌ Error loading desks view:", err));
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
    });
  }
});

document.addEventListener("DOMContentLoaded", initOverview);
document.addEventListener("overviewLoaded", initOverview);