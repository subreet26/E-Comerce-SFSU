/**
 * Image upload preview module
 * Handles drag-and-drop, multi-image selection (up to 5), thumbnail display,
 * and per-image remove buttons for both create and edit listing pages.
 *
 * Expected DOM (provided by create_listing.html / edit_listing.html):
 *   #image-input        — <input type="file" name="images" multiple>
 *   #drop-zone          — wrapper div (hidden when limit reached)
 *   #upload-icon        — inner content of drop-zone (icon + text)
 *   #thumbnail-row      — flex container for thumbnail cards
 *   #image-count        — <span> showing current count
 *   #hidden-inputs      — container for hidden file-list tracking (unused but kept)
 *   #existing-image-data — optional; data-images attr with current image URL (edit page)
 */

const MAX_IMAGES = 5;

// Accumulated File objects chosen by the user (new uploads only).
let selectedFiles = [];

// URL of an existing image already saved on the server (edit page only).
// If the user does not remove it, we keep it; if they do, we clear it.
let existingImageUrl = null;
let existingImageRemoved = false;

// ─── Boot ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const input      = document.getElementById('image-input');
  const dropZone   = document.getElementById('drop-zone');
  const thumbRow   = document.getElementById('thumbnail-row');
  const countSpan  = document.getElementById('image-count');
  const existingEl = document.getElementById('existing-image-data');

  if (!input || !dropZone || !thumbRow) return;

  // ── Load existing image (edit page) ──────────────────────────────────────
  if (existingEl) {
    const url = (existingEl.dataset.images || '').trim();
    if (url) {
      existingImageUrl = url;
      renderExistingThumb(url, thumbRow, countSpan, dropZone);
    }
  }

  // ── File-input change ─────────────────────────────────────────────────────
  input.addEventListener('change', () => {
    addFiles(Array.from(input.files), thumbRow, countSpan, dropZone);
    // Reset input so the same file can be re-selected if removed
    input.value = '';
  });

  // ── Drag-and-drop ─────────────────────────────────────────────────────────
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('border-slate-500', 'bg-slate-100');
  });

  ['dragleave', 'dragend'].forEach(evt =>
    dropZone.addEventListener(evt, () =>
      dropZone.classList.remove('border-slate-500', 'bg-slate-100')
    )
  );

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('border-slate-500', 'bg-slate-100');
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    addFiles(files, thumbRow, countSpan, dropZone);
  });

  // ── Form submit — sync FileList on the real input ────────────────────────
  const form = input.closest('form');
  if (form) {
    form.addEventListener('submit', () => syncInputFiles(input));
  }
});

// ─── Core helpers ────────────────────────────────────────────────────────────

function totalCount() {
  // existing (not removed) + new files
  const existingCount = (existingImageUrl && !existingImageRemoved) ? 1 : 0;
  return existingCount + selectedFiles.length;
}

function addFiles(files, thumbRow, countSpan, dropZone) {
  const slots = MAX_IMAGES - totalCount();
  if (slots <= 0) return;

  const toAdd = files.slice(0, slots);
  toAdd.forEach(file => {
    if (!ALLOWED_TYPE(file)) return;
    selectedFiles.push(file);
    renderNewThumb(file, thumbRow, countSpan, dropZone);
  });

  updateUI(countSpan, dropZone);
}

function ALLOWED_TYPE(file) {
  return /\.(jpe?g|png|gif|webp)$/i.test(file.name) || file.type.startsWith('image/');
}

// ─── Thumbnail renderers ──────────────────────────────────────────────────────

function renderExistingThumb(url, thumbRow, countSpan, dropZone) {
  const card = makeCard();

  const img = document.createElement('img');
  img.src = url;
  img.alt = 'Current image';
  img.className = 'w-full h-full object-cover';
  card.appendChild(img);

  const badge = makeBadge('Current');
  card.appendChild(badge);

  const removeBtn = makeRemoveBtn(() => {
    existingImageUrl = null;
    existingImageRemoved = true;
    card.remove();
    // Inject a hidden input so the server knows to clear the image
    ensureHiddenClearInput();
    updateUI(countSpan, dropZone);
  });
  card.appendChild(removeBtn);

  thumbRow.appendChild(card);
  updateUI(countSpan, dropZone);
}

