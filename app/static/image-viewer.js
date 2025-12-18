// Image viewer modal functions

async function loadAndDisplayImage(filename) {
  const imageViewerModal = document.getElementById("imageViewerModal");

  try {
    // Load metadata
    const metaResponse = await fetch(`/api/metadata/${filename}`);
    const metaData = await metaResponse.json();

    // Get image info from gallery
    const galleryResponse = await fetch("/api/images");
    const galleryData = await galleryResponse.json();
    const imageInfo = galleryData.images.find(
      (img) => img.filename === filename
    );

    // Update modal header
    document.getElementById("viewerImageTitle").textContent =
      metaData.metadata.title || filename;

    // Update image
    document.getElementById("viewerImage").src = viewerImageData.url;

    // Update metadata fields
    document.getElementById("viewerFilename").textContent = filename;

    const titleEl = document.getElementById("viewerTitle");
    if (metaData.metadata.title) {
      titleEl.textContent = metaData.metadata.title;
      titleEl.classList.remove("metadata-empty");
    } else {
      titleEl.textContent = "No title";
      titleEl.classList.add("metadata-empty");
    }

    const descEl = document.getElementById("viewerDescription");
    if (metaData.metadata.description) {
      descEl.textContent = metaData.metadata.description;
      descEl.classList.remove("metadata-empty");
    } else {
      descEl.textContent = "No description";
      descEl.classList.add("metadata-empty");
    }

    // Update tags
    const tagsEl = document.getElementById("viewerTags");
    if (metaData.metadata.tags && metaData.metadata.tags.length > 0) {
      tagsEl.innerHTML = metaData.metadata.tags
        .map((tag) => `<span class="metadata-tag">${tag.name}</span>`)
        .join("");
    } else {
      tagsEl.innerHTML = '<span class="metadata-empty">No tags</span>';
    }

    // Update uploaded date
    document.getElementById("viewerUploaded").textContent = new Date(
      metaData.metadata.uploaded_at
    ).toLocaleString();

    // Update size
    if (imageInfo) {
      const sizeInKB = (imageInfo.size / 1024).toFixed(2);
      document.getElementById(
        "viewerSize"
      ).textContent = `${sizeInKB} KB`;
    }

    // Show modal
    imageViewerModal.classList.add("active");

    // Show eink version dropdown
    document.getElementById("einkVersionDropdown").style.display =
      "block";
    populateEinkVersionMenu();
  } catch (error) {
    console.error("Error loading image data:", error);
    showMessage("Error loading image metadata", "error");
  }
}

function closeImageViewer() {
  const imageViewerModal = document.getElementById("imageViewerModal");
  imageViewerModal.classList.remove("active");
  viewerImageData = null;
  document.getElementById("einkVersionMenu").style.display = "none";
  document.getElementById("einkVersionDropdown").style.display = "none";
}

function editFromViewer() {
  if (viewerImageData && viewerImageData.filename) {
    openMetadataModal(viewerImageData.filename);
  }
}

// Initialize image viewer event handlers
function initializeImageViewerHandlers() {
  const einkVersionBtn = document.getElementById("einkVersionBtn");
  const editFromViewerBtn = document.getElementById("editFromViewerBtn");
  const closeImageViewerBtn = document.getElementById("closeImageViewerBtn");

  if (einkVersionBtn) {
    einkVersionBtn.addEventListener("click", toggleEinkVersionMenu);
  }
  if (editFromViewerBtn) {
    editFromViewerBtn.addEventListener("click", editFromViewer);
  }
  if (closeImageViewerBtn) {
    closeImageViewerBtn.addEventListener("click", closeImageViewer);
  }
}

