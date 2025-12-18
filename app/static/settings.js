// Settings view management

function openSettings() {
  document.getElementById("settingsView").style.display = "flex";
  // Hide gallery view
  document.getElementById("galleryView").style.display = "none";
}

function closeSettings() {
  document.getElementById("settingsView").style.display = "none";
  // Show gallery view
  document.getElementById("galleryView").style.display = "block";
}

function initializeSettingsHandlers() {
  // Settings button click handler
  const settingsMenuBtn = document.getElementById("settingsMenuBtn");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const settingsView = document.getElementById("settingsView");

  if (settingsMenuBtn) {
    settingsMenuBtn.addEventListener("click", openSettings);
  }

  if (closeSettingsBtn) {
    closeSettingsBtn.addEventListener("click", closeSettings);
  }

  // Close settings when clicking outside the content area
  if (settingsView) {
    settingsView.addEventListener("click", function(event) {
      if (event.target === this) {
        closeSettings();
      }
    });
  }
}