function renderNewThumb(file, thumbRow, countSpan, dropZone) {
  const card = makeCard();
  const idx = selectedFiles.length - 1; // index of this file in selectedFiles

  const img = document.createElement('img');
  img.alt = file.name;
  img.className = 'w-full h-full object-cover';
  card.appendChild(img);

  // Async preview
  const reader = new FileReader();
  reader.onload = e => { img.src = e.target.result; };
  reader.readAsDataURL(file);

  if (idx === 0 && !existingImageUrl) {
    const badge = makeBadge('Main');
    card.appendChild(badge);
  }

  const removeBtn = makeRemoveBtn(() => {
    // Find this file's current index (may have shifted)
    const pos = selectedFiles.indexOf(file);
    if (pos !== -1) selectedFiles.splice(pos, 1);
    card.remove();
    // Re-label first new thumb as "Main" if no existing image
    relabelMainBadge(thumbRow);
    updateUI(countSpan, dropZone);
  });
  card.appendChild(removeBtn);

  thumbRow.appendChild(card);
}

// ─── UI state ────────────────────────────────────────────────────────────────

function updateUI(countSpan, dropZone) {
  const count = totalCount();
  if (countSpan) countSpan.textContent = count;

  const atLimit = count >= MAX_IMAGES;
  dropZone.style.display = atLimit ? 'none' : '';

  // Show drop-zone upload icon always (it's inside the visible zone)
  const icon = document.getElementById('upload-icon');
  if (icon) icon.style.display = '';
}

function relabelMainBadge(thumbRow) {
  // Remove all "Main" badges, re-add to first card if no existing image
  thumbRow.querySelectorAll('.main-badge').forEach(b => b.remove());
  if (existingImageUrl && !existingImageRemoved) return; // existing is main
  const cards = thumbRow.querySelectorAll('.thumb-card');
  if (cards.length > 0) {
    const badge = makeBadge('Main');
    cards[0].appendChild(badge);
  }
}

// ─── DOM helpers ─────────────────────────────────────────────────────────────

function makeCard() {
  const card = document.createElement('div');
  card.className = 'thumb-card relative rounded-lg overflow-hidden bg-slate-100 flex-shrink-0';
  card.style.cssText = 'width:80px;height:80px;';
  return card;
}

function makeBadge(text) {
  const badge = document.createElement('span');
  badge.className = 'main-badge absolute bottom-0 left-0 right-0 text-center text-white text-[10px] font-semibold py-0.5 bg-black/50';
  badge.textContent = text;
  return badge;
}

function makeRemoveBtn(onClick) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.title = 'Remove image';
  btn.className = 'absolute top-0.5 right-0.5 flex items-center justify-center rounded-full bg-black/60 hover:bg-black/80 text-white transition';
  btn.style.cssText = 'width:18px;height:18px;';
  btn.innerHTML = '<svg viewBox="0 0 20 20" fill="currentColor" style="width:10px;height:10px"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>';
  btn.addEventListener('click', onClick);
  return btn;
}

function ensureHiddenClearInput() {
  if (document.getElementById('clear-main-picture')) return;
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = 'clear_main_picture';
  input.id = 'clear-main-picture';
  input.value = '1';
  document.getElementById('hidden-inputs')?.appendChild(input);
}

// ─── Sync files to the real <input> before submit ────────────────────────────
// Browsers don't allow programmatic FileList assignment, so we use a DataTransfer.

function syncInputFiles(input) {
  if (selectedFiles.length === 0) return;
  try {
    const dt = new DataTransfer();
    selectedFiles.forEach(f => dt.items.add(f));
    input.files = dt.files;
  } catch (e) {
    // DataTransfer not supported in very old browsers; files already
    // attached via the native picker will still go through.
    console.warn('DataTransfer not supported; only natively-picked files will upload.', e);
  }
}

// ─── Backwards-compatible named export (kept so any other caller still works) ─
export function initImagePreview() {
  // No-op: initialization now happens automatically on DOMContentLoaded above.
}