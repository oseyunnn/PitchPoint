document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('pitchModal');
    const openBtn = document.getElementById('openModalBtn');
    const closeBtn = document.getElementById('closeModalBtn');

    // Open Modal
    openBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    // Close Modal via 'X'
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close Modal via clicking outside the container
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});