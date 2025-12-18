// Gallery management functions

let viewerImageData = null;

async function loadGallery() {
  const gallery = document.getElementById("gallery");

  try {
    const response = await fetch("/api/images?t=" + Date.now());
    const data = await response.json();

    if (data.status === "success") {
      if (data.images.length === 0) {
        gallery.innerHTML =
          '<div class="empty-gallery">No images yet. Upload one to get started!</div>';
      } else {
        gallery.innerHTML = data.images
          .map(
            (img) => `
                      <div class="gallery-item">
                          <img src="${img.url}?t=${Date.now()}" alt="${
              img.title || img.filename
            }" class="gallery-item-image" onclick="viewImage('${
              img.url
            }', '${
              img.title || img.filename
            }')" style="cursor: pointer;" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E%3Crect fill=%22%23e0e0e0%22 width=%22100%22 height=%22100%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2214%22 fill=%22%23999%22%3E?%3C/text%3E%3C/svg%3E'">
                          <div class="gallery-item-info">
                              <div class="gallery-item-title" title="${
                                img.title || img.filename
                              }">${img.title || img.filename}</div>
                              <div class="gallery-item-filename" title="${
                                img.filename
                              }">${img.filename}</div>
                              ${
                                img.tags && img.tags.length > 0
                                  ? `<div class="gallery-item-tags">${img.tags
                                      .slice(0, 3)
                                      .map(
                                        (tag) =>
                                          `<span class="tag-badge">${tag.name}</span>`
                                      )
                                      .join("")}</div>`
                                  : ""
                              }
                              <div class="gallery-item-actions">
                                  <button class="btn-small btn-edit" onclick="openMetadataModal('${
                                    img.filename
                                  }')">Edit</button>
                                  <button class="btn-small btn-delete" onclick="deleteImage('${
                                    img.filename
                                  }')">Delete</button>
                              </div>
                          </div>
                      </div>
                  `
          )
          .join("");
      }
    }
  } catch (error) {
    gallery.innerHTML =
      '<div class="empty-gallery">Error loading gallery</div>';
    console.error("Error loading gallery:", error);
  }
}

async function deleteImage(filename) {
  if (!confirm(`Are you sure you want to delete '${filename}'?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/images/${filename}`, {
      method: "DELETE",
    });

    const data = await response.json();

    if (response.ok) {
      showMessage("Image deleted successfully!", "success");
      loadGallery();
      loadStatus();
      loadTags();
    } else {
      showMessage(data.message || "Delete failed", "error");
    }
  } catch (error) {
    showMessage("Error deleting image: " + error.message, "error");
  }
}

function viewImage(url, title) {
  // Extract filename from URL
  const filename = url.split("/").pop();
  viewerImageData = { url, title, filename };

  // Load metadata and display image
  loadAndDisplayImage(filename);
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    if (data.status === "success") {
      document.getElementById("status-total").textContent =
        data.total_images;
      document.getElementById("status-api").textContent = "✅ Running";
    }
  } catch (error) {
    document.getElementById("status-api").textContent = "❌ Error";
  }
}

