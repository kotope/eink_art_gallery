// Upload functionality

function initializeUploadHandlers() {
  const uploadBox = document.getElementById("uploadBox");
  const fileInput = document.getElementById("fileInput");
  const titleInput = document.getElementById("titleInput");
  const uploadBtn = document.getElementById("uploadBtn");

  // Upload box click - only open dialog if no file selected and form is not showing
  uploadBox.addEventListener("click", (e) => {
    // Don't open file dialog if clicking on the title input or upload button
    if (e.target === titleInput || e.target === uploadBtn) {
      return;
    }
    if (!fileInput.files || fileInput.files.length === 0) {
      fileInput.click();
    }
  });

  // Drag and drop
  uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = "#764ba2";
    uploadBox.style.background = "#f0f2ff";
  });

  uploadBox.addEventListener("dragleave", () => {
    uploadBox.style.borderColor = "#667eea";
    uploadBox.style.background = "#f8f9ff";
  });

  uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = "#667eea";
    uploadBox.style.background = "#f8f9ff";

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      showUploadForm();
    }
  });

  // File input change
  fileInput.addEventListener("change", showUploadForm);

  // Upload button click
  uploadBtn.addEventListener("click", uploadImage);
}

function showUploadForm() {
  const titleInput = document.getElementById("titleInput");
  const uploadBtn = document.getElementById("uploadBtn");

  titleInput.style.display = "block";
  uploadBtn.style.display = "block";
  titleInput.focus();
}

async function uploadImage() {
  const fileInput = document.getElementById("fileInput");
  const titleInput = document.getElementById("titleInput");
  const uploadBtn = document.getElementById("uploadBtn");

  if (!fileInput.files.length) {
    showMessage("Please select a file", "error");
    return;
  }

  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<span class="loading"></span>';

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const title = titleInput.value;
  const url = title
    ? `/api/images/upload?title=${encodeURIComponent(title)}`
    : "/api/images/upload";

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    logger.info("Upload response:", response.status, data);

    if (response.ok) {
      showMessage("Image uploaded successfully!", "success");
      fileInput.value = "";
      titleInput.value = "";
      titleInput.style.display = "none";
      uploadBtn.style.display = "none";
      // Add a small delay to ensure file is written to disk
      await new Promise(resolve => setTimeout(resolve, 500));
      await loadGallery();
      await loadStatus();
    } else {
      showMessage(data.message || "Upload failed", "error");
    }
  } catch (error) {
    logger.error("Upload error:", error);
    showMessage("Error uploading image: " + error.message, "error");
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = "Upload";
  }
}

