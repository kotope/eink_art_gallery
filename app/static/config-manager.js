// Display Configuration Management
let currentDisplayConfig = null;

async function initDisplayConfigManager() {
  document
    .getElementById("refreshDisplaysBtn")
    .addEventListener("click", loadDisplaysList);
  document
    .getElementById("saveConfigBtn")
    .addEventListener("click", saveDisplayConfig);
  document
    .getElementById("resetConfigBtn")
    .addEventListener("click", resetDisplayConfig);
  document
    .getElementById("duplicateConfigBtn")
    .addEventListener("click", duplicateDisplayConfig);
  document
    .getElementById("exportConfigBtn")
    .addEventListener("click", exportDisplayConfig);
  document
    .getElementById("deleteConfigBtn")
    .addEventListener("click", deleteDisplayConfig);
  document
    .getElementById("importConfigBtn")
    .addEventListener("click", importDisplayConfig);
  document
    .getElementById("displaySelect")
    .addEventListener("change", onDisplaySelected);

  await loadDisplaysList();
}

async function loadDisplaysList() {
  try {
    const response = await fetch("/api/displays");
    const data = await response.json();

    if (data.status !== "success") {
      showMessage("Failed to load displays: " + data.message, "error");
      return;
    }

    const select = document.getElementById("displaySelect");
    const displays = data.displays || [];

    select.innerHTML = '<option value="">Select a display...</option>';
    displays.forEach((display) => {
      const label = display.is_custom
        ? `${display.name} (Custom)`
        : display.name;
      const option = document.createElement("option");
      option.value = display.name;
      option.textContent = label;
      select.appendChild(option);
    });

    // Update eink version menu too
    populateEinkVersionMenu();
  } catch (error) {
    logger.error("Error loading displays:", error);
    showMessage("Error loading displays: " + error.message, "error");
  }
}

async function onDisplaySelected() {
  const displayName = document.getElementById("displaySelect").value;
  if (!displayName) {
    document.getElementById("configEditorContainer").style.display =
      "none";
    currentDisplayConfig = null;
    return;
  }

  await loadDisplayConfig(displayName);
}

async function loadDisplayConfig(displayName) {
  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(displayName)}/config`
    );
    const data = await response.json();

    if (data.status !== "success") {
      showMessage("Failed to load config: " + data.message, "error");
      return;
    }

    currentDisplayConfig = {
      name: displayName,
      content: data.content,
    };

    document.getElementById("configEditor").value = data.content;
    document.getElementById("configEditorContainer").style.display =
      "block";
    updateConfigInfo(displayName);
  } catch (error) {
    logger.error("Error loading display config:", error);
    showMessage(
      "Error loading display config: " + error.message,
      "error"
    );
  }
}

async function updateConfigInfo(displayName) {
  try {
    const response = await fetch("/api/displays");
    const data = await response.json();
    const displays = data.displays || [];
    const display = displays.find((d) => d.name === displayName);

    if (display) {
      const typeInfo = display.is_custom
        ? "Custom (Modified)"
        : "Default";
      const modifiedInfo = display.modified_at
        ? new Date(display.modified_at).toLocaleString()
        : "-";

      document.getElementById("configTypeInfo").textContent = typeInfo;
      document.getElementById("configModifiedInfo").textContent =
        modifiedInfo;
      document.getElementById("deleteConfigBtn").style.display =
        display.is_custom ? "block" : "none";
    }
  } catch (error) {
    logger.warn("Could not update config info:", error);
  }
}

async function saveDisplayConfig() {
  if (!currentDisplayConfig) {
    showMessage("No display selected", "error");
    return;
  }

  const content = document.getElementById("configEditor").value;
  if (!content.trim()) {
    showMessage("Configuration cannot be empty", "error");
    return;
  }

  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(
        currentDisplayConfig.name
      )}/config`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      }
    );

    const data = await response.json();
    if (data.status !== "success") {
      showMessage("Failed to save: " + data.message, "error");
      return;
    }

    currentDisplayConfig.content = content;
    await updateConfigInfo(currentDisplayConfig.name);
    showMessage(
      `Configuration for '${currentDisplayConfig.name}' saved successfully`,
      "success"
    );
    await loadDisplaysList();
  } catch (error) {
    logger.error("Error saving display config:", error);
    showMessage("Error saving configuration: " + error.message, "error");
  }
}

