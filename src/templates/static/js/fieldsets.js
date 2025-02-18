document.addEventListener("DOMContentLoaded", function () {
  initializeFieldsets();
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
