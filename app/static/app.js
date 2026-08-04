(function () {
  var storageKey = "cast-panel-theme";
  var toggle = document.querySelector("[data-theme-toggle]");
  var label = document.querySelector("[data-theme-label]");

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    if (label) {
      label.textContent = theme === "light" ? "Przełącz na ciemny" : "Przełącz na jasny";
    }
  }

  applyTheme(window.localStorage.getItem(storageKey) || "dark");

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      window.localStorage.setItem(storageKey, next);
      applyTheme(next);
    });
  }
}());
