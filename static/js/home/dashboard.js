document.addEventListener("DOMContentLoaded", () => {
    const detailModal = document.getElementById("pitchDetailModal");
    const newPitchModal = document.getElementById("newPitchModal");
    const closeButtons = [
        document.getElementById("closePitchModal"),
        document.getElementById("closeNewPitchModal"),
    ];
    let activeModal = null;

    function openModal(modal) {
        if (!modal) return;
        activeModal = modal;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        modal.querySelector(".modal-close")?.focus();
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        activeModal = null;
    }

    document.getElementById("openPitchModal")?.addEventListener("click", () => openModal(newPitchModal));
    document.getElementById("closePitchModal")?.addEventListener("click", () => closeModal(detailModal));
    document.getElementById("closeNewPitchModal")?.addEventListener("click", () => closeModal(newPitchModal));

    document.querySelectorAll(".view-details-btn").forEach((button) => {
        button.addEventListener("click", () => {
            document.getElementById("modalPitchTitle").textContent = button.dataset.title || "Pitch details";
            document.getElementById("modalPitchType").textContent = button.dataset.type || "Not specified";
            document.getElementById("modalPitchDate").textContent = button.dataset.date || "Not specified";
            document.getElementById("modalPitchTime").textContent = button.dataset.time || "Not specified";
            document.getElementById("modalPitchLocation").textContent = button.dataset.location || "Location to be announced";
            document.getElementById("modalPitchDetails").textContent = button.dataset.details || "No additional information provided.";
            document.getElementById("modalPitchId").value = button.dataset.id || "";

            const pdfLink = document.getElementById("modalPitchPdf");
            const pdfUrl = button.dataset.pdf;
            if (pdfUrl) {
                try {
                    const parsedUrl = new URL(pdfUrl, window.location.origin);
                    if (["http:", "https:"].includes(parsedUrl.protocol)) {
                        pdfLink.href = parsedUrl.href;
                        pdfLink.hidden = false;
                    } else {
                        pdfLink.hidden = true;
                    }
                } catch {
                    pdfLink.hidden = true;
                }
            } else {
                pdfLink.hidden = true;
            }
            openModal(detailModal);
        });
    });

    closeButtons.forEach((button) => {
        button?.addEventListener("click", () => closeModal(button.closest(".pitch-modal")));
    });

    document.querySelectorAll(".pitch-modal").forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeModal(modal);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && activeModal) closeModal(activeModal);
    });
});