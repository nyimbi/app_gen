// Initialize fieldsets
document.addEventListener("DOMContentLoaded", function () {
  initializeFieldsets();
  initializeJsonEditors();
  setupFilters();
});

function initializeFieldsets() {
  document.querySelectorAll(".fieldset-header").forEach((header) => {
    header.addEventListener("click", function () {
      const fieldset = this.closest(".form-fieldset");
      const content = fieldset.querySelector(".fieldset-content");
      const icon = this.querySelector(".fieldset-toggle-icon");

      content.classList.toggle("collapsed");
      icon.style.transform = content.classList.contains("collapsed")
        ? "rotate(-90deg)"
        : "";

      // Save state
      if (fieldset.id) {
        localStorage.setItem(
          `fieldset-${fieldset.id}`,
          content.classList.contains("collapsed") ? "collapsed" : "expanded",
        );
      }
    });

    // Restore saved state
    const fieldset = header.closest(".form-fieldset");
    if (fieldset.id) {
      const savedState = localStorage.getItem(`fieldset-${fieldset.id}`);
      if (savedState === "collapsed") {
        const content = fieldset.querySelector(".fieldset-content");
        content.classList.add("collapsed");
        header.querySelector(".fieldset-toggle-icon").style.transform =
          "rotate(-90deg)";
      }
    }
  });
}

function initializeJsonEditors() {
  document.querySelectorAll(".json-editor").forEach((container) => {
    const input = container.nextElementSibling;
    if (input && input.type === "hidden") {
      const editor = new JSONEditor(container, {
        mode: "tree",
        modes: ["tree", "code"],
        onChangeText: function (jsonString) {
          input.value = jsonString;
        },
      });

      try {
        const json = JSON.parse(input.value || "{}");
        editor.set(json);
      } catch (e) {
        editor.set({});
      }
    }
  });
}

function setupFilters() {
  const filterForm = document.querySelector(".filter-box form");
  if (filterForm) {
    filterForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const params = new URLSearchParams(formData);
      window.location.search = params.toString();
    });
  }
}
