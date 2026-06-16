
const btnDelete= document.querySelectorAll('.btn-borrar');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('¿Está seguro de querer borrar?')){
        e.preventDefault();
      }
    });
  })
}

document.querySelectorAll('.tema').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    document.documentElement.setAttribute('data-bs-theme', this.dataset.theme);
  });
});
