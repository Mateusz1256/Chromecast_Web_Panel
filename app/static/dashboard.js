(function () {
  var root = document.querySelector(".cast-panel");
  if (!root) {
    return;
  }

  var statusUrl = root.dataset.statusUrl;
  var csrfToken = root.dataset.csrfToken;
  var maxVolume = parseFloat(root.dataset.maxVolume || "0.5");
  var refreshMs = parseInt(root.dataset.refreshMs, 10);
  var controller = null;
  var timerId = null;
  var commandInFlight = false;
  var lastStatus = {};

  var labels = {
    pl: {
      device_fallback: "Urządzenie Cast",
      refreshed: "Status odświeżony.",
      unavailable: "Urządzenie niedostępne.",
      refresh_failed: "Nie udało się odświeżyć statusu.",
      no_standard_media: "Aktywna aplikacja nie udostępnia standardowego statusu mediów.",
      cast_not_found: "Skonfigurowane urządzenie Cast nie zostało znalezione.",
      cast_ip_missing: "Adres IP urządzenia Cast nie jest skonfigurowany.",
      unexpected_error: "Nieoczekiwany błąd statusu Cast.",
      sending: "Wysyłanie komendy...",
      command_done: "Komenda wykonana.",
      command_failed: "Nie udało się wykonać komendy.",
      yes: "Tak",
      no: "Nie",
      device_unavailable: "Niedostępne",
      standby: "Czuwanie",
      powered_on: "Włączone",
      connected: "Połączone",
      no_connection: "Brak połączenia",
      cast_on_screen: "Cast na ekranie",
      other_input: "Inne wejście",
      unknown: "Nieznane",
      media: {
        player_state: "Stan odtwarzania",
        title: "Tytuł",
        content_id: "Źródło",
        content_type: "Typ",
        duration: "Czas trwania",
        current_time: "Aktualny czas"
      }
    },
    en: {
      device_fallback: "Cast device",
      refreshed: "Status refreshed.",
      unavailable: "Device unavailable.",
      refresh_failed: "Could not refresh status.",
      no_standard_media: "Active application does not expose standard media status.",
      cast_not_found: "Configured Cast device was not found.",
      cast_ip_missing: "Cast IP is not configured.",
      unexpected_error: "Unexpected Cast status error.",
      sending: "Sending command...",
      command_done: "Command completed.",
      command_failed: "Could not run command.",
      yes: "Yes",
      no: "No",
      device_unavailable: "Unavailable",
      standby: "Standby",
      powered_on: "On",
      connected: "Connected",
      no_connection: "No connection",
      cast_on_screen: "Cast on screen",
      other_input: "Other input",
      unknown: "Unknown",
      media: {
        player_state: "Playback state",
        title: "Title",
        content_id: "Source",
        content_type: "Type",
        duration: "Duration",
        current_time: "Current time"
      }
    }
  };

  if (!refreshMs || refreshMs < 1000) {
    refreshMs = 5000;
  }

  function currentLabels() {
    var language = window.localStorage.getItem("cast-panel-language") === "en"
      ? "en"
      : "pl";
    return labels[language];
  }

  function setText(id, value) {
    var element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.textContent = value === null || value === undefined || value === ""
      ? "-"
      : value;
  }

  function yesNo(value) {
    if (value === true) {
      return currentLabels().yes;
    }
    if (value === false) {
      return currentLabels().no;
    }
    return "-";
  }

  function formatVolume(value) {
    if (typeof value !== "number") {
      return "-";
    }
    return Math.round(value * 100) + "%";
  }

  function formatSeconds(value) {
    if (typeof value !== "number") {
      return value;
    }
    var total = Math.max(0, Math.round(value));
    var minutes = Math.floor(total / 60);
    var seconds = String(total % 60).padStart(2, "0");
    return minutes + ":" + seconds;
  }

  function deviceState(status) {
    if (!status.online) {
      return currentLabels().device_unavailable;
    }
    if (status.is_stand_by === true) {
      return currentLabels().standby;
    }
    if (status.is_stand_by === false) {
      return currentLabels().powered_on;
    }
    return currentLabels().connected;
  }

  function inputState(status) {
    if (!status.online) {
      return currentLabels().no_connection;
    }
    if (status.is_active_input === true) {
      return currentLabels().cast_on_screen;
    }
    if (status.is_active_input === false) {
      return currentLabels().other_input;
    }
    return currentLabels().unknown;
  }

  function statusMessage(message) {
    var knownMessages = {
      "Active application does not expose standard media status": "no_standard_media",
      "Configured Cast device was not found": "cast_not_found",
      "Cast IP is not configured": "cast_ip_missing",
      "Unexpected Cast status error": "unexpected_error"
    };
    if (knownMessages[message]) {
      return currentLabels()[knownMessages[message]];
    }
    return message;
  }

  function updateBadge(online) {
    var badge = document.getElementById("online-badge");
    if (!badge) {
      return;
    }
    badge.className = online ? "badge online" : "badge offline";
    badge.textContent = online ? "Online" : "Offline";
  }

  function renderMedia(media) {
    var list = document.getElementById("media-status");
    var empty = document.getElementById("media-empty");
    if (!list || !empty) {
      return;
    }
    list.textContent = "";
    var keys = Object.keys(media || {});
    empty.hidden = keys.length > 0;
    keys.forEach(function (key) {
      var wrapper = document.createElement("div");
      var term = document.createElement("dt");
      var description = document.createElement("dd");
      var value = media[key];
      term.textContent = currentLabels().media[key] || key.replace(/_/g, " ");
      if (key === "duration" || key === "current_time") {
        value = formatSeconds(value);
      }
      description.textContent = value;
      wrapper.appendChild(term);
      wrapper.appendChild(description);
      list.appendChild(wrapper);
    });
  }

  function render(payload) {
    var status = payload.status || {};
    var media = status.media || {};
    lastStatus = status;
    setText("device-name", status.name || currentLabels().device_fallback);
    setText("device-name-detail", status.name);
    setText("model-name", status.model_name);
    setText("app-name", status.app_name);
    setText("app-id", status.app_id);
    setText("standby", yesNo(status.is_stand_by));
    setText("active-input", yesNo(status.is_active_input));
    setText("device-state", deviceState(status));
    setText("input-state", inputState(status));
    setText("volume", formatVolume(status.volume_level));
    setText("muted", yesNo(status.volume_muted));
    setText("player-state", media.player_state);
    setText(
      "status-message",
      status.message
        ? statusMessage(status.message)
        : (status.online ? currentLabels().refreshed : currentLabels().unavailable)
    );
    updateBadge(Boolean(status.online));
    renderMedia(media);
    updateRemoteState(status);
  }

  function updateRemoteState(status) {
    var online = Boolean(status.online);
    var hasMedia = Object.keys(status.media || {}).length > 0;
    var buttons = root.querySelectorAll("[data-remote-command]");
    buttons.forEach(function (button) {
      var command = button.dataset.remoteCommand;
      var needsMedia = command === "pause" || command === "resume" || command === "stop";
      button.disabled = commandInFlight || !online || (needsMedia && !hasMedia);
    });

    var seekButton = root.querySelector("[data-needs-media='true']");
    if (seekButton) {
      seekButton.disabled = commandInFlight || !online || !hasMedia;
    }

    var slider = document.getElementById("volume-slider");
    if (slider) {
      slider.disabled = commandInFlight || !online;
      slider.max = String(maxVolume);
      if (typeof status.volume_level === "number") {
        slider.value = String(Math.min(status.volume_level, maxVolume));
      }
    }
  }

  function setRemoteMessage(message) {
    setText("remote-message", message || "");
  }

  function scheduleNext() {
    timerId = window.setTimeout(fetchStatus, refreshMs);
  }

  function fetchStatus() {
    if (controller !== null) {
      return;
    }
    controller = new AbortController();
    window.fetch(statusUrl, {
      headers: { Accept: "application/json" },
      signal: controller.signal
    })
      .then(function (response) {
        return response.json();
      })
      .then(render)
      .catch(function () {
        render({
          ok: false,
          status: {
            online: false,
            media: {},
            message: currentLabels().refresh_failed
          }
        });
      })
      .finally(function () {
        controller = null;
        scheduleNext();
      });
  }

  function remoteUrl(command) {
    if (command === "volume") {
      return "/remote/volume";
    }
    if (command === "quit-app") {
      return "/remote/quit-app";
    }
    return "/remote/" + command;
  }

  function remoteBody(command) {
    if (command === "volume") {
      return {
        level: parseFloat(document.getElementById("volume-slider").value)
      };
    }
    if (command === "seek") {
      return {
        seconds: parseFloat(document.getElementById("seek-seconds").value)
      };
    }
    return {};
  }

  function sendRemoteCommand(command) {
    if (commandInFlight || !csrfToken) {
      return;
    }
    commandInFlight = true;
    setRemoteMessage(currentLabels().sending);
    updateRemoteState(lastStatus);
    window.fetch(remoteUrl(command), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify(remoteBody(command))
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          if (!response.ok) {
            throw payload;
          }
          return payload;
        });
      })
      .then(function (payload) {
        setRemoteMessage(payload.result ? payload.result.message : currentLabels().command_done);
        render({ ok: true, status: payload.status });
      })
      .catch(function (payload) {
        setRemoteMessage(payload && payload.message ? payload.message : currentLabels().command_failed);
        if (payload && payload.status) {
          render({ ok: false, status: payload.status });
        }
      })
      .finally(function () {
        commandInFlight = false;
        updateRemoteState(lastStatus);
      });
  }

  root.addEventListener("click", function (event) {
    var button = event.target.closest("[data-remote-command]");
    if (!button) {
      return;
    }
    sendRemoteCommand(button.dataset.remoteCommand);
  });

  var seekForm = document.getElementById("seek-form");
  if (seekForm) {
    seekForm.addEventListener("submit", function (event) {
      event.preventDefault();
      sendRemoteCommand("seek");
    });
  }

  window.addEventListener("cast-panel-language-changed", function () {
    render({ status: lastStatus });
  });

  window.addEventListener("beforeunload", function () {
    if (controller !== null) {
      controller.abort();
    }
    if (timerId !== null) {
      window.clearTimeout(timerId);
    }
  });

  fetchStatus();
}());
