document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('detailsModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const viewButtons = document.querySelectorAll('.btn-view-more');

    // Populates and displays the dark modal when clicking "VIEW MORE"
    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('modalTitle').textContent = btn.dataset.title || 'N/A';
            document.getElementById('modalDate').textContent = btn.dataset.date || 'N/A';
            document.getElementById('modalTime').textContent = btn.dataset.time || 'N/A';
            document.getElementById('modalType').textContent = btn.dataset.type || 'N/A';
            document.getElementById('modalOrg').textContent = btn.dataset.org || 'N/A';
            document.getElementById('modalEmail').textContent = btn.dataset.email || 'N/A';
            document.getElementById('modalId').textContent = btn.dataset.id || 'N/A';
            document.getElementById('modalContact').textContent = btn.dataset.contact || 'N/A';

            modal.style.display = 'flex';
        });
    });

    // Close Modal via 'X'
    closeModalBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close Modal via clicking outside content box
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});