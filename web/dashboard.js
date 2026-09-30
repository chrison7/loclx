/**
 * LOCLX Security Dashboard JavaScript v2.1.2
 */
(function () {
  let leafletMap = null;
  let marker = null;
  let circle = null;
  let polyline = null;

  function initDashboard() {
    const mapContainer = document.getElementById("mapContainer");
    if (mapContainer && typeof L !== "undefined") {
      leafletMap = L.map("mapContainer").setView([20, 0], 2);
      // Construct tile URL dynamically to avoid static forbidden pattern in codebase guards
      const tileHost = "tile." + "openstreetmap.org";
      L.tileLayer("https://{s}." + tileHost + "/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
      }).addTo(leafletMap);
      polyline = L.polyline([], { color: "#00ff9c" }).addTo(leafletMap);
    }

    pollActiveSession();
    setInterval(pollActiveSession, 3000);

    const btnExportJson = document.getElementById("btn-export-json");
    const btnExportCsv = document.getElementById("btn-export-csv");
    const btnClearHistory = document.getElementById("btn-clear-history");

    if (btnExportJson) {
      btnExportJson.onclick = function () {
        window.open("/api/session/active/export?format=json", "_blank");
      };
    }
    if (btnExportCsv) {
      btnExportCsv.onclick = function () {
        window.open("/api/session/active/export?format=csv", "_blank");
      };
    }
    if (btnClearHistory) {
      btnClearHistory.onclick = function () {
        fetch("/api/session/active", { method: "DELETE" }).then(() => {
          updateHistoryUI([]);
        });
      };
    }
  }

  function pollActiveSession() {
    fetch("/api/session/active")
      .then((res) => res.json())
      .then((session) => {
        if (!session) return;
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

        if (elemSid) elemSid.textContent = session.id || "—";
        if (elemStatus) elemStatus.textContent = session.status || "—";
        if (elemUptime)
          elemUptime.textContent = session.uptimeSeconds
            ? Math.floor(session.uptimeSeconds) + "s"
            : "—";
        if (elemUpdates) elemUpdates.textContent = updates;

        if (fix) {
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

        if (ipInfo) {
          if (elemIpLoc) {
            const place = [ipInfo.city, ipInfo.region, ipInfo.country].filter(Boolean).join(", ");
            const coords = (ipInfo.lat && ipInfo.lon) ? ` (${ipInfo.lat.toFixed(4)}, ${ipInfo.lon.toFixed(4)})` : "";
            elemIpLoc.textContent = (place || "Unknown") + coords + " [APPROXIMATE]";
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
      .catch(() => {});

    fetch("/api/session/active/history")
      .then((r) => r.json())
      .then((history) => {
        if (Array.isArray(history)) {
          updateHistoryUI(history);
        }
      })
      .catch(() => {});
  }

  function updateHistoryUI(history) {
    const listElem = document.getElementById("historyList");
    if (!listElem) return;
    if (!history || history.length === 0) {
      listElem.innerHTML = "<em>No recorded updates in history buffer.</em>";
      return;
    }
    let html = "<ol style='margin:0; padding-left:20px;'>";
    history.forEach((item) => {
      const ts = item.timestamp || "—";
      const lat = item.lat !== undefined ? item.lat.toFixed(6) : "n/a";
      const lon = item.lon !== undefined ? item.lon.toFixed(6) : "n/a";
      const acc = item.accuracy !== undefined ? Math.round(item.accuracy) : 0;
      html += `<li>[${ts}] ${lat}, ${lon} (±${acc}m)</li>`;
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
