/**
 * LOCLX Security Dashboard JavaScript v2.4.2
 */
(function () {
  let leafletMap = null;
  let marker = null;
  let circle = null;
  let polyline = null;
  let ipMarker = null;
  let connectionLine = null;
  let lastGpsCoords = null;

  function getSessionId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === "dashboard" && parts[1] !== "dashboard.html") {
      return parts[1];
    }
    return "active";
  }

  function initDashboard() {
    const mapContainer = document.getElementById("mapContainer");
    if (mapContainer && typeof L !== "undefined") {
      leafletMap = L.map("mapContainer").setView([20, 0], 2);
      const tileHost = "tile." + "openstreetmap.org";
      L.tileLayer("https://{s}." + tileHost + "/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
      }).addTo(leafletMap);
      polyline = L.polyline([], { color: "#00ff9c", weight: 3 }).addTo(leafletMap);
    }

    const sid = getSessionId();
    pollActiveSession(sid);
    setInterval(function () { pollActiveSession(sid); }, 3000);

    const btnResetView = document.getElementById("btn-reset-view");
    const btnFullscreen = document.getElementById("btn-toggle-fullscreen");
    const btnExportJson = document.getElementById("btn-export-json");
    const btnExportCsv = document.getElementById("btn-export-csv");
    const btnClearHistory = document.getElementById("btn-clear-history");

    if (btnResetView) {
      btnResetView.onclick = function () {
        if (leafletMap && lastGpsCoords) {
          leafletMap.setView(lastGpsCoords, 14);
        } else if (leafletMap) {
          leafletMap.setView([20, 0], 2);
        }
      };
    }

    if (btnFullscreen && mapContainer) {
      btnFullscreen.onclick = function () {
        if (!document.fullscreenElement) {
          if (mapContainer.requestFullscreen) mapContainer.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      };
    }

    if (btnExportJson) {
      btnExportJson.onclick = function () {
        window.open("/api/session/" + sid + "/export?format=json", "_blank");
      };
    }
    if (btnExportCsv) {
      btnExportCsv.onclick = function () {
        window.open("/api/session/" + sid + "/export?format=csv", "_blank");
      };
    }
    if (btnClearHistory) {
      btnClearHistory.onclick = function () {
        fetch("/api/session/" + sid, { method: "DELETE" }).then(function () {
          updateHistoryUI([]);
        });
      };
    }
  }

  function pollActiveSession(sid) {
    const endpoint = "/api/session/" + sid;
    fetch(endpoint)
      .then(function (res) { return res.json(); })
      .then(function (session) {
        if (!session || session.error) return;
        const elemSid = document.getElementById("dash-session-id");
        const elemStatus = document.getElementById("dash-status");
        const elemUptime = document.getElementById("dash-uptime");
        const elemUpdates = document.getElementById("dash-updates");
        const elemLastFix = document.getElementById("dash-last-fix");
        const elemDiff = document.getElementById("dash-diff");
        const elemIpLoc = document.getElementById("dash-ip-loc");
        const elemGpsLoc = document.getElementById("dash-gps-loc");
        const elemDiscrepancy = document.getElementById("dash-discrepancy");

        const fix = session.currentFix || session.gps_fix;
        const ipInfo = session.ipInfo || session.ip_information;
        const updates = session.gpsUpdates !== undefined ? session.gpsUpdates : (session.gps_updates || 0);

        if (elemSid) elemSid.textContent = session.id || sid;
        if (elemStatus) elemStatus.textContent = session.status || "—";
        if (elemUptime)
          elemUptime.textContent = session.uptimeSeconds
            ? Math.floor(session.uptimeSeconds) + "s"
            : "—";
        if (elemUpdates) elemUpdates.textContent = updates;

        if (fix) {
          lastGpsCoords = [fix.lat, fix.lon];
          if (elemLastFix) {
            elemLastFix.textContent =
              fix.lat.toFixed(6) +
              ", " +
              fix.lon.toFixed(6) +
              " (±" +
              Math.round(fix.accuracy || 0) +
              "m)";
          }
          if (elemGpsLoc) {
            elemGpsLoc.textContent =
              fix.lat.toFixed(6) +
              ", " +
              fix.lon.toFixed(6) +
              " (Accuracy: ±" +
              Math.round(fix.accuracy || 0) +
              "m)";
          }
          if (leafletMap && L) {
            const latLng = [fix.lat, fix.lon];
            if (!marker) {
              marker = L.marker(latLng).addTo(leafletMap);
            } else {
              marker.setLatLng(latLng);
            }
            if (!circle && fix.accuracy) {
              circle = L.circle(latLng, {
                radius: fix.accuracy,
                color: "#4fd6ff",
                fillColor: "#4fd6ff",
                fillOpacity: 0.2
              }).addTo(leafletMap);
            } else if (circle && fix.accuracy) {
              circle.setLatLng(latLng);
              circle.setRadius(fix.accuracy);
            }
            if (polyline) {
              polyline.addLatLng(latLng);
            }
            leafletMap.setView(latLng, 14);
          }
        }

        if (ipInfo && typeof ipInfo.lat === "number" && typeof ipInfo.lon === "number") {
          const ipCoords = [ipInfo.lat, ipInfo.lon];
          if (elemIpLoc) {
            const place = [ipInfo.city, ipInfo.region, ipInfo.country].filter(Boolean).join(", ");
            const coords = " (" + ipInfo.lat.toFixed(4) + ", " + ipInfo.lon.toFixed(4) + ")";
            elemIpLoc.textContent = (place || "Unknown") + coords + " [APPROXIMATE]";
          }
          if (leafletMap && L) {
            if (!ipMarker) {
              ipMarker = L.circleMarker(ipCoords, {
                radius: 6,
                color: "#ffaa00",
                fillColor: "#ffaa00",
                fillOpacity: 0.8
              }).addTo(leafletMap);
            } else {
              ipMarker.setLatLng(ipCoords);
            }
            if (fix) {
              const gpsCoords = [fix.lat, fix.lon];
              if (!connectionLine) {
                connectionLine = L.polyline([ipCoords, gpsCoords], {
                  color: "#ffaa00",
                  dashArray: "5, 5",
                  weight: 2
                }).addTo(leafletMap);
              } else {
                connectionLine.setLatLngs([ipCoords, gpsCoords]);
              }
            }
          }
        }

        if (ipInfo && fix) {
          const ipLat = ipInfo.lat !== undefined ? ipInfo.lat : ipInfo.latitude;
          const ipLon = ipInfo.lon !== undefined ? ipInfo.lon : ipInfo.longitude;
          if (ipLat !== undefined && ipLon !== undefined) {
            const dist = calculateHaversine(ipLat, ipLon, fix.lat, fix.lon);
            const text = dist.toFixed(2) + " km difference";
            if (elemDiff) elemDiff.textContent = text + " (Network IP vs GPS Fix)";
            if (elemDiscrepancy) elemDiscrepancy.textContent = text;
          }
        }
      })
      .catch(function () {});

    fetch(endpoint + "/history")
      .then(function (r) { return r.json(); })
      .then(function (history) {
        if (Array.isArray(history)) {
          updateHistoryUI(history);
        }
      })
      .catch(function () {});
  }

  function updateHistoryUI(history) {
    const listElem = document.getElementById("historyList");
    if (!listElem) return;
    if (!history || history.length === 0) {
      listElem.innerHTML = "<em>No recorded updates in history buffer.</em>";
      return;
    }
    let html = "<ol style='margin:0; padding-left:20px;'>";
    history.forEach(function (item) {
      const ts = item.timestamp || "—";
      const lat = item.lat !== undefined ? item.lat.toFixed(6) : "n/a";
      const lon = item.lon !== undefined ? item.lon.toFixed(6) : "n/a";
      const acc = item.accuracy !== undefined ? Math.round(item.accuracy) : 0;
      html += "<li>[" + ts + "] " + lat + ", " + lon + " (±" + acc + "m)</li>";
    });
    html += "</ol>";
    listElem.innerHTML = html;
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
  } else {
    initDashboard();
  }
})();
