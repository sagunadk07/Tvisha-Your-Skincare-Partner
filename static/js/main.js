const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const previewImage = document.getElementById('previewImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const uploadForm = document.getElementById('uploadForm');

uploadBox.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
  handleFile(e.target.files[0]);
});

uploadBox.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadBox.classList.add('drag-over');
});

uploadBox.addEventListener('dragleave', () => {
  uploadBox.classList.remove('drag-over');
});

uploadBox.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadBox.classList.remove('drag-over');
  handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.src = e.target.result;
    previewImage.hidden = false;
    uploadPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);

  analyzeBtn.disabled = false;
}

uploadForm.addEventListener('submit', () => {
  loadingState.hidden = false;
  analyzeBtn.disabled = true;
});
