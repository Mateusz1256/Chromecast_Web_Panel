(function () {
  var storageKey = "cast-panel-theme";
  var switchInput = document.querySelector("[data-theme-switch]");

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    if (switchInput) {
      switchInput.checked = theme === "light";
    }
  }

  applyTheme(window.localStorage.getItem(storageKey) || "dark");

  if (switchInput) {
    switchInput.addEventListener("change", function () {
      var next = switchInput.checked ? "light" : "dark";
      window.localStorage.setItem(storageKey, next);
      applyTheme(next);
    });
  }
}());
