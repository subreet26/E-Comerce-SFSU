/**
 * Image preview module
 * Handles image upload preview functionality
 */

/**
 * Initializes image preview for an input/preview pair
 * @param {string} inputId - ID of the file input element
 * @param {string} previewId - ID of the preview image element
 * @param {string} iconId - ID of the upload icon element (optional)
 */
export function initImagePreview(inputId, previewId, iconId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  const icon = document.getElementById(iconId);

  if (!input) return;

  input.addEventListener('change', function () {
    const file = this.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = e => {
        if (preview) {
          preview.src = e.target.result;
          preview.classList.remove('hidden');
        }
        if (icon) {
          icon.classList.add('hidden');
        }
      };
      reader.readAsDataURL(file);
    }
  });
}
