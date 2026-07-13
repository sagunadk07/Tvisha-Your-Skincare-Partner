document.addEventListener('DOMContentLoaded', () => {
    const dataString = localStorage.getItem('skinResult');
  
    if (!dataString) {
      document.querySelector('.result-section .container').innerHTML =
        '<p>No analysis found. Please upload a photo first.</p><a href="/" class="hero-btn">Go to Home</a>';
      return;
    }
  
    const result = JSON.parse(dataString);
  
    document.getElementById('skinType').textContent = result.skin_type;
  
    const issuesList = document.getElementById('issuesList');
    result.issues.forEach(issue => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = issue;
      issuesList.appendChild(tag);
    });
  
    const ingredientsList = document.getElementById('ingredientsList');
    result.recommended_ingredients.forEach(ingredient => {
      const tag = document.createElement('span');
      tag.className = 'tag tag-ingredient';
      tag.textContent = ingredient;
      ingredientsList.appendChild(tag);
    });
  
    const productsList = document.getElementById('productsList');
    result.products.forEach(product => {
      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <h4>${product.name}</h4>
        <p>${product.brand}</p>
      `;
      productsList.appendChild(card);
    });
  
    const savedPhoto = localStorage.getItem('uploadedPhoto');
    const photoWrap = document.querySelector('.result-photo-wrap');
    if (savedPhoto) {
      document.getElementById('analyzedPhoto').src = savedPhoto;
    } else {
      photoWrap.style.display = 'none';
    }
  });