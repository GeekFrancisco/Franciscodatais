// Arquivo JavaScript principal

document.addEventListener('DOMContentLoaded', function() {
    console.log('Documento carregado com sucesso!');
    
    // Adiciona a data atual no rodapé
    const footer = document.querySelector('footer p');
    const ano = new Date().getFullYear();
    if (footer) {
        footer.innerHTML = `&copy; ${ano} Projeto Web Python`;
    }
    
    // Destaca o item de menu atual
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav ul li a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = '#e8491d';
        }
    });
});