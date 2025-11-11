function initOverview() {
  console.log("✅ initOverview() initialized");

  const roomButtons = document.querySelectorAll(".overview-grid button");
  console.log("Found room buttons:", roomButtons.length);

  roomButtons.forEach(button => {
    button.addEventListener("click", () => {
      console.log(`🟢 Room button clicked: ${button.dataset.label}`);

      const rect = button.getBoundingClientRect();

      // === 1️⃣ ZOOM OVERLAY ===
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
        transition: "all 1.5s ease-in-out"
      });
      document.body.appendChild(overlay);

      // === 2️⃣ WHITE FADE OVERLAY ===
      const fadeOverlay = document.createElement("div");
      fadeOverlay.classList.add("fade-overlay");
      document.body.appendChild(fadeOverlay);

      // Trigger both animations
      requestAnimationFrame(() => {
        overlay.style.left = "0";
        overlay.style.top = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.borderRadius = "0";
        fadeOverlay.classList.add("fade-in"); // fade to white *while zooming*
      });

      // === 3️⃣ When zoom animation finishes ===
      overlay.addEventListener(
        "transitionend",
        () => {
          console.log("🔁 Zoom complete — loading desks view...");
          fetch("/load_view/desks/")
            .then(response => response.text())
            .then(html => {
              const mainContent = document.getElementById("main-content");
              if (mainContent) mainContent.innerHTML = html;

              // short delay for smoother transition into desks
              setTimeout(() => {
                fadeOverlay.classList.remove("fade-in"); // fade *out* from white
                setTimeout(() => fadeOverlay.remove(), 500); // remove after fade-out
              }, 100); // small delay before fading out

              overlay.remove();
              console.log("✅ Desks view loaded dynamically");
            })
            .catch(err => console.error("❌ Error loading desks view:", err));
        },
        { once: true }
      );
    });
  });
}

document.addEventListener("DOMContentLoaded", initOverview);
document.addEventListener("overviewLoaded", initOverview);

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
