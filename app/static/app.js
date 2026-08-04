(function () {
  var themeKey = "cast-panel-theme";
  var languageKey = "cast-panel-language";
  var switchInput = document.querySelector("[data-theme-switch]");
  var languageSelect = document.querySelector("[data-language-select]");
  var fileInput = document.querySelector(".file-input");
  var fileName = document.querySelector("[data-file-name]");

  var translations = {
    pl: {
      "app.title": "Panel Cast",
      "nav.status": "Status",
      "nav.remote": "Pilot",
      "nav.media": "Media",
      "nav.settings": "Ustawienia",
      "nav.audit": "Dziennik",
      "nav.logout": "Wyloguj",
      "settings.interface.eyebrow": "Interfejs",
      "settings.interface.title": "Preferencje interfejsu",
      "settings.theme.title": "Motyw",
      "settings.theme.help": "Przełącz wygląd panelu na jasny albo ciemny.",
      "settings.theme.dark": "Ciemny",
      "settings.theme.light": "Jasny",
      "settings.language.title": "Język",
      "settings.language.help": "Wybierz język interfejsu.",
      "settings.language.label": "Język interfejsu",
      "settings.app.title": "Ustawienia",
      "media.library.eyebrow": "Biblioteka",
      "media.library.title": "Media",
      "media.stop_playback": "Zatrzymaj odtwarzanie",
      "media.upload.file": "Plik multimedialny",
      "media.upload.choose": "Wybierz plik",
      "media.upload.no_file": "Nie wybrano pliku",
      "media.upload.submit": "Prześlij",
      "media.upload.help": "Audio i wideo nie są transkodowane. Zalecany format wideo to MP4 H.264 + AAC.",
      "media.tasks.eyebrow": "Zadania",
      "media.tasks.title": "Pokaz slajdów i kolejka",
      "media.tasks.stop": "Zatrzymaj zadanie",
      "media.tasks.slide_seconds": "Czas slajdu",
      "media.tasks.start_slideshow": "Start pokazu",
      "media.tasks.start_queue": "Start kolejki",
      "media.presets.eyebrow": "Presety",
      "media.presets.title": "Scenariusze",
      "media.presets.run": "Uruchom",
      "media.presets.save": "Zapisz preset",
      "media.presets.name_placeholder": "Nazwa presetu",
      "media.presets.stop_after": "Stop po s",
      "media.presets.empty": "Brak presetów.",
      "media.queue": "Kolejka",
      "media.display": "Wyświetl",
      "media.play": "Odtwórz",
      "media.empty": "Brak mediów w bibliotece.",
      "status.eyebrow": "Status",
      "status.title": "Urządzenie Cast",
      "status.receiver": "Odbiornik",
      "status.state": "Stan",
      "status.input": "Wejście",
      "status.volume": "Głośność",
      "status.details.eyebrow": "Szczegóły",
      "status.details.title": "Połączenie i aplikacja",
      "status.name": "Nazwa",
      "status.model": "Model",
      "status.app": "Aplikacja",
      "status.app_id": "Identyfikator aplikacji",
      "status.standby": "Czuwanie",
      "status.active_input": "Aktywne wejście",
      "status.muted": "Wyciszenie",
      "status.media.eyebrow": "Treść",
      "status.media.title": "Aktualnie wyświetlane media",
      "status.media.empty": "Brak standardowego statusu mediów dla aktywnej aplikacji.",
      "remote.eyebrow": "Pilot",
      "remote.title": "Sterowanie odtwarzaniem",
      "remote.set": "Ustaw",
      "remote.mute": "Wycisz",
      "remote.unmute": "Włącz dźwięk",
      "remote.quit_app": "Zamknij aplikację Cast",
      "remote.seek": "Przejdź do sekundy",
      "remote.seek_submit": "Przejdź",
      "remote.preview": "Podgląd",
      "remote.receiver_state": "Stan odbiornika",
      "remote.device_state": "Stan urządzenia",
      "remote.playback": "Odtwarzanie",
      "remote.power_note": "PyChromecast nie udostępnia stabilnego polecenia fizycznego włączenia lub wyłączenia TV. Przycisk zamyka aktywną aplikację Cast, jeśli odbiornik to obsługuje.",
      "audit.eyebrow": "Dziennik",
      "audit.title": "Logi techniczne",
      "audit.help": "Dziennik zawiera operacje techniczne panelu i wyniki komend. Nie zapisuje tytułów odtwarzanych treści ani pełnych URL-i mediów.",
      "audit.errors": "Ostatnie błędy",
      "audit.no_errors": "Brak błędów w ostatnich wpisach.",
      "audit.entries": "Ostatnie operacje",
      "audit.no_entries": "Brak wpisów dziennika.",
      "common.delete": "Usuń"
    },
    en: {
      "app.title": "Cast Panel",
      "nav.status": "Status",
      "nav.remote": "Remote",
      "nav.media": "Media",
      "nav.settings": "Settings",
      "nav.audit": "Log",
      "nav.logout": "Log out",
      "settings.interface.eyebrow": "Interface",
      "settings.interface.title": "Interface preferences",
      "settings.theme.title": "Theme",
      "settings.theme.help": "Switch the panel between light and dark mode.",
      "settings.theme.dark": "Dark",
      "settings.theme.light": "Light",
      "settings.language.title": "Language",
      "settings.language.help": "Choose the interface language.",
      "settings.language.label": "Interface language",
      "settings.app.title": "Settings",
      "media.library.eyebrow": "Library",
      "media.library.title": "Media",
      "media.stop_playback": "Stop playback",
      "media.upload.file": "Media file",
      "media.upload.choose": "Choose file",
      "media.upload.no_file": "No file selected",
      "media.upload.submit": "Upload",
      "media.upload.help": "Audio and video are not transcoded. Recommended video format is MP4 H.264 + AAC.",
      "media.tasks.eyebrow": "Jobs",
      "media.tasks.title": "Slideshow and queue",
      "media.tasks.stop": "Stop job",
      "media.tasks.slide_seconds": "Slide duration",
      "media.tasks.start_slideshow": "Start slideshow",
      "media.tasks.start_queue": "Start queue",
      "media.presets.eyebrow": "Presets",
      "media.presets.title": "Scenarios",
      "media.presets.run": "Run",
      "media.presets.save": "Save preset",
      "media.presets.name_placeholder": "Preset name",
      "media.presets.stop_after": "Stop after s",
      "media.presets.empty": "No presets.",
      "media.queue": "Queue",
      "media.display": "Display",
      "media.play": "Play",
      "media.empty": "No media in the library.",
      "status.eyebrow": "Status",
      "status.title": "Cast device",
      "status.receiver": "Receiver",
      "status.state": "State",
      "status.input": "Input",
      "status.volume": "Volume",
      "status.details.eyebrow": "Details",
      "status.details.title": "Connection and app",
      "status.name": "Name",
      "status.model": "Model",
      "status.app": "App",
      "status.app_id": "App ID",
      "status.standby": "Standby",
      "status.active_input": "Active input",
      "status.muted": "Muted",
      "status.media.eyebrow": "Content",
      "status.media.title": "Currently displayed media",
      "status.media.empty": "No standard media status for the active app.",
      "remote.eyebrow": "Remote",
      "remote.title": "Playback control",
      "remote.set": "Set",
      "remote.mute": "Mute",
      "remote.unmute": "Unmute",
      "remote.quit_app": "Close Cast app",
      "remote.seek": "Go to second",
      "remote.seek_submit": "Go",
      "remote.preview": "Preview",
      "remote.receiver_state": "Receiver state",
      "remote.device_state": "Device state",
      "remote.playback": "Playback",
      "remote.power_note": "PyChromecast does not expose a stable physical TV power on/off command. This button closes the active Cast app when the receiver supports it.",
      "audit.eyebrow": "Log",
      "audit.title": "Technical logs",
      "audit.help": "The log contains technical panel operations and command results. It does not store watched titles or full media URLs.",
      "audit.errors": "Recent errors",
      "audit.no_errors": "No errors in recent entries.",
      "audit.entries": "Recent operations",
      "audit.no_entries": "No log entries.",
      "common.delete": "Delete"
    }
  };

  function currentLanguage() {
    var saved = window.localStorage.getItem(languageKey);
    return saved === "en" ? "en" : "pl";
  }

  function translate(key) {
    var language = currentLanguage();
    return translations[language][key] || translations.pl[key] || key;
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    if (switchInput) {
      switchInput.checked = theme === "light";
    }
  }

  function applyLanguage(language) {
    var selectedLanguage = language === "en" ? "en" : "pl";
    document.documentElement.lang = selectedLanguage;
    window.localStorage.setItem(languageKey, selectedLanguage);
    if (languageSelect) {
      languageSelect.value = selectedLanguage;
    }
    document.querySelectorAll("[data-i18n]").forEach(function (element) {
      element.textContent = translate(element.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (element) {
      element.placeholder = translate(element.dataset.i18nPlaceholder);
    });
    updateFileName();
  }

  function updateFileName() {
    if (!fileName) {
      return;
    }
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      fileName.textContent = translate("media.upload.no_file");
      fileName.title = fileName.textContent;
      return;
    }
    fileName.textContent = fileInput.files[0].name;
    fileName.title = fileInput.files[0].name;
  }

  applyTheme(window.localStorage.getItem(themeKey) || "dark");
  applyLanguage(currentLanguage());

  if (switchInput) {
    switchInput.addEventListener("change", function () {
      var next = switchInput.checked ? "light" : "dark";
      window.localStorage.setItem(themeKey, next);
      applyTheme(next);
    });
  }

  if (languageSelect) {
    languageSelect.addEventListener("change", function () {
      applyLanguage(languageSelect.value);
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", updateFileName);
  }
}());
