document.addEventListener("DOMContentLoaded", function () {
    // 1. Add Pitch Modal Logic
    const pitchModal = document.getElementById("pitchModal");
    const openModalBtn = document.getElementById("openModalBtn");
    const closeModalBtn = document.getElementById("closeModalBtn");

    if (openModalBtn && pitchModal) {
        openModalBtn.addEventListener("click", function () {
            pitchModal.style.display = "flex";
        });
    }

    if (closeModalBtn && pitchModal) {
        closeModalBtn.addEventListener("click", function () {
            pitchModal.style.display = "none";
        });
    }

    // 2. View Details & Volunteer Modal Logic
    const viewModal = document.getElementById("viewPitchModal");
    const closeViewModalBtn = document.getElementById("closeViewModalBtn");
    const viewBtns = document.querySelectorAll(".view-details-btn");

    viewBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            // Extract data attributes from button
            const pitchId = this.getAttribute("data-id");
            const pitchTitle = this.getAttribute("data-title");
            const pitchType = this.getAttribute("data-type");
            const pitchDate = this.getAttribute("data-date");
            const pitchTime = this.getAttribute("data-time");
            const pitchDetails = this.getAttribute("data-details");
            const pdfUrl = this.getAttribute("data-pdf");

            // Populate Modal Content
            document.getElementById("modalPitchId").value = pitchId;
            document.getElementById("modalPitchTitle").textContent = pitchTitle.toUpperCase();
            document.getElementById("modalPitchType").textContent = pitchType.toUpperCase();
            document.getElementById("modalPitchSchedule").textContent = `${pitchDate} | ${pitchTime}`;
            document.getElementById("modalPitchDetails").textContent = pitchDetails;

            const pdfContainer = document.getElementById("modalPdfContainer");
            if (pdfUrl && pdfUrl.trim() !== "") {
                pdfContainer.innerHTML = `<a href="${pdfUrl}" target="_blank" style="color: #4da6ff; text-decoration: underline; font-size: 12px;">📄 View Attached PDF Letter</a>`;
            } else {
                pdfContainer.innerHTML = `<span style="font-size: 11px; color: #888;">No PDF Letter Attached</span>`;
            }

            // Display Modal
            viewModal.style.display = "flex";
        });
    });

    if (closeViewModalBtn && viewModal) {
        closeViewModalBtn.addEventListener("click", function () {
            viewModal.style.display = "none";
        });
    }

    // 3. Close Modals on Overlay Click
    window.addEventListener("click", function (event) {
        if (event.target === pitchModal) {
            pitchModal.style.display = "none";
        }
        if (event.target === viewModal) {
            viewModal.style.display = "none";
        }
    });
});