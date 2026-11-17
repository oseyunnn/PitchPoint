document.addEventListener('DOMContentLoaded', () => {
    const tabItems = document.querySelectorAll('.settings-nav-list .tab-item');
    const panels = document.querySelectorAll('.settings-panel');

    function switchTab(targetId) {
        if (!targetId) return;

        tabItems.forEach(item => {
            if (item.dataset.target === targetId) {
                item.classList.add('is-active');
            } else {
                item.classList.remove('is-active');
            }
        });

        panels.forEach(panel => {
            if (panel.id === targetId) {
                panel.classList.add('is-active');
            } else {
                panel.classList.remove('is-active');
            }
        });
    }

    tabItems.forEach(item => {
        item.addEventListener('click', () => {
            const target = item.dataset.target;
            switchTab(target);
            window.location.hash = target;
        });
    });

    // Handle hash on page load (e.g. #tab-security)
    if (window.location.hash) {
        const hashTarget = window.location.hash.substring(1);
        const matchedTab = document.querySelector(`.settings-nav-list [data-target="${hashTarget}"]`);
        if (matchedTab) {
            switchTab(hashTarget);
        }
    }

    // Password validation on submit
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', (e) => {
            const newPass = document.getElementById('newPasswordInput')?.value;
            const confirmPass = document.getElementById('confirmPasswordInput')?.value;

            if (newPass && newPass.length < 8) {
                e.preventDefault();
                alert('New password must be at least 8 characters long.');
                return;
            }

            if (newPass !== confirmPass) {
                e.preventDefault();
                alert('New password and confirm password do not match.');
            }
        });
    }
});
