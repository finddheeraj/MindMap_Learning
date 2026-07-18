/**
 * Learning Hub - main.js
 * Phase 1: landing page interactions (delete confirmation modal,
 * live search debounce).
 */

document.addEventListener("DOMContentLoaded", () => {
    initDeleteConfirmation();
    initLiveSearch();
});

/**
 * Wires up the "Delete" buttons on the topics table to populate
 * and show the shared confirmation modal instead of deleting
 * immediately.
 */
function initDeleteConfirmation() {
    const deleteModalEl = document.getElementById("deleteModal");
    if (!deleteModalEl) return;

    const deleteModal = new bootstrap.Modal(deleteModalEl);
    const deleteForm = document.getElementById("deleteForm");
    const deleteTopicName = document.getElementById("deleteTopicName");

    document.querySelectorAll(".btn-delete-topic").forEach((btn) => {
        btn.addEventListener("click", () => {
            const topicName = btn.getAttribute("data-topic-name");
            const deleteUrl = btn.getAttribute("data-delete-url");

            deleteTopicName.textContent = topicName;
            deleteForm.setAttribute("action", deleteUrl);
            deleteModal.show();
        });
    });
}

/**
 * Auto-submits the search form shortly after the user stops typing,
 * so results update without needing to press Enter.
 */
function initLiveSearch() {
    const searchInput = document.getElementById("searchInput");
    if (!searchInput) return;

    let debounceTimer;
    searchInput.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchInput.closest("form").submit();
        }, 450);
    });
}
