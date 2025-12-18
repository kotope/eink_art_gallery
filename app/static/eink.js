// E-ink version handling

let availableDisplays = [];

function toggleEinkVersionMenu() {
  const menu = document.getElementById("einkVersionMenu");
  if (menu.style.display === "none" || menu.innerHTML === "") {
    populateEinkVersionMenu();
    menu.style.display = "block";
  } else {
    menu.style.display = "none";
  }
}

function populateEinkVersionMenu() {
  const menu = document.getElementById("einkVersionMenu");

  if (!menu.innerHTML) {
    // Load displays and populate menu
    if (availableDisplays.length === 0) {
      menu.innerHTML = '<div class="eink-version-item">Loading...</div>';
      // The displays should be loaded by config-loader.js and stored in availableDisplays
      // For now, we'll load from the config
      fetch("/api/config")
        .then((response) => response.json())
        .then((data) => {
          if (data.displays && data.displays.length > 0) {
            availableDisplays = data.displays;
            renderEinkVersionMenu();
          }
        })
        .catch((error) => {
          console.error("Error loading displays:", error);
          menu.innerHTML = '<div class="eink-version-item">Error loading displays</div>';
        });
    } else {
      renderEinkVersionMenu();
    }
  }
}

function renderEinkVersionMenu() {
  const menu = document.getElementById("einkVersionMenu");

  if (availableDisplays.length === 0) {
    menu.innerHTML = '<div class="eink-version-item">No displays available</div>';
  } else {
    menu.innerHTML = availableDisplays
      .map(
        (display) =>
          `<button class="eink-version-item" onclick="openEinkVersion('${display}')">${display}</button>`
      )
      .join("");
  }
}

function openEinkVersion(displayType) {
  if (!viewerImageData || !viewerImageData.filename) {
    showMessage("No image selected", "error");
    return;
  }

  // Extract basename from filename (remove extension)
  const basename = viewerImageData.filename.split(".")[0];

  // Open eink version in new tab
  const einkUrl = `/api/images/eink/${basename}?display=${encodeURIComponent(
    displayType
  )}`;
  window.open(einkUrl, "_blank");

  // Close the dropdown menu
  document.getElementById("einkVersionMenu").style.display = "none";
}

// Function to set available displays (called from config-loader.js)
function setAvailableDisplays(displays) {
  availableDisplays = displays;
}

