let NavOpenBtn = document.getElementById('nav-open-btn')
let NavCloseBtn = document.getElementById('nav-close-btn')

let Nav = document.querySelector('nav')

NavOpenBtn.addEventListener('click', () => {
    Nav.style.display = 'block'
});

NavCloseBtn.addEventListener('click', () => {
    Nav.style.display = 'none'
});