(function () {
  var root = document.querySelector(".dashboard");
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

  if (!refreshMs || refreshMs < 1000) {
    refreshMs = 5000;
  }

  function setText(id, value) {
    var element = document.getElementById(id);
    if (element) {
      element.textContent = value === null || value === undefined || value === ""
        ? "-"
        : value;
    }
  }

  function yesNo(value) {
    if (value === true) {
      return "Tak";
    }
    if (value === false) {
      return "Nie";
    }
    return "-";
  }

  function formatVolume(value) {
    if (typeof value !== "number") {
      return "-";
    }
    return Math.round(value * 100) + "%";
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
      term.textContent = key.replace(/_/g, " ");
      description.textContent = media[key];
      wrapper.appendChild(term);
      wrapper.appendChild(description);
      list.appendChild(wrapper);
    });
  }

  function render(payload) {
    var status = payload.status || {};
    lastStatus = status;
    setText("device-name", status.name || "Urządzenie Cast");
    setText("model-name", status.model_name);
    setText("app-name", status.app_name);
    setText("app-id", status.app_id);
    setText("standby", yesNo(status.is_stand_by));
    setText("active-input", yesNo(status.is_active_input));
    setText("volume", formatVolume(status.volume_level));
    setText("muted", yesNo(status.volume_muted));
    setText("status-message", status.message || (status.online ? "Status odświeżony." : "Urządzenie niedostępne."));
    updateBadge(Boolean(status.online));
    renderMedia(status.media || {});
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
            message: "Nie udało się odświeżyć statusu."
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
    if (commandInFlight) {
      return;
    }
    commandInFlight = true;
    setRemoteMessage("Wysyłanie komendy...");
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
        setRemoteMessage(payload.result ? payload.result.message : "Komenda wykonana.");
        render({ ok: true, status: payload.status });
      })
      .catch(function (payload) {
        setRemoteMessage(payload && payload.message ? payload.message : "Nie udało się wykonać komendy.");
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
