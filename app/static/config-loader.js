// Configuration HTML Loader
async function loadConfigurationSection() {
  try {
    const response = await fetch('/templates/config.html');
    const html = await response.text();

    const settingsBody = document.querySelector('.settings-body');
    if (settingsBody) {
      settingsBody.innerHTML = html;
      // Re-initialize the config manager after loading
      await initDisplayConfigManager();
    }
  } catch (error) {
    console.error('Error loading configuration section:', error);
    showMessage('Error loading configuration section', 'error');
  }
}

// Call this during initialization
document.addEventListener('DOMContentLoaded', loadConfigurationSection);
