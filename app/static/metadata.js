// Metadata modal and tag management

let currentImageFilename = null;
let allTags = [];

function openMetadataModal(filename) {
  const metadataModal = document.getElementById("metadataModal");
  currentImageFilename = filename;
  metadataModal.classList.add("active");

  // Load current metadata
  loadImageMetadata(filename);
}

function closeMetadataModal() {
  const metadataModal = document.getElementById("metadataModal");
  const imageViewerModal = document.getElementById("imageViewerModal");

  metadataModal.classList.remove("active");
  const wasEditingFromViewer =
    viewerImageData && viewerImageData.filename === currentImageFilename;
  currentImageFilename = null;
  document.getElementById("metadataForm").reset();
  document.getElementById("existingTags").innerHTML = "";

  // Refresh viewer if it's still open
  if (
    wasEditingFromViewer &&
    imageViewerModal.classList.contains("active")
  ) {
    loadAndDisplayImage(viewerImageData.filename);
  }
}

async function loadImageMetadata(filename) {
  try {
    const response = await fetch(`/api/metadata/${filename}`);
    const data = await response.json();

    if (data.status === "success") {
      const metadata = data.metadata;
      document.getElementById("metadataTitle").value =
        metadata.title || "";
      document.getElementById("metadataDescription").value =
        metadata.description || "";

      // Display existing tags
      const tagsContainer = document.getElementById("existingTags");
      tagsContainer.innerHTML = metadata.tags
        .map(
          (tag) =>
            `<div class="tag-item">
                ${tag.name}
                <button type="button" class="tag-remove" onclick="removeTag('${filename}', '${tag.name}')" title="Remove tag">&times;</button>
              </div>`
        )
        .join("");

      // Update suggested tags
      updateSuggestedTags(metadata.tags.map((t) => t.name));

      // Refresh viewer if it's still open and showing this image
      if (
        viewerImageData &&
        viewerImageData.filename === filename &&
        document.getElementById("imageViewerModal").classList.contains("active")
      ) {
        loadAndDisplayImage(filename);
      }
    }
  } catch (error) {
    console.error("Error loading image metadata:", error);
    showMessage("Error loading metadata", "error");
  }
}

function updateSuggestedTags(currentTags) {
  const suggestedContainer = document.getElementById("suggestedTags");
  const usedTagNames = new Set(currentTags);
  const suggestions = allTags.filter(
    (tag) => !usedTagNames.has(tag.name) && tag.name !== "latest"
  );

  if (suggestions.length > 0) {
    suggestedContainer.style.display = "flex";
    suggestedContainer.innerHTML =
      '<small style="width: 100%; color: #999;">Suggested:</small>' +
      suggestions
        .slice(0, 5)
        .map(
          (tag) =>
            `<button type="button" class="suggested-tag" onclick="addSuggestedTag('${tag.name}')">${tag.name}</button>`
        )
        .join("");
  } else {
    suggestedContainer.style.display = "none";
  }
}

async function addNewTag() {
  const tagInput = document.getElementById("newTagInput");
  const tagName = tagInput.value.trim();

  if (!tagName) {
    showMessage("Please enter a tag name", "error");
    return;
  }

  if (!/^[a-zA-Z0-9\s\-_]+$/.test(tagName)) {
    showMessage(
      "Tag can only contain letters, numbers, spaces, hyphens, and underscores",
      "error"
    );
    return;
  }

  try {
    const response = await fetch(
      `/api/metadata/${currentImageFilename}/tags`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tag: tagName }),
      }
    );

    const data = await response.json();

    if (response.ok) {
      tagInput.value = "";
      loadImageMetadata(currentImageFilename);
      showMessage(`Tag '${tagName}' added successfully!`, "success");
      loadTags(); // Update tag list
      loadGallery(); // Update gallery to show new tags
    } else {
      showMessage(data.message || "Failed to add tag", "error");
    }
  } catch (error) {
    showMessage("Error adding tag: " + error.message, "error");
  }
}

function addSuggestedTag(tagName) {
  document.getElementById("newTagInput").value = tagName;
  addNewTag();
}

async function removeTag(filename, tagName) {
  try {
    const response = await fetch(
      `/api/metadata/${filename}/tags/${encodeURIComponent(tagName)}`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json();

    if (response.ok) {
      loadImageMetadata(filename);
      showMessage(`Tag '${tagName}' removed successfully!`, "success");
      loadTags(); // Update tag list
      loadGallery(); // Update gallery to show updated tags
    } else {
      showMessage(data.message || "Failed to remove tag", "error");
    }
  } catch (error) {
    showMessage("Error removing tag: " + error.message, "error");
  }
}

async function saveMetadata() {
  const title = document.getElementById("metadataTitle").value;
  const description = document.getElementById(
    "metadataDescription"
  ).value;
  const imageViewerModal = document.getElementById("imageViewerModal");

  try {
    const response = await fetch(
      `/api/metadata/${currentImageFilename}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, description }),
      }
    );

    const data = await response.json();

    if (response.ok) {
      showMessage("Metadata saved successfully!", "success");
      const wasEditingFromViewer =
        viewerImageData &&
        viewerImageData.filename === currentImageFilename;
      closeMetadataModal();
      loadGallery();

      // Refresh viewer if it's still open
      if (
        wasEditingFromViewer &&
        imageViewerModal.classList.contains("active")
      ) {
        loadAndDisplayImage(viewerImageData.filename);
      }
    } else {
      showMessage(data.message || "Failed to save metadata", "error");
    }
  } catch (error) {
    showMessage("Error saving metadata: " + error.message, "error");
  }
}

async function loadTags() {
  try {
    const response = await fetch("/api/tags");
    const data = await response.json();

    if (data.status === "success") {
      allTags = data.tags;
      const totalTags = data.tags.length;
      document.getElementById("status-tags").textContent = totalTags;
    }
  } catch (error) {
    console.error("Error loading tags:", error);
  }
}

// Initialize tag input Enter key handler
function initializeTagInputHandler() {
  const newTagInput = document.getElementById("newTagInput");
  const addTagBtn = document.getElementById("addTagBtn");

  if (newTagInput) {
    newTagInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addNewTag();
      }
    });
  }

  if (addTagBtn) {
    addTagBtn.addEventListener("click", addNewTag);
  }
}

// Initialize metadata modal event handlers
function initializeMetadataModalHandlers() {
  const cancelMetadataBtn = document.getElementById("cancelMetadataBtn");
  const saveMetadataBtn = document.getElementById("saveMetadataBtn");

  if (cancelMetadataBtn) {
    cancelMetadataBtn.addEventListener("click", closeMetadataModal);
  }
  if (saveMetadataBtn) {
    saveMetadataBtn.addEventListener("click", saveMetadata);
  }
}

