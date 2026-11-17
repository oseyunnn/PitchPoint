document.addEventListener("DOMContentLoaded", () => {
    const detailModal = document.getElementById("pitchDetailModal");
    const newPitchModal = document.getElementById("newPitchModal");

    let activeModal = null;
    let returnFocus = null;
    let previousBodyOverflow = "";

    function openModal(modal, trigger) {
        if (!modal) return;
        activeModal = modal;
        returnFocus = trigger;
        previousBodyOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        modal.querySelector(".modal-close")?.focus();
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        if (activeModal === modal) {
            activeModal = null;
            document.body.style.overflow = previousBodyOverflow;
            returnFocus?.focus();
            returnFocus = null;
        }
    }

    // Modal open triggers
    document.getElementById("openPitchModal")?.addEventListener("click", (e) => openModal(newPitchModal, e.currentTarget));
    document.getElementById("openPitchModalRail")?.addEventListener("click", (e) => openModal(newPitchModal, e.currentTarget));
    document.getElementById("openPitchModalHeader")?.addEventListener("click", (e) => {
        if (newPitchModal) openModal(newPitchModal, e.currentTarget);
    });

    // Close buttons
    document.getElementById("closePitchModal")?.addEventListener("click", () => closeModal(detailModal));
    document.getElementById("closeNewPitchModal")?.addEventListener("click", () => closeModal(newPitchModal));

    // Handle view details click
    document.querySelectorAll(".view-details-btn").forEach((button) => {
        button.addEventListener("click", () => {
            const titleEl = document.getElementById("modalPitchTitle");
            if (titleEl) titleEl.textContent = button.dataset.title || "Pitch Details";

            const typeEl = document.getElementById("modalPitchType");
            if (typeEl) typeEl.textContent = button.dataset.type || "Coverage";

            const dateEl = document.getElementById("modalPitchDate");
            if (dateEl) dateEl.textContent = button.dataset.date || "Scheduled";

            const timeEl = document.getElementById("modalPitchTime");
            if (timeEl) timeEl.textContent = button.dataset.time || "TBA";

            const locEl = document.getElementById("modalPitchLocation");
            if (locEl) locEl.textContent = button.dataset.location || "Location to be announced";

            const detailsEl = document.getElementById("modalPitchDetails");
            if (detailsEl) detailsEl.textContent = button.dataset.details || "No additional briefing provided.";

            const idInput = document.getElementById("modalPitchId");
            if (idInput) idInput.value = button.dataset.id || "";

            // Status changer if user is pitch owner
            const statusSection = document.getElementById("modalStatusUpdateSection");
            const statusPitchId = document.getElementById("modalStatusPitchId");
            const statusSelect = document.getElementById("modalStatusSelect");

            if (statusSection && statusPitchId) {
                if (button.dataset.isOwner === "true") {
                    statusSection.style.display = "block";
                    statusPitchId.value = button.dataset.id || "";
                    if (statusSelect && button.dataset.status) {
                        statusSelect.value = button.dataset.status;
                    }
                } else {
                    statusSection.style.display = "none";
                }
            }

            // PDF letter URL
            const pdfLink = document.getElementById("modalPitchPdf");
            const pdfUrl = button.dataset.pdf;
            if (pdfLink) {
                if (pdfUrl && pdfUrl.trim() !== "") {
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
            }

            openModal(detailModal, button);
        });
    });

    // Quick volunteer button triggers
    document.querySelectorAll(".quick-volunteer-btn, .trigger-volunteer-modal").forEach((button) => {
        button.addEventListener("click", () => {
            const pitchId = button.dataset.pitchId;
            const pitchTitle = button.dataset.title;

            const idInput = document.getElementById("modalPitchId");
            if (idInput) idInput.value = pitchId || "";

            const titleEl = document.getElementById("modalPitchTitle");
            if (titleEl && pitchTitle) titleEl.textContent = pitchTitle;

            openModal(detailModal, button);
        });
    });

    // Backdrop click to close
    document.querySelectorAll(".pitch-modal").forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeModal(modal);
        });
    });

    // Escape key to close
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && activeModal) closeModal(activeModal);
    });

    // Submissions details accordion styling
    document.querySelectorAll(".work-submission-details").forEach((details) => {
        details.addEventListener("toggle", () => {
            details.closest(".deliverable-card")?.classList.toggle("has-open-submission", details.open);
        });
    });

    // Role checkbox toggle in pitch submission modal
    document.querySelectorAll("[data-role-toggle]").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const slotsInput = checkbox.closest(".role-need-option")?.querySelector('input[type="number"]');
            if (slotsInput) {
                slotsInput.disabled = !checkbox.checked;
                if (checkbox.checked && !slotsInput.value) {
                    slotsInput.value = "1";
                }
            }
        });
    });

    // Workspace Filter Tabs on Dashboard
    const filterTabs = document.querySelectorAll(".workspace-filter-tabs .tab-btn");
    const deliverableCards = document.querySelectorAll(".deliverables-grid .deliverable-card");

    filterTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            filterTabs.forEach((t) => t.classList.remove("is-active"));
            tab.classList.add("is-active");

            const filter = tab.dataset.filter; // "all", "assigned", "created", "review"

            deliverableCards.forEach((card) => {
                const category = card.dataset.category || "";
                if (filter === "all" || category.includes(filter)) {
                    card.style.display = "flex";
                } else {
                    card.style.display = "none";
                }
            });
        });
    });

    // Check URL hash for modal opening or scrolling
    if (window.location.hash === "#submit-pitch" && newPitchModal) {
        openModal(newPitchModal, null);
    }
});
