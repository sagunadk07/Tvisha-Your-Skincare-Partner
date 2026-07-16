const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const previewWrap = document.getElementById('preview-wrap');
const previewImg = document.getElementById('preview-img');
const removeBtn = document.getElementById('remove-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const form = document.getElementById('upload-form');

fileInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) showPreview(file);
});

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; showPreview(file); }
});

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = e => {
    previewImg.src = e.target.result;
    previewWrap.style.display = 'block';
    dropZone.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

removeBtn.addEventListener('click', () => {
  fileInput.value = '';
  previewWrap.style.display = 'none';
  dropZone.style.display = 'block';
});

form.addEventListener('submit', () => {
  analyzeBtn.disabled = true;
  analyzeBtn.querySelector('.default-state').style.display = 'none';
  analyzeBtn.querySelector('.analyzing-state').style.display = 'flex';
});