async function resetDisplayConfig() {
  if (!currentDisplayConfig) {
    showMessage("No display selected", "error");
    return;
  }

  if (
    !confirm(
      `Reset '${currentDisplayConfig.name}' to default configuration?`
    )
  ) {
    return;
  }

  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(
        currentDisplayConfig.name
      )}/reset`,
      { method: "POST" }
    );

    const data = await response.json();
    if (data.status !== "success") {
      showMessage("Failed to reset: " + data.message, "error");
      return;
    }

    showMessage(`Configuration reset to default`, "success");
    await loadDisplayConfig(currentDisplayConfig.name);
    await loadDisplaysList();
  } catch (error) {
    logger.error("Error resetting display config:", error);
    showMessage(
      "Error resetting configuration: " + error.message,
      "error"
    );
  }
}

async function duplicateDisplayConfig() {
  if (!currentDisplayConfig) {
    showMessage("No display selected", "error");
    return;
  }

  const newName = prompt(
    `Enter name for the duplicate of '${currentDisplayConfig.name}':`
  );
  if (!newName) return;

  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(
        currentDisplayConfig.name
      )}/duplicate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_name: newName }),
      }
    );

    const data = await response.json();
    if (data.status !== "success") {
      showMessage("Failed to duplicate: " + data.message, "error");
      return;
    }

    showMessage(`Configuration duplicated as '${newName}'`, "success");
    await loadDisplaysList();
    document.getElementById("displaySelect").value = newName;
    await loadDisplayConfig(newName);
  } catch (error) {
    logger.error("Error duplicating display config:", error);
    showMessage(
      "Error duplicating configuration: " + error.message,
      "error"
    );
  }
}

async function exportDisplayConfig() {
  if (!currentDisplayConfig) {
    showMessage("No display selected", "error");
    return;
  }

  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(
        currentDisplayConfig.name
      )}/export`
    );

    if (!response.ok) {
      showMessage("Failed to export configuration", "error");
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentDisplayConfig.name}.yaml`;
    a.click();
    window.URL.revokeObjectURL(url);

    showMessage("Configuration exported", "success");
  } catch (error) {
    logger.error("Error exporting display config:", error);
    showMessage(
      "Error exporting configuration: " + error.message,
      "error"
    );
  }
}

async function deleteDisplayConfig() {
  if (!currentDisplayConfig) {
    showMessage("No display selected", "error");
    return;
  }

  if (
    !confirm(
      `Delete custom configuration for '${currentDisplayConfig.name}'? This cannot be undone.`
    )
  ) {
    return;
  }

  try {
    const response = await fetch(
      `/api/displays/${encodeURIComponent(currentDisplayConfig.name)}`,
      { method: "DELETE" }
    );

    const data = await response.json();
    if (data.status !== "success") {
      showMessage("Failed to delete: " + data.message, "error");
      return;
    }

    showMessage(
      `Configuration deleted. Default configuration restored.`,
      "success"
    );
    currentDisplayConfig = null;
    document.getElementById("configEditorContainer").style.display =
      "none";
    document.getElementById("displaySelect").value = "";
    await loadDisplaysList();
  } catch (error) {
    logger.error("Error deleting display config:", error);
    showMessage(
      "Error deleting configuration: " + error.message,
      "error"
    );
  }
}

async function importDisplayConfig() {
  const fileInput = document.getElementById("importConfigFile");
  if (!fileInput.files || fileInput.files.length === 0) {
    showMessage("Please select a file to import", "error");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  const overwrite = document.getElementById(
    "overwriteImportCheckbox"
  ).checked;
  const url = `/api/displays/import${overwrite ? "?overwrite=true" : ""}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.status !== "success") {
      showMessage("Failed to import: " + data.message, "error");
      return;
    }

    showMessage(
      `Configuration '${data.display_name}' imported successfully`,
      "success"
    );
    fileInput.value = "";
    await loadDisplaysList();
    document.getElementById("displaySelect").value = data.display_name;
    await loadDisplayConfig(data.display_name);
  } catch (error) {
    logger.error("Error importing display config:", error);
    showMessage(
      "Error importing configuration: " + error.message,
      "error"
    );
  }
}

// Load available displays
async function loadAvailableDisplays() {
  try {
    // Try to fetch a random eink image to get available displays from error message
    // Since we don't have a dedicated endpoint, we'll get displays from status or try directly
    const response = await fetch("/api/images/eink/random");
    // We'll catch the error and parse the available displays from it
  } catch (error) {
    // Ignore for now, we'll handle it differently
  }

  // For now, we'll create the dropdown dynamically based on common display types
  // In production, you might want to add a dedicated API endpoint for listing displays
  populateEinkVersionMenu();
}

function populateEinkVersionMenu() {
  const menuDiv = document.getElementById("einkVersionMenu");
  const dropdown = document.getElementById("einkVersionDropdown");

  // Fetch available displays from API
  fetch("/api/displays")
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success" && data.displays) {
        const displays = data.displays.map((d) => d.name);
        if (displays.length > 0) {
          menuDiv.innerHTML = displays
            .map(
              (display) =>
                `<button class="eink-version-item" onclick="openEinkVersion('${display}')">${display}</button>`
            )
            .join("");
        } else {
          populateWithDefaultDisplays();
        }
      } else {
        populateWithDefaultDisplays();
      }
    })
    .catch(() => {
      populateWithDefaultDisplays();
    });

  function populateWithDefaultDisplays() {
    menuDiv.innerHTML =
      '<button class="eink-version-item" onclick="openEinkVersion(\'7.3inch_eink_spectra_6\')">7.3" E-ink Spectra 6</button>';
  }

  // Show dropdown if filename is available
  if (viewerImageData && viewerImageData.filename) {
    dropdown.style.display = "block";
  }
}
