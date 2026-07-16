// Get elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const previewImage = document.getElementById('previewImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');

let selectedFile = null;

// Click box → open file picker
uploadBox.addEventListener('click', () => fileInput.click());

// File selected via browse
fileInput.addEventListener('change', (e) => {
  handleFile(e.target.files[0]);
});

// Drag & drop support
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

// Handle the selected file
function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) return;

  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => { 
    previewImage.src = e.target.result;
    localStorage.setItem('uploadedPhoto', e.target.result);
    previewImage.hidden = false;
    uploadPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);

  analyzeBtn.disabled = false;
}

// Analyze button click
analyzeBtn.addEventListener('click', () => {
  if (!selectedFile) return;

  loadingState.hidden = false;
  analyzeBtn.disabled = true;

  // FAKE analysis for now — replace with real fetch() later
  setTimeout(() => {
    const fakeResult = {
      skin_type: "Oily",
      issues: ["Acne", "Dark Spots"],
      recommended_ingredients: ["Salicylic Acid", "Niacinamide"],
      products: [
        { name: "Clear Gel Cleanser", brand: "CeraVe" },
        { name: "Niacinamide Serum", brand: "The Ordinary" }
      ]
    };

    localStorage.setItem('skinResult', JSON.stringify(fakeResult));
    window.location.href = "/result";
  }, 1800);
});