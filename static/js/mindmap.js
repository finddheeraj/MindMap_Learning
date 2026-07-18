/**
 * Learning Hub - mindmap.js
 * Phase 2: initializes the Mind Elixir canvas for a topic, and
 * autosaves the full tree to the server after every edit.
 */

import MindElixir from "../vendor/mind-elixir/MindElixir.js";

const AUTOSAVE_DEBOUNCE_MS = 700;

document.addEventListener("DOMContentLoaded", () => {
    const config = window.LEARNING_HUB_MINDMAP_CONFIG;
    const initialTree = JSON.parse(document.getElementById("initial-tree-data").textContent);

    const mind = new MindElixir({
        el: "#map",
        direction: 2, // 0 = left, 1 = right, 2 = both sides
        draggable: true,
        contextMenu: true,
        toolBar: true,
        keypress: true,
        editable: true,
        newTopicName: "New Node",
        alignment: "root",
    });

    mind.init({ nodeData: initialTree });
    mind.toCenter();

    window.addEventListener("resize", () => {
        mind.toCenter();
    });

    const statusEl = document.getElementById("saveStatus");
    let debounceTimer = null;
    let inFlightController = null;

    function setStatus(state) {
        statusEl.classList.remove("saving", "saved", "error");
        if (state === "saving") {
            statusEl.classList.add("saving");
            statusEl.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span>Saving...</span>
            `;
        } else if (state === "error") {
            statusEl.classList.add("error");
            statusEl.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i><span>Save failed - retrying</span>`;
        } else {
            statusEl.classList.add("saved");
            statusEl.innerHTML = `<i class="bi bi-check-circle-fill"></i><span>All changes saved</span>`;
        }
    }

    async function saveTree() {
        setStatus("saving");

        if (inFlightController) {
            inFlightController.abort();
        }
        inFlightController = new AbortController();

        const data = mind.getData();

        try {
            const response = await fetch(config.saveUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nodeData: data.nodeData }),
                signal: inFlightController.signal,
            });

            if (!response.ok) {
                throw new Error(`Save failed with status ${response.status}`);
            }

            setStatus("saved");
        } catch (err) {
            if (err.name !== "AbortError") {
                console.error("Autosave error:", err);
                setStatus("error");
            }
        }
    }

    function scheduleSave() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(saveTree, AUTOSAVE_DEBOUNCE_MS);
    }

    // Every structural or text change (add child, add sibling, remove node,
    // rename, drag/move) fires an "operation" event - autosave on all of them.
    mind.bus.addListener("operation", () => {
        scheduleSave();
    });
});
