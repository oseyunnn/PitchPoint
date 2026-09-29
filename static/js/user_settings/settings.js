document.addEventListener('DOMContentLoaded', () => {
    // 1. Password Field Special Configuration Toggle
    const btnUpdatePass = document.getElementById('btnUpdatePass');
    const passInitial = document.getElementById('passInitial');
    const passExpanded = document.getElementById('passExpanded');

    if (btnUpdatePass && passInitial && passExpanded) {
        btnUpdatePass.addEventListener('click', () => {
            // Hide the single password row and reveal the 3-input change form
            passInitial.style.display = 'none';
            passExpanded.style.display = 'block';
        });
    }

    // 2. Inline Text Fields Toggle (Username & Position)
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const form = e.target.closest('form');
            if (!form) return;

            const input = form.querySelector('input[type="text"]');
            if (!input) return;

            // If input is read-only, enable editing
            if (input.hasAttribute('readonly')) {
                input.removeAttribute('readonly');
                input.classList.remove('read-only-input');
                input.classList.add('editable-input');
                input.focus();
                
                // Change button state to submit the form
                btn.textContent = 'SAVE';
                btn.type = 'submit';
            }
        });
    });
});