document.addEventListener('DOMContentLoaded', () => {
    // 1. Password Special Toggle Configuration
    const btnUpdatePass = document.getElementById('btnUpdatePass');
    const passInitial = document.getElementById('passInitial');
    const passExpanded = document.getElementById('passExpanded');

    btnUpdatePass.addEventListener('click', () => {
        passInitial.style.display = 'none';
        passExpanded.style.display = 'block';
    });

    // 2. Inline Text Fields (Username / Position Toggle)
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const form = e.target.closest('form');
            const input = form.querySelector('input[type="text"]');
            
            if (input.hasAttribute('readonly')) {
                input.removeAttribute('readonly');
                input.classList.remove('read-only-input');
                input.classList.add('editable-input');
                input.focus();
                btn.textContent = 'SAVE';
                btn.type = 'submit';
            }
        });
    });
});