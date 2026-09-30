(function () {
  const GEO_OPTS = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 };
  const ERR = {
    1: "PERMISSION_DENIED — you declined, no coordinates available",
    2: "POSITION_UNAVAILABLE — no fix (indoors / no GPS / no network)",
    3: "TIMEOUT — no fix in time"
  };

  let ipInfo = null;
  let lastGps = null;
  let watchId = null;
  let lastErrorAt = 0;
  let lastErrorKey = "";

  const logEl = document.getElementById("netlog");

  function getSessionId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === "session") {
      return parts[1];
    }
    return "";
  }

  function setText(id, text, cls) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.className = "v" + (cls ? " " + cls : "");
  }

  function netlog(line) {
    if (!logEl) return;
    const t = new Date().toLocaleTimeString();
    logEl.textContent += "[" + t + "] " + line + "\n";
    logEl.scrollTop = logEl.scrollHeight;
  }

  function haversineM(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const p1 = lat1 * Math.PI / 180;
    const p2 = lat2 * Math.PI / 180;
    const dphi = (lat2 - lat1) * Math.PI / 180;
    const dl = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dphi / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function fmtDist(m) {
    if (m < 1000) return (m < 10 ? m.toFixed(1) : Math.round(m)) + " m";
    return (m / 1000).toFixed(1) + " km";
  }

  function accClass(m) {
    if (m <= 20) return "ok";
    if (m <= 150) return "warn";
    return "bad";
  }

  function updateAccuracySvg(acc) {
    const container = document.getElementById("gps-acc-viz");
    if (!container) return;
    if (typeof acc !== "number" || isNaN(acc) || acc < 0) {
      container.textContent = "—";
      return;
    }
    const svgNS = "http://www.w3.org/2000/svg";
    container.innerHTML = "";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "200");
    svg.setAttribute("height", "200");
    svg.setAttribute("viewBox", "0 0 200 200");
    svg.style.display = "block";
    svg.style.background = "#080c12";
    svg.style.border = "1px solid var(--border)";
    svg.style.borderRadius = "4px";
    svg.style.marginTop = "4px";

    const cx = 100;
    const cy = 100;
    const maxR = 85;
    const clampedAcc = Math.min(acc, 500);
    const r = Math.max(4, (clampedAcc / 500) * maxR);

    const refCircle = document.createElementNS(svgNS, "circle");
    refCircle.setAttribute("cx", cx);
    refCircle.setAttribute("cy", cy);
    refCircle.setAttribute("r", maxR);
    refCircle.setAttribute("fill", "none");
    refCircle.setAttribute("stroke", "#1e2b3a");
    refCircle.setAttribute("stroke-dasharray", "3 3");
    refCircle.setAttribute("stroke-width", "1");
    svg.appendChild(refCircle);

    const circle = document.createElementNS(svgNS, "circle");
    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", r);
    circle.setAttribute("fill", "rgba(79, 214, 255, 0.15)");
    circle.setAttribute("stroke", "#4fd6ff");
    circle.setAttribute("stroke-width", "2");
    svg.appendChild(circle);

    const centerDot = document.createElementNS(svgNS, "circle");
    centerDot.setAttribute("cx", cx);
    centerDot.setAttribute("cy", cy);
    centerDot.setAttribute("r", "3");
    centerDot.setAttribute("fill", "#00ff9c");
    svg.appendChild(centerDot);

    const label = document.createElementNS(svgNS, "text");
    label.setAttribute("x", cx);
    label.setAttribute("y", "190");
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "#4fd6ff");
    label.setAttribute("font-family", "monospace");
    label.setAttribute("font-size", "12");
    label.textContent = "±" + Math.round(acc) + " m";
    svg.appendChild(label);

    container.appendChild(svg);
  }

  function updateWorldView(lat, lon) {
    const x = (lon + 180) / 360 * 360;
    const y = (90 - lat) / 180 * 180;
    const marker = document.getElementById("worldMarker");
    const label = document.getElementById("worldLabel");
    if (marker) {
      marker.setAttribute("cx", x);
      marker.setAttribute("cy", y);
    }
    if (label) {
      label.setAttribute("x", x + 4);
      label.setAttribute("y", y - 3);
      label.textContent = lat.toFixed(2) + ", " + lon.toFixed(2);
    }
  }

  function enableMapLink(el, host) {
    if (!el) return;
    el.removeAttribute("aria-disabled");
    el.classList.add("active");
    el.onclick = function () {
      netlog("→ leaving page: " + host + " (coordinates sent to that site by your browser)");
    };
  }

  function updateMapLinks(lat, lon) {
    const latS = lat.toFixed(6);
    const lonS = lon.toFixed(6);

    const osm = document.getElementById("link-osm");
    const gmaps = document.getElementById("link-gmaps");
    const gsat = document.getElementById("link-gsat");

    if (osm) {
      osm.href = "https://www.openstreetmap.org/?mlat=" + latS + "&mlon=" + lonS + "#map=15/" + latS + "/" + lonS;
      enableMapLink(osm, "www.openstreetmap.org");
    }
    if (gmaps) {
      gmaps.href = "https://www.google.com/maps?q=" + latS + "," + lonS;
      enableMapLink(gmaps, "www.google.com");
    }
    if (gsat) {
      gsat.href = "https://www.google.com/maps/@" + latS + "," + lonS + ",15z/data=!3m1!1e3";
      enableMapLink(gsat, "www.google.com");
    }
  }

  function showVerdict() {
    if (!ipInfo || lastGps == null) return;
    if (typeof ipInfo.lat !== "number" || typeof ipInfo.lon !== "number") return;
    const d = haversineM(ipInfo.lat, ipInfo.lon, lastGps.lat, lastGps.lon);
    const el = document.getElementById("verdict");
    if (!el) return;
    el.style.display = "block";
    el.textContent = "IP geolocation was off by " + fmtDist(d) +
      " from the actual GPS fix. A link alone gave an approximation; precise coordinates only appeared after the permission prompt was accepted.";
  }

  function collectBrowserInfo() {
    return {
      userAgent: navigator.userAgent || "Unknown",
      platform: navigator.platform || "Unknown",
      screenResolution: (window.screen ? screen.width + "x" + screen.height : "Unknown"),
      devicePixelRatio: (window.devicePixelRatio || 1).toString(),
      hardwareConcurrency: (navigator.hardwareConcurrency || "Unknown").toString(),
      language: navigator.language || "Unknown",
      timezone: (Intl && Intl.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : "Unknown"),
      timezoneOffset: new Date().getTimezoneOffset().toString(),
      viewportSize: window.innerWidth + "x" + window.innerHeight,
      colorDepth: (window.screen ? screen.colorDepth + "bpp" : "Unknown"),
      touchSupport: (('ontouchstart' in window || navigator.maxTouchPoints > 0) ? "Supported" : "None"),
      onlineStatus: (navigator.onLine ? "Online" : "Offline")
    };
  }

  function renderBrowserInfo(info) {
    setText("b-ua", info.userAgent);
    setText("b-platform", info.platform);
    setText("b-screen", info.screenResolution);
    setText("b-dpr", info.devicePixelRatio);
    setText("b-cpu", info.hardwareConcurrency);
    setText("b-lang", info.language);
    setText("b-tz", info.timezone);
  }

  function fillIp(data) {
    ipInfo = data;
    setText("ip-status", "IP-based estimate only", "warn");
    setText("ip-addr", data.ip || "—");
    const place = [data.city, data.region, data.country].filter(Boolean).join(", ") || "—";
    setText("ip-place", place);
    if (typeof data.lat === "number" && typeof data.lon === "number") {
      setText("ip-ll", data.lat.toFixed(3) + ", " + data.lon.toFixed(3));
    } else {
      setText("ip-ll", "—");
    }
    setText("ip-isp", data.isp || "—");
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
    setText("ip-status", "looking up…");
    try {
      netlog("GET https://ipwho.is/");
      const r = await fetch("https://ipwho.is/");
      if (!r.ok) throw new Error("ipwho.is HTTP " + r.status);
      const j = await r.json();
      if (j && j.success === false) throw new Error("ipwho.is unsuccessful");
      netlog("ipwho.is responded");
      fillIp(parseWho(j));
      return;
    } catch (err) {
      netlog("ipwho.is failed (" + err + "); GET https://ipapi.co/json/");
    }
    try {
      const r = await fetch("https://ipapi.co/json/");
      if (!r.ok) throw new Error("ipapi.co HTTP " + r.status);
      const j = await r.json();
      netlog("ipapi.co responded");
      fillIp(parseApi(j));
    } catch (err) {
      netlog("IP lookup error: " + err);
      setText("ip-status", "lookup failed", "bad");
    }
  }

  function applyFix(pos) {
    const c = pos.coords;
    const lat = c.latitude;
    const lon = c.longitude;
    const acc = c.accuracy;
    const alt = c.altitude;
    lastGps = { lat: lat, lon: lon, accuracy: acc, altitude: alt };
    lastErrorAt = 0;
    lastErrorKey = "";

    setText("gps-status", "fix received", "ok");
    setText("gps-lat", lat.toFixed(6));
    setText("gps-lon", lon.toFixed(6));
    if (typeof acc === "number") {
      setText("gps-acc", "±" + Math.round(acc) + " m", accClass(acc));
      updateAccuracySvg(acc);
    } else {
      setText("gps-acc", "n/a");
      updateAccuracySvg(null);
    }
    updateWorldView(lat, lon);
    updateMapLinks(lat, lon);

    setText("gps-alt", typeof alt === "number" ? Math.round(alt) + " m" : "n/a");
    setText("gps-at", new Date().toLocaleString());
    showVerdict();

    const gps = { lat: lat, lon: lon, accuracy: acc, altitude: alt };
    const bInfo = collectBrowserInfo();
    const sid = getSessionId();
    const dest = sid ? ("/api/session/" + sid + "/location") : "/report";
    netlog("POST " + dest);

    fetch(dest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ip: ipInfo, gps: gps, browser: bInfo })
    }).catch(function (err) {
      netlog("POST " + dest + " error: " + err);
    });
  }

  function geoError(err) {
    const msg = ERR[err.code] || ("geolocation error " + err.code);
    setText("gps-status", msg, "bad");
    const key = String(err.code);
    const now = Date.now();
    if (key === lastErrorKey && (now - lastErrorAt) < 30000) {
      return;
    }
    lastErrorAt = now;
    lastErrorKey = key;
    netlog(msg);
  }

  function requestOnce() {
    if (!navigator.geolocation) {
      setText("gps-status", "geolocation API not available", "bad");
      return;
    }
    setText("gps-status", "requesting permission…", "warn");
    navigator.geolocation.getCurrentPosition(applyFix, geoError, GEO_OPTS);
  }

  function startWatch() {
    if (!navigator.geolocation) {
      setText("gps-status", "geolocation API not available", "bad");
      return;
    }
    if (watchId !== null) return;
    setText("gps-status", "watch started — waiting for fix…", "warn");
    watchId = navigator.geolocation.watchPosition(applyFix, geoError, GEO_OPTS);
    const btnWatch = document.getElementById("btn-watch");
    const btnStop = document.getElementById("btn-stop");
    if (btnWatch) btnWatch.disabled = true;
    if (btnStop) btnStop.disabled = false;
  }

  function stopWatch() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
    const btnWatch = document.getElementById("btn-watch");
    const btnStop = document.getElementById("btn-stop");
    if (btnWatch) btnWatch.disabled = false;
    if (btnStop) btnStop.disabled = true;
    setText("gps-status", "watch stopped");
  }

  function initApp() {
    const bInfo = collectBrowserInfo();
    renderBrowserInfo(bInfo);
    lookupIp();

    const sid = getSessionId();
    const tagEl = document.getElementById("session-tag-display");
    if (tagEl) {
      tagEl.textContent = sid ? ("SESSION " + sid) : "SESSION: LOCAL LAB";
    }
    const dashLink = document.getElementById("btn-dashboard-link");
    if (dashLink && sid) {
      dashLink.href = "/dashboard/" + sid;
    }

    const btnPerm = document.getElementById("btn-perm");
    const btnOnce = document.getElementById("btn-once");
    const btnWatch = document.getElementById("btn-watch");
    const btnStop = document.getElementById("btn-stop");

    if (btnPerm) {
      btnPerm.onclick = function () {
        if (btnOnce) btnOnce.disabled = false;
        if (btnWatch) btnWatch.disabled = false;
        requestOnce();
      };
    }
    if (btnOnce) btnOnce.onclick = requestOnce;
    if (btnWatch) btnWatch.onclick = startWatch;
    if (btnStop) btnStop.onclick = stopWatch;
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("ip-status")) {
      initApp();
    }
  });
})();
