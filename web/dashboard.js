/**
 * LOCLX Security Dashboard JavaScript v2.4.8
 */
(function () {
  const state = {
    sid: null,
    session: null,
    gps: null,
    ip: null,
    history: [],
    map: null,
    gpsMarker: null,
    ipMarker: null,
    trail: null,
    pollTimer: null,
    isPolling: false,
    lastGpsCoords: null,
    lastIpCoords: null
  };

  function getSessionId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === "dashboard" && parts[1] !== "dashboard.html") {
      return parts[1];
    }
    const params = new URLSearchParams(window.location.search);
    if (params.has("sid")) {
      return params.get("sid");
    }
    return "active";
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = text !== null && text !== undefined && text !== "" ? text : "—";
    }
  }

  function isValidCoordinate(lat, lon) {
    if (typeof lat !== "number" || typeof lon !== "number") return false;
    if (isNaN(lat) || !isFinite(lat) || isNaN(lon) || !isFinite(lon)) return false;
    if (lat < -90 || lat > 90) return false;
    if (lon < -180 || lon > 180) return false;
    return true;
  }

  function initMap() {
    const mapContainer = document.getElementById("mapContainer");
    if (!mapContainer || typeof L === "undefined" || state.map) return;

    state.map = L.map("mapContainer").setView([20, 0], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(state.map);

    state.trail = L.polyline([], { color: "#3b82f6", weight: 3, opacity: 0.8 }).addTo(state.map);
  }

  function fitMapBounds() {
    if (!state.map || typeof L === "undefined") return;
    const points = [];
    if (state.lastGpsCoords) points.push(state.lastGpsCoords);
    if (state.lastIpCoords) points.push(state.lastIpCoords);

    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  }

  function updateMapUI(fix, ip) {
    if (!state.map || typeof L === "undefined") return;

    // Update GPS marker & movement trail
    if (fix && isValidCoordinate(fix.lat, fix.lon)) {
      const gpsLatLng = [fix.lat, fix.lon];
      state.lastGpsCoords = gpsLatLng;

      if (!state.gpsMarker) {
        state.gpsMarker = L.marker(gpsLatLng).addTo(state.map);
        state.gpsMarker.bindPopup("<b>Browser GPS</b><br>Permission-Based Fix");
      } else {
        state.gpsMarker.setLatLng(gpsLatLng);
      }

      if (state.history && Array.isArray(state.history)) {
        const trailPoints = [];
        state.history.forEach(function (rec) {
          if (rec && isValidCoordinate(rec.lat, rec.lon)) {
            trailPoints.push([rec.lat, rec.lon]);
          }
        });
        if (state.trail) {
          state.trail.setLatLngs(trailPoints);
        }
      }
    }

    // Update IP location marker
    if (ip && isValidCoordinate(ip.lat, ip.lon)) {
      const ipLatLng = [ip.lat, ip.lon];
      state.lastIpCoords = ipLatLng;

      if (!state.ipMarker) {
        state.ipMarker = L.circleMarker(ipLatLng, {
          radius: 7,
          color: "#f59e0b",
          fillColor: "#f59e0b",
          fillOpacity: 0.8
        }).addTo(state.map);
        state.ipMarker.bindPopup("<b>Approximate IP Location</b><br>Network Routing Estimate");
      } else {
        state.ipMarker.setLatLng(ipLatLng);
      }
    }

    state.map.invalidateSize();
  }

  function updateHistoryTable(history) {
    const tbody = document.getElementById("historyTableBody");
    if (!tbody) return;

    tbody.textContent = "";

    if (!history || history.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 6;
      td.className = "k";
      td.style.textAlign = "center";
      td.textContent = "No recorded updates in history buffer.";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    history.forEach(function (rec, index) {
      const tr = document.createElement("tr");

      const tdNum = document.createElement("td");
      tdNum.textContent = (index + 1).toString();
      tr.appendChild(tdNum);

      const tdTime = document.createElement("td");
      tdTime.textContent = rec.timestamp || "—";
      tr.appendChild(tdTime);

      const tdLat = document.createElement("td");
      tdLat.textContent = typeof rec.lat === "number" ? rec.lat.toFixed(6) : "—";
      tr.appendChild(tdLat);

      const tdLon = document.createElement("td");
      tdLon.textContent = typeof rec.lon === "number" ? rec.lon.toFixed(6) : "—";
      tr.appendChild(tdLon);

      const tdAcc = document.createElement("td");
      tdAcc.textContent = typeof rec.accuracy === "number" ? "±" + Math.round(rec.accuracy) + " m" : "—";
      tr.appendChild(tdAcc);

      const tdSrc = document.createElement("td");
      tdSrc.textContent = "Browser Geolocation";
      tr.appendChild(tdSrc);

      tbody.appendChild(tr);
    });
  }

  function fetchDashboardData() {
    if (state.isPolling) return;
    state.isPolling = true;

    const endpoint = state.sid === "active" ? "/api/session/active" : "/api/session/" + state.sid + "/dashboard";

    fetch(endpoint)
      .then(function (res) {
        if (!res.ok) {
          if (res.status === 409) {
            setText("dash-status", "STOPPED");
            if (state.pollTimer) clearInterval(state.pollTimer);
          } else if (res.status === 410) {
            setText("dash-status", "EXPIRED");
            if (state.pollTimer) clearInterval(state.pollTimer);
          } else if (res.status === 404) {
            setText("dash-status", "NOT FOUND");
            if (state.pollTimer) clearInterval(state.pollTimer);
          }
          return null;
        }
        return res.json();
      })
      .then(function (data) {
        state.isPolling = false;
        if (!data) return;

        // Support both structured dashboard payload and standard session dict
        const sess = data.session || data;
        const fix = (data.gps && data.gps.current) || data.currentFix || data.gps_fix || (data.gps && data.gps.best);
        const ip = data.ip || data.ipInfo || data.ip_information;
        const history = (data.gps && data.gps.updates) || data.history || [];

        state.session = sess;
        state.gps = fix;
        state.ip = ip;
        state.history = history;

        if (data.version) {
          setText("dash-version-tag", "v" + data.version);
        }

        // Populate Session Overview
        setText("dash-session-id", sess.id || state.sid);
        setText("dash-status", sess.status || "—");
        setText("dash-connected", sess.connected ? "YES" : "NO");
        setText("dash-uptime", typeof sess.uptime_seconds === "number" ? Math.floor(sess.uptime_seconds) + "s" : (typeof sess.uptimeSeconds === "number" ? Math.floor(sess.uptimeSeconds) + "s" : "—"));
        setText("dash-updates", sess.gps_updates !== undefined ? sess.gps_updates : (sess.gpsUpdates || 0));

        let permState = "waiting for fix";
        if (sess.status === "STOPPED") permState = "session stopped";
        else if (sess.status === "EXPIRED") permState = "session expired";
        else if (fix) permState = "fix received";
        setText("dash-permission-state", permState);

        // Populate Browser GPS
        if (fix && isValidCoordinate(fix.lat, fix.lon)) {
          const fixStr = fix.lat.toFixed(6) + ", " + fix.lon.toFixed(6) + " (±" + Math.round(fix.accuracy || 0) + "m)";
          setText("dash-last-fix", fixStr);
          setText("dash-gps-loc-summary", fixStr);
          setText("dash-gps-lat", fix.lat.toFixed(9));
          setText("dash-gps-lon", fix.lon.toFixed(9));
          setText("dash-gps-acc", typeof fix.accuracy === "number" ? "±" + Math.round(fix.accuracy) + " m" : "—");
          setText("dash-gps-alt", typeof fix.altitude === "number" ? fix.altitude.toFixed(1) + " m" : "n/a");
          setText("dash-gps-speed", typeof fix.speed === "number" ? fix.speed.toFixed(1) + " m/s" : "n/a");
          setText("dash-gps-hdg", typeof fix.heading === "number" ? Math.round(fix.heading) + "°" : "n/a");
          setText("dash-gps-time", fix.timestamp || "—");
        } else {
          setText("dash-last-fix", "Waiting for fix...");
          setText("dash-gps-loc-summary", "Permission pending");
          setText("dash-gps-lat", "—");
          setText("dash-gps-lon", "—");
          setText("dash-gps-acc", "—");
          setText("dash-gps-alt", "—");
          setText("dash-gps-speed", "—");
          setText("dash-gps-hdg", "—");
          setText("dash-gps-time", "—");
        }

        // Populate IP Geolocation
        if (ip) {
          setText("dash-ip-address", ip.ip || "—");
          setText("dash-ip-country", ip.country || "—");
          setText("dash-ip-region", ip.region || "—");
          setText("dash-ip-city", ip.city || "—");
          setText("dash-ip-isp", ip.isp || ip.org || "—");

          if (isValidCoordinate(ip.lat, ip.lon)) {
            const place = [ip.city, ip.region, ip.country].filter(Boolean).join(", ");
            const ipSummary = (place || "Unknown") + " (" + ip.lat.toFixed(4) + ", " + ip.lon.toFixed(4) + ") [APPROXIMATE]";
            setText("dash-ip-loc-summary", ipSummary);
            setText("dash-ip-lat", ip.lat.toFixed(6) + " (Approximate)");
            setText("dash-ip-lon", ip.lon.toFixed(6) + " (Approximate)");
          } else {
            setText("dash-ip-loc-summary", "Lookup pending");
            setText("dash-ip-lat", "—");
            setText("dash-ip-lon", "—");
          }
        } else {
          setText("dash-ip-loc-summary", "Lookup pending");
          setText("dash-ip-address", "—");
          setText("dash-ip-country", "—");
          setText("dash-ip-region", "—");
          setText("dash-ip-city", "—");
          setText("dash-ip-isp", "—");
          setText("dash-ip-lat", "—");
          setText("dash-ip-lon", "—");
        }

        // Populate Discrepancy
        if (data.comparison && data.comparison.text) {
          setText("dash-discrepancy", data.comparison.text);
        } else if (fix && ip && isValidCoordinate(fix.lat, fix.lon) && isValidCoordinate(ip.lat, ip.lon)) {
          const distKm = calculateHaversine(ip.lat, ip.lon, fix.lat, fix.lon);
          setText("dash-discrepancy", distKm.toFixed(2) + " km coordinate difference");
        } else {
          setText("dash-discrepancy", "— (Requires valid GPS and IP coordinates)");
        }

        updateMapUI(fix, ip);
        updateHistoryTable(history);
      })
      .catch(function () {
        state.isPolling = false;
      });
  }

  function calculateHaversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function initDashboard() {
    state.sid = getSessionId();
    initMap();

    fetchDashboardData();
    state.pollTimer = setInterval(fetchDashboardData, 3000);

    const btnResetView = document.getElementById("btn-reset-view");
    const btnFitBounds = document.getElementById("btn-fit-bounds");
    const btnFullscreen = document.getElementById("btn-toggle-fullscreen");
    const btnExportJson = document.getElementById("btn-export-json");
    const btnExportCsv = document.getElementById("btn-export-csv");
    const btnClearHistory = document.getElementById("btn-clear-history");

    if (btnResetView) {
      btnResetView.onclick = function () {
        if (state.map && state.lastGpsCoords) {
          state.map.setView(state.lastGpsCoords, 14);
        } else if (state.map) {
          state.map.setView([20, 0], 2);
        }
      };
    }

    if (btnFitBounds) {
      btnFitBounds.onclick = function () {
        fitMapBounds();
      };
    }

    if (btnFullscreen) {
      const container = document.getElementById("mapContainer");
      btnFullscreen.onclick = function () {
        if (!container) return;
        if (!document.fullscreenElement) {
          if (container.requestFullscreen) container.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      };
    }

    if (btnExportJson) {
      btnExportJson.onclick = function () {
        window.open("/api/session/" + state.sid + "/export?format=json", "_blank");
      };
    }

    if (btnExportCsv) {
      btnExportCsv.onclick = function () {
        window.open("/api/session/" + state.sid + "/export?format=csv", "_blank");
      };
    }

    if (btnClearHistory) {
      btnClearHistory.onclick = function () {
        fetch("/api/session/" + state.sid, { method: "DELETE" }).then(function () {
          state.history = [];
          updateHistoryTable([]);
          if (state.trail) state.trail.setLatLngs([]);
        });
      };
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
  } else {
    initDashboard();
  }
})();
