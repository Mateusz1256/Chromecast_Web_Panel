(function () {
  var root = document.querySelector(".dashboard");
  if (!root) {
    return;
  }

  var statusUrl = root.dataset.statusUrl;
  var refreshMs = parseInt(root.dataset.refreshMs, 10);
  var controller = null;
  var timerId = null;

  if (!refreshMs || refreshMs < 1000) {
    refreshMs = 5000;
  }

  function setText(id, value) {
    var element = document.getElementById(id);
    if (element) {
      element.textContent = value === null || value === undefined || value === "" ? "-" : value;
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
