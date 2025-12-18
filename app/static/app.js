// Main application initialization

// Initialize
document.addEventListener("DOMContentLoaded", function() {
  // Initialize all handlers
  initializeUploadHandlers();
  initializeUIEventListeners();
  initializeImageViewerHandlers();
  initializeTagInputHandler();
  initializeMetadataModalHandlers();
  initializeSettingsHandlers();

  // Load initial data
  loadGallery();
  loadStatus();
  loadTags();
  // loadConfigurationSection is called via DOMContentLoaded listener in config-loader.js
  setInterval(loadStatus, 5000); // Refresh status every 5 seconds
});

