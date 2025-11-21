function initOverview() {
  console.log("✅ initOverview() initialized");

  const roomButtons = document.querySelectorAll(".overview-grid button");
  console.log("Found room buttons:", roomButtons.length);

  roomButtons.forEach(button => {
    // Remove previous event listeners if any
    button.replaceWith(button.cloneNode(true));
  });

  const freshButtons = document.querySelectorAll(".overview-grid button");

  freshButtons.forEach(button => {
    button.addEventListener("click", () => {
      console.log(`🟢 Room button clicked: ${button.dataset.label}`);

      const rect = button.getBoundingClientRect();

      // 1️⃣ Create zoom overlay
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

      // 2️⃣ Create fade overlay
      const fadeOverlay = document.createElement("div");
      fadeOverlay.classList.add("fade-overlay");
      document.body.appendChild(fadeOverlay);

      // Trigger animations
      requestAnimationFrame(() => {
        overlay.style.left = "0";
        overlay.style.top = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.borderRadius = "0";
        fadeOverlay.classList.add("fade-in");
      });

      // 3️⃣ Wait for animation and load desks
      setTimeout(() => {
        const roomLabel = button.dataset.label;
        console.log(`🔁 Loading desks for ${roomLabel}...`);

        fetch(`/load_view/desks/?room=${roomLabel}`)
          .then(res => res.text())
          .then(html => {
            const mainContent = document.getElementById("main-content");
            if (!mainContent) {
              console.error("❌ #main-content not found!");
              return;
            }
            mainContent.innerHTML = html;

            // Reinitialize overview buttons if needed
            document.dispatchEvent(new Event("overviewLoaded"));

            // Fade out
            fadeOverlay.classList.remove("fade-in");
            setTimeout(() => fadeOverlay.remove(), 500);
            overlay.remove();

            console.log(`✅ Desks view for ${roomLabel} loaded`);
          })
          .catch(err => console.error("❌ Error loading desks view:", err));
      }, 800); // matches the overlay transition duration
    });
  });
}

// Floor selector change
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

// Initialize overview
document.addEventListener("DOMContentLoaded", initOverview);
document.addEventListener("overviewLoaded", initOverview);
