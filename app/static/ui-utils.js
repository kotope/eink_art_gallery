// UI utilities for message display and modal management

function showMessage(message, type) {
  const messageDiv = document.getElementById("message");
  messageDiv.textContent = message;
  messageDiv.className = `message ${type}`;
  setTimeout(() => {
    messageDiv.className = "message";
  }, 5000);
}

// Initialize global UI event listeners
function initializeUIEventListeners() {
  const metadataModal = document.getElementById("metadataModal");
  const imageViewerModal = document.getElementById("imageViewerModal");

  // Close modal when clicking outside
  window.addEventListener("click", (event) => {
    if (event.target === metadataModal) {
      closeMetadataModal();
    }
    if (event.target === imageViewerModal) {
      closeImageViewer();
    }
    // Close eink version menu if clicking outside
    const einkMenu = document.getElementById("einkVersionMenu");
    const einkBtn = document.getElementById("einkVersionBtn");
    if (
      einkMenu &&
      einkMenu.style.display === "block" &&
      event.target !== einkBtn &&
      !einkMenu.contains(event.target)
    ) {
      einkMenu.style.display = "none";
    }
  });
}

