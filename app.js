/**
 * Bengaluru Namma Metro - Network Analysis Interactive Application
 * Powers the interactive map, topological graph, shortest path planner,
 * centrality inspector, disruption simulator, and research workspace.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Check if METRO_DATA is loaded
  if (!window.METRO_DATA) {
    console.error("METRO_DATA not found. Please ensure bangalore_metro_data.js is loaded.");
    return;
  }

  const { nodes, edges, similarity, analysis } = window.METRO_DATA;

  // State Management
  const state = {
    isPhase1Only: false,
    activeMode: "geo", // 'geo' or 'graph'
    activeTab: "commuter",
    selectedNodeScale: "betweenness",
    disruptedStation: null,
    highlightedPath: [],
    showStationLabels: false,
    visibleLines: new Set(["Purple Line", "Green Line", "Yellow Line"]),
    map: null,
    mapLayers: {
      tracks: null,
      stations: null,
      stationLabels: null,
      routeHighlight: null,
      endpointPins: null
    }
  };

  // Node and Edge lookup dictionaries for O(1) queries
  const nodeMap = new Map();
  nodes.forEach(n => nodeMap.set(n.id, n));

  // Build Adjacency List for Graph Traversal & Dijkstra
  function buildAdjacencyList(filterPhase1 = false, excludeStation = null, addEdge = null) {
    const adj = new Map();
    nodes.forEach(n => {
      if (filterPhase1 && !n.is_phase1) return;
      if (excludeStation && n.id === excludeStation) return;
      adj.set(n.id, []);
    });

    edges.forEach(e => {
      if (filterPhase1 && e.status !== "Operational") return;
      if (excludeStation && (e.source === excludeStation || e.target === excludeStation)) return;
      if (adj.has(e.source) && adj.has(e.target)) {
        adj.get(e.source).push({ target: e.target, dist: e.dist_km, time: e.time_min, line: e.line, color: e.color });
        adj.get(e.target).push({ target: e.source, dist: e.dist_km, time: e.time_min, line: e.line, color: e.color });
      }
    });

    if (addEdge && adj.has(addEdge.u) && adj.has(addEdge.v)) {
      adj.get(addEdge.u).push({ target: addEdge.v, dist: addEdge.dist, time: addEdge.time, line: "Proposed Link", color: "#06b6d4" });
      adj.get(addEdge.v).push({ target: addEdge.u, dist: addEdge.dist, time: addEdge.time, line: "Proposed Link", color: "#06b6d4" });
    }

    return adj;
  }

  /* ========================================================
     1. INITIALIZE UI ELEMENTS & DROPDOWNS
     ======================================================== */
  function populateDropdowns(filterLine = "all") {
    const originSel = document.getElementById("selectOrigin");
    const destSel = document.getElementById("selectDest");
    const disruptSel = document.getElementById("selectDisruptStation");
    const newLinkASel = document.getElementById("selectNewLinkA");
    const newLinkBSel = document.getElementById("selectNewLinkB");
    const dlOrigin = document.getElementById("stationsDatalistOrigin");
    const dlDest = document.getElementById("stationsDatalistDest");

    const currentOrigin = originSel ? originSel.value : "Whitefield (Kadugodi)";
    const currentDest = destSel ? destSel.value : "Electronic City";

    // Clear dropdowns
    [originSel, destSel, disruptSel, newLinkASel, newLinkBSel].forEach(sel => {
      if (sel) sel.innerHTML = "";
    });
    if (dlOrigin) dlOrigin.innerHTML = "";
    if (dlDest) dlDest.innerHTML = "";

    // Build datalist options for search autocomplete
    nodes.forEach(n => {
      const opt = document.createElement("option");
      opt.value = n.name;
      opt.label = `${n.lines.join(", ")} | ${n.zone}`;
      if (dlOrigin) dlOrigin.appendChild(opt.cloneNode(true));
      if (dlDest) dlDest.appendChild(opt.cloneNode(true));
    });

    // Filter nodes if line selected
    let filteredNodes = [...nodes];
    if (filterLine === "interchange") {
      filteredNodes = nodes.filter(n => n.is_interchange);
    } else if (filterLine !== "all") {
      filteredNodes = nodes.filter(n => n.lines.includes(filterLine));
    }

    // Helper to group by line for select dropdowns
    function buildGroupedOptions(selectEl) {
      if (!selectEl) return;

      const purpleGroup = document.createElement("optgroup");
      purpleGroup.label = "🟣 Purple Line (Challegatta - Whitefield)";

      const greenGroup = document.createElement("optgroup");
      greenGroup.label = "🟢 Green Line (Madavara - Silk Institute)";

      const yellowGroup = document.createElement("optgroup");
      yellowGroup.label = "🟡 Yellow Line (RV Road - Bommasandra)";

      filteredNodes.forEach(n => {
        const icBadge = n.is_interchange ? " [🔄 INTERCHANGE]" : "";
        const opt = new Option(`${n.name}${icBadge}`, n.id);

        if (n.lines.includes("Purple Line")) {
          purpleGroup.appendChild(opt.cloneNode(true));
        } else if (n.lines.includes("Green Line")) {
          greenGroup.appendChild(opt.cloneNode(true));
        } else if (n.lines.includes("Yellow Line")) {
          yellowGroup.appendChild(opt.cloneNode(true));
        }
      });

      if (purpleGroup.children.length > 0) selectEl.appendChild(purpleGroup);
      if (greenGroup.children.length > 0) selectEl.appendChild(greenGroup);
      if (yellowGroup.children.length > 0) selectEl.appendChild(yellowGroup);
    }

    buildGroupedOptions(originSel);
    buildGroupedOptions(destSel);

    // Populate other selectors without optgroups
    nodes.forEach(n => {
      const lineStr = n.lines.map(l => l.replace(" Line", "")).join("/");
      const opt = new Option(`${n.name} [${lineStr}]`, n.id);
      if (disruptSel) disruptSel.add(opt.cloneNode(true));
      if (newLinkASel) newLinkASel.add(opt.cloneNode(true));
      if (newLinkBSel) newLinkBSel.add(opt.cloneNode(true));
    });

    // Restore or set defaults
    if (originSel && nodeMap.has(currentOrigin)) originSel.value = currentOrigin;
    else if (originSel && originSel.options.length > 0) originSel.selectedIndex = 0;

    if (destSel && nodeMap.has(currentDest)) destSel.value = currentDest;
    else if (destSel && destSel.options.length > 1) destSel.selectedIndex = 1;

    const inputOrigin = document.getElementById("inputOriginSearch");
    const inputDest = document.getElementById("inputDestSearch");
    if (inputOrigin && originSel) inputOrigin.value = originSel.value;
    if (inputDest && destSel) inputDest.value = destSel.value;

    if (disruptSel) disruptSel.value = "Nadaprabhu Kempegowda Station Majestic";
    if (newLinkASel) newLinkASel.value = "Indiranagar";
    if (newLinkBSel) newLinkBSel.value = "Central Silk Board";

    updateStationBadges();
  }

  function updateStationBadges() {
    const origSel = document.getElementById("selectOrigin");
    const destSel = document.getElementById("selectDest");
    const bFrom = document.getElementById("badgeFromLine");
    const bTo = document.getElementById("badgeToLine");

    if (origSel && bFrom && nodeMap.has(origSel.value)) {
      const n = nodeMap.get(origSel.value);
      bFrom.textContent = `${n.lines.join(", ")} | ${n.zone}`;
    }
    if (destSel && bTo && nodeMap.has(destSel.value)) {
      const n = nodeMap.get(destSel.value);
      bTo.textContent = `${n.lines.join(", ")} | ${n.zone}`;
    }

    if (origSel && destSel && nodeMap.has(origSel.value) && nodeMap.has(destSel.value)) {
      updateLiveCentralityPanel(origSel.value, destSel.value);
    }
  }

  // Global hooks for map popup click-to-select
  window.setAsOrigin = function (stationId) {
    const originSel = document.getElementById("selectOrigin");
    const inputOrigin = document.getElementById("inputOriginSearch");
    if (originSel && nodeMap.has(stationId)) {
      originSel.value = stationId;
      if (inputOrigin) inputOrigin.value = stationId;
      updateStationBadges();
      triggerAutoRoute();
      if (state.map) state.map.closePopup();
    }
  };

  window.setAsDestination = function (stationId) {
    const destSel = document.getElementById("selectDest");
    const inputDest = document.getElementById("inputDestSearch");
    if (destSel && nodeMap.has(stationId)) {
      destSel.value = stationId;
      if (inputDest) inputDest.value = stationId;
      updateStationBadges();
      triggerAutoRoute();
      if (state.map) state.map.closePopup();
    }
  };

  function triggerAutoRoute() {
    const fromSt = document.getElementById("selectOrigin").value;
    const toSt = document.getElementById("selectDest").value;
    if (fromSt && toSt) {
      const route = findShortestPath(fromSt, toSt);
      renderRouteResult(route);
    }
  }

  /* ========================================================
     2. LEAFLET GEOGRAPHIC TRANSIT MAP
     ======================================================== */
  function initLeafletMap() {
    const mapContainer = document.getElementById("leafletMap");
    if (!mapContainer || typeof L === "undefined") return;

    // Center on Bangalore
    state.map = L.map("leafletMap", {
      zoomControl: true,
      attributionControl: false
    }).setView([12.9716, 77.5946], 11);

    // Esri World Dark Gray Canvas tiles (Clean, Dark, High-Performance, Zero Watermarks)
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16,
      attribution: "&copy; Esri"
    }).addTo(state.map);

    state.mapLayers.tracks = L.layerGroup().addTo(state.map);
    state.mapLayers.stations = L.layerGroup().addTo(state.map);
    state.mapLayers.stationLabels = L.layerGroup().addTo(state.map);
    state.mapLayers.routeHighlight = L.layerGroup().addTo(state.map);
    state.mapLayers.endpointPins = L.layerGroup().addTo(state.map);

    // Dynamic zoom-level label density
    state.map.on("zoomend", () => {
      if (state.showStationLabels) {
        renderMapLayers();
      }
    });

    renderMapLayers();
  }

  function getStationColor(n) {
    if (n.is_interchange) return "#ef4444";
    if (n.lines.includes("Purple Line")) return "#a855f7";
    if (n.lines.includes("Green Line")) return "#10b981";
    if (n.lines.includes("Yellow Line")) return "#f59e0b";
    return "#3b82f6";
  }

  function getStationRadius(n) {
    const scale = state.selectedNodeScale;
    if (scale === "betweenness") {
      return n.is_interchange ? 13 : Math.max(5.5, n.betweenness_centrality * 20 + 5);
    } else if (scale === "degree") {
      return n.degree * 3.0;
    } else {
      return Math.max(5.5, n.closeness_centrality * 130);
    }
  }

  function renderMapLayers() {
    if (!state.map) return;

    state.mapLayers.tracks.clearLayers();
    state.mapLayers.stations.clearLayers();
    if (state.mapLayers.stationLabels) state.mapLayers.stationLabels.clearLayers();

    const hasActiveRoute = state.highlightedPath && state.highlightedPath.length > 0;
    const activeRouteStations = hasActiveRoute ? new Set(state.highlightedPath.map(p => p.station)) : null;

    // 1. Draw High-Contrast Track Lines (Filtered by visibleLines)
    edges.forEach(e => {
      if (state.isPhase1Only && e.status !== "Operational") return;
      if (state.visibleLines && !state.visibleLines.has(e.line)) return;
      if (state.disruptedStation && (e.source === state.disruptedStation || e.target === state.disruptedStation)) return;

      const u = nodeMap.get(e.source);
      const v = nodeMap.get(e.target);
      if (!u || !v) return;

      // Track Under-Glow Polyline
      L.polyline([[u.lat, u.lon], [v.lat, v.lon]], {
        color: e.color,
        weight: 9,
        opacity: hasActiveRoute ? 0.15 : 0.35,
        lineCap: "round"
      }).addTo(state.mapLayers.tracks);

      // Core Solid Track Line (slightly dimmed if an active route is highlighted)
      L.polyline([[u.lat, u.lon], [v.lat, v.lon]], {
        color: e.color,
        weight: 4.5,
        opacity: hasActiveRoute ? 0.40 : 0.95,
        dashArray: e.status === "Phase 2 Ready" ? "6, 6" : null
      }).addTo(state.mapLayers.tracks);
    });

    // 2. Draw Station Markers & Tooltips
    const currentZoom = state.map ? state.map.getZoom() : 11;
    nodes.forEach(n => {
      if (state.isPhase1Only && !n.is_phase1) return;
      if (state.visibleLines && !n.lines.some(l => state.visibleLines.has(l))) return;

      const isDisrupted = (n.id === state.disruptedStation);
      const isOnRoute = activeRouteStations ? activeRouteStations.has(n.id) : false;
      const isStart = state.highlightedPath && state.highlightedPath.length > 0 && state.highlightedPath[0].station === n.id;
      const isEnd = state.highlightedPath && state.highlightedPath.length > 0 && state.highlightedPath[state.highlightedPath.length - 1].station === n.id;

      const color = isDisrupted ? "#6b7280" : (isStart ? "#10b981" : (isEnd ? "#ef4444" : getStationColor(n)));
      const baseRadius = isDisrupted ? 4 : getStationRadius(n);
      const radius = (isStart || isEnd) ? baseRadius + 3 : (isOnRoute ? baseRadius + 1.5 : baseRadius);

      const circle = L.circleMarker([n.lat, n.lon], {
        radius: radius,
        fillColor: color,
        color: isDisrupted ? "#4b5563" : (isStart ? "#a7f3d0" : (isEnd ? "#fecaca" : (n.is_interchange ? "#ffd700" : (isOnRoute ? "#38bdf8" : "#ffffff")))),
        weight: (isStart || isEnd) ? 3.5 : (n.is_interchange ? 3.0 : (isOnRoute ? 2.5 : 1.5)),
        opacity: 1,
        fillOpacity: isDisrupted ? 0.4 : (hasActiveRoute && !isOnRoute ? 0.55 : 0.95)
      });

      // Bind Click & Hover
      circle.on("mouseover", () => showStationTooltip(n));
      circle.on("mouseout", () => hideStationTooltip());
      circle.on("click", () => {
        circle.bindPopup(createPopupContent(n)).openPopup();
      });

      // Bind clean hover tooltip so station names are visible on hover without cluttering the map
      circle.bindTooltip(`<strong>${n.name}</strong><br><span style="font-size:10px; color:#94a3b8;">${n.lines.join(", ")} | ${n.zone}</span>`, {
        direction: 'top',
        className: 'clean-map-tooltip',
        offset: [0, -radius - 4]
      });

      circle.addTo(state.mapLayers.stations);

      // 3. Station Name Labels on the Map (Only when enabled by user AND zoomed in close >= 13)
      if (state.showStationLabels && state.mapLayers.stationLabels && currentZoom >= 13) {
        const isHub = n.is_interchange || n.betweenness_centrality > 0.08;
        const labelIcon = L.divIcon({
          className: 'custom-div-label',
          html: `<div class="station-map-label ${isHub ? 'hub' : ''}">${n.name}</div>`,
          iconSize: [null, null],
          iconAnchor: [-radius - 6, 11]
        });
        L.marker([n.lat, n.lon], { icon: labelIcon, interactive: false })
          .addTo(state.mapLayers.stationLabels);
      }
    });
  }

  function createPopupContent(n) {
    const escapedId = n.id.replace(/'/g, "\\'");
    return `
      <div style="font-family: var(--font-body); color: #f9fafb; min-width: 210px; padding: 2px;">
        <h4 style="margin: 0 0 4px 0; font-size: 14px; font-weight: bold; color: #ffffff;">${n.name}</h4>
        <div style="font-size: 11px; margin-bottom: 6px; color: #9ca3af;">${n.lines.join(", ")} | ${n.zone}</div>
        <div style="font-size: 11px; line-height: 1.5; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px; color: #d1d5db;">
          <div><strong>Betweenness:</strong> <span style="color:#38bdf8; font-weight:bold;">${n.betweenness_centrality.toFixed(4)}</span></div>
          <div><strong>Degree:</strong> ${n.degree} (${n.degree_centrality.toFixed(4)})</div>
          <div><strong>Closeness:</strong> ${n.closeness_centrality.toFixed(4)}</div>
          <div><strong>Type:</strong> ${n.is_interchange ? '⭐ Interchange Hub' : 'Corridor Transit'}</div>
        </div>
        <div class="map-popup-actions">
          <button class="btn-popup-pick btn-popup-from" onclick="window.setAsOrigin('${escapedId}')" title="Set this station as departure point">
            🟢 Set FROM
          </button>
          <button class="btn-popup-pick btn-popup-to" onclick="window.setAsDestination('${escapedId}')" title="Set this station as arrival destination">
            🎯 Set TO
          </button>
        </div>
      </div>
    `;
  }

  function showStationTooltip(n) {
    const tip = document.getElementById("stationTooltip");
    if (!tip) return;

    document.getElementById("tipStationName").textContent = n.name;
    document.getElementById("tipZone").textContent = `Zone: ${n.zone}`;
    document.getElementById("tipDegree").textContent = `${n.degree} (${n.degree_centrality.toFixed(4)})`;
    document.getElementById("tipBetweenness").textContent = n.betweenness_centrality.toFixed(4);
    document.getElementById("tipCloseness").textContent = n.closeness_centrality.toFixed(4);

    const cutEl = document.getElementById("tipCutVertex");
    cutEl.textContent = n.is_articulation_point ? "Articulation Point (SPOF)" : "Redundant";
    cutEl.style.color = n.is_articulation_point ? "#f87171" : "#34d399";

    const badgesContainer = document.getElementById("tipLines");
    badgesContainer.innerHTML = "";
    n.lines.forEach(l => {
      const badge = document.createElement("span");
      badge.className = `line-badge ${l.toLowerCase().includes("purple") ? "purple" : l.toLowerCase().includes("green") ? "green" : "yellow"}`;
      badge.textContent = l;
      badgesContainer.appendChild(badge);
    });

    tip.classList.add("active");
  }

  function hideStationTooltip() {
    const tip = document.getElementById("stationTooltip");
    if (tip) tip.classList.remove("active");
  }

  /* ========================================================
     3. CANVO FORCE-DIRECTED GRAPH VISUALIZATION
     ======================================================== */
  class ForceGraph {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext("2d");
      this.graphNodes = [];
      this.graphEdges = [];
      this.animId = null;
      this.isDragging = false;
      this.draggedNode = null;
      this.transform = { x: 0, y: 0, k: 1 };

      this.init();
    }

    init() {
      this.resize();
      window.addEventListener("resize", () => this.resize());
      this.setupInteraction();
      this.buildData();
    }

    resize() {
      if (!this.canvas) return;
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.canvas.width = rect.width;
      this.canvas.height = rect.height;
      this.transform.x = rect.width / 2;
      this.transform.y = rect.height / 2;
    }

    buildData() {
      // Scale lat/lon into 2D layout space centered at Bangalore
      const latMin = 12.80, latMax = 13.08;
      const lonMin = 77.46, lonMax = 77.78;

      this.graphNodes = nodes
        .filter(n => !(state.isPhase1Only && !n.is_phase1))
        .map(n => {
          // Invert lat for canvas Y
          const normX = (n.lon - lonMin) / (lonMax - lonMin);
          const normY = 1 - (n.lat - latMin) / (latMax - latMin);
          return {
            ...n,
            x: (normX - 0.5) * (this.canvas.width * 0.85),
            y: (normY - 0.5) * (this.canvas.height * 0.85),
            vx: 0,
            vy: 0
          };
        });

      const nodeIndexMap = new Map();
      this.graphNodes.forEach((n, i) => nodeIndexMap.set(n.id, i));

      this.graphEdges = [];
      edges.forEach(e => {
        if (state.isPhase1Only && e.status !== "Operational") return;
        if (state.disruptedStation && (e.source === state.disruptedStation || e.target === state.disruptedStation)) return;
        const uIdx = nodeIndexMap.get(e.source);
        const vIdx = nodeIndexMap.get(e.target);
        if (uIdx !== undefined && vIdx !== undefined) {
          this.graphEdges.push({
            source: uIdx,
            target: vIdx,
            color: e.color
          });
        }
      });
    }

    start() {
      this.buildData();
      const tick = () => {
        this.render();
        this.animId = requestAnimationFrame(tick);
      };
      if (this.animId) cancelAnimationFrame(this.animId);
      this.animId = requestAnimationFrame(tick);
    }

    stop() {
      if (this.animId) cancelAnimationFrame(this.animId);
    }

    render() {
      const { ctx, canvas, transform } = this;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      // Track active route edges for neon highlight
      const activeEdges = new Set();
      if (state.highlightedPath && state.highlightedPath.length > 1) {
        for (let i = 0; i < state.highlightedPath.length - 1; i++) {
          const u = state.highlightedPath[i].station;
          const v = state.highlightedPath[i + 1].station;
          activeEdges.add(`${u}__${v}`);
          activeEdges.add(`${v}__${u}`);
        }
      }

      // 1. Draw Edges
      this.graphEdges.forEach(e => {
        const u = this.graphNodes[e.source];
        const v = this.graphNodes[e.target];
        if (!u || !v) return;

        const isRouteEdge = activeEdges.has(`${u.id}__${v.id}`);
        if (isRouteEdge) {
          ctx.strokeStyle = "#38bdf8";
          ctx.lineWidth = 5;
          ctx.shadowColor = "#38bdf8";
          ctx.shadowBlur = 12;
        } else {
          ctx.strokeStyle = activeEdges.size > 0 ? (e.color ? e.color + "44" : "#374151") : (e.color || "#6b7280");
          ctx.lineWidth = activeEdges.size > 0 ? 2 : 3;
          ctx.shadowBlur = 0;
        }

        ctx.beginPath();
        ctx.moveTo(u.x, u.y);
        ctx.lineTo(v.x, v.y);
        ctx.stroke();
      });
      ctx.shadowBlur = 0; // reset blur

      // 2. Draw Nodes
      this.graphNodes.forEach(n => {
        const isDisrupted = (n.id === state.disruptedStation);
        const isOnRoute = state.highlightedPath && state.highlightedPath.some(p => p.station === n.id);
        const isStart = state.highlightedPath && state.highlightedPath.length > 0 && state.highlightedPath[0].station === n.id;
        const isEnd = state.highlightedPath && state.highlightedPath.length > 0 && state.highlightedPath[state.highlightedPath.length - 1].station === n.id;

        const baseR = isDisrupted ? 3.5 : getStationRadius(n);
        const r = (isStart || isEnd) ? baseR + 3 : (isOnRoute ? baseR + 1.5 : baseR);

        const color = isDisrupted ? "#6b7280" : (isStart ? "#10b981" : (isEnd ? "#ef4444" : (isOnRoute ? "#38bdf8" : getStationColor(n))));

        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        ctx.strokeStyle = isStart ? "#a7f3d0" : (isEnd ? "#fecaca" : (n.is_interchange ? "#ffd700" : (isOnRoute ? "#38bdf8" : "#ffffff")));
        ctx.lineWidth = (isStart || isEnd) ? 3.5 : (n.is_interchange ? 2.5 : 1);
        ctx.stroke();

        // High-contrast labels for hubs, start/end, and major betweenness stations
        const shouldLabel = isStart || isEnd || n.is_interchange || n.betweenness_centrality > 0.08 || (isOnRoute && transform.k >= 1.2);
        if (shouldLabel) {
          ctx.font = (isStart || isEnd || n.is_interchange) ? "bold 11px Inter, sans-serif" : "10px Inter, sans-serif";
          const labelText = isStart ? `START: ${n.name}` : (isEnd ? `DEST: ${n.name}` : n.name);
          const textWidth = ctx.measureText(labelText).width;

          // Draw dark pill backing for 100% text readability
          ctx.fillStyle = "rgba(10, 14, 23, 0.88)";
          ctx.fillRect(n.x + r + 3, n.y - 7, textWidth + 6, 14);
          ctx.strokeStyle = isStart ? "#10b981" : (isEnd ? "#ef4444" : (n.is_interchange ? "#ffd700" : "rgba(255,255,255,0.2)"));
          ctx.lineWidth = 1;
          ctx.strokeRect(n.x + r + 3, n.y - 7, textWidth + 6, 14);

          ctx.fillStyle = isStart ? "#a7f3d0" : (isEnd ? "#fecaca" : (n.is_interchange ? "#ffd700" : "#ffffff"));
          ctx.fillText(labelText, n.x + r + 6, n.y + 4);
        }
      });

      ctx.restore();
    }

    setupInteraction() {
      let isDown = false;
      let startX, startY;

      this.canvas.addEventListener("mousedown", e => {
        const rect = this.canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left - this.transform.x) / this.transform.k;
        const my = (e.clientY - rect.top - this.transform.y) / this.transform.k;

        // Check if node is clicked
        const clickedNode = this.graphNodes.find(n => {
          const r = getStationRadius(n) + 5;
          return Math.hypot(n.x - mx, n.y - my) <= r;
        });

        if (clickedNode) {
          this.isDragging = true;
          this.draggedNode = clickedNode;
          showStationTooltip(clickedNode);
        } else {
          isDown = true;
          startX = e.clientX - this.transform.x;
          startY = e.clientY - this.transform.y;
          this.canvas.style.cursor = "grabbing";
        }
      });

      window.addEventListener("mousemove", e => {
        if (this.isDragging && this.draggedNode) {
          const rect = this.canvas.getBoundingClientRect();
          this.draggedNode.x = (e.clientX - rect.left - this.transform.x) / this.transform.k;
          this.draggedNode.y = (e.clientY - rect.top - this.transform.y) / this.transform.k;
        } else if (isDown) {
          this.transform.x = e.clientX - startX;
          this.transform.y = e.clientY - startY;
        } else {
          // Hover cursor check
          const rect = this.canvas.getBoundingClientRect();
          const mx = (e.clientX - rect.left - this.transform.x) / this.transform.k;
          const my = (e.clientY - rect.top - this.transform.y) / this.transform.k;
          const hovered = this.graphNodes.find(n => Math.hypot(n.x - mx, n.y - my) <= getStationRadius(n) + 5);
          this.canvas.style.cursor = hovered ? "pointer" : "default";
          if (hovered) showStationTooltip(hovered);
        }
      });

      window.addEventListener("mouseup", () => {
        isDown = false;
        this.isDragging = false;
        this.draggedNode = null;
        this.canvas.style.cursor = "default";
      });

      this.canvas.addEventListener("wheel", e => {
        e.preventDefault();
        const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
        this.transform.k = Math.max(0.4, Math.min(3.5, this.transform.k * zoomFactor));
      });
    }

    reset() {
      this.transform.x = this.canvas.width / 2;
      this.transform.y = this.canvas.height / 2;
      this.transform.k = 1;
      this.buildData();
    }
  }

  let forceGraph = null;

  /* ========================================================
     4. SHORTEST PATH FINDER (DIJKSTRA ALGORITHM)
     ======================================================== */
  function findShortestPath(startId, destId) {
    if (startId === destId) return null;

    const adj = buildAdjacencyList(state.isPhase1Only, state.disruptedStation, state.hypotheticalEdge);
    if (!adj.has(startId) || !adj.has(destId)) return null;

    const dist = new Map();
    const prev = new Map();
    const unvisited = new Set(adj.keys());

    adj.keys().forEach(k => dist.set(k, Infinity));
    dist.set(startId, 0);

    while (unvisited.size > 0) {
      // Pick node with lowest distance
      let curr = null;
      let minD = Infinity;
      unvisited.forEach(u => {
        if (dist.get(u) < minD) {
          minD = dist.get(u);
          curr = u;
        }
      });

      if (!curr || minD === Infinity || curr === destId) break;
      unvisited.delete(curr);

      const neighbors = adj.get(curr) || [];
      neighbors.forEach(edge => {
        if (!unvisited.has(edge.target)) return;

        // Cost function: travel time + interchange penalty (5 mins if changing lines)
        const prevStation = prev.get(curr);
        let transferPenalty = 0;
        if (prevStation) {
          // If transfer
          const currLines = nodeMap.get(curr).lines;
          const targetLines = nodeMap.get(edge.target).lines;
          const common = currLines.filter(l => targetLines.includes(l));
          if (common.length === 0) transferPenalty = 4.0;
        }

        const alt = dist.get(curr) + edge.time + transferPenalty;
        if (alt < dist.get(edge.target)) {
          dist.set(edge.target, alt);
          prev.set(edge.target, { station: curr, line: edge.line, dist: edge.dist, time: edge.time, color: edge.color });
        }
      });
    }

    // Reconstruct Path
    if (!prev.has(destId)) return null;

    const path = [];
    let curr = destId;
    let totalKm = 0;
    let totalMins = 0;

    while (curr && curr !== startId) {
      const step = prev.get(curr);
      if (!step) break;
      path.unshift({
        station: curr,
        line: step.line,
        dist: step.dist,
        time: step.time,
        color: step.color
      });
      totalKm += step.dist;
      totalMins += step.time;
      curr = step.station;
    }

    path.unshift({
      station: startId,
      line: path.length > 0 ? path[0].line : "",
      dist: 0,
      time: 0,
      color: path.length > 0 ? path[0].color : "#ffffff"
    });

    return { path, totalKm, totalMins };
  }

  function renderRouteResult(routeData) {
    const listEl = document.getElementById("itineraryList");
    const timeEl = document.getElementById("routeTimeVal");
    const distEl = document.getElementById("routeDistVal");
    const stopsEl = document.getElementById("routeStopsVal");
    const alertEl = document.getElementById("interchangeAlert");
    const alertText = document.getElementById("interchangeText");

    if (!routeData) {
      timeEl.textContent = "--";
      distEl.textContent = "--";
      stopsEl.textContent = "Unreachable";
      listEl.innerHTML = `<div style="color: #f87171; font-size: 0.8rem; padding: 0.5rem;">No path exists between selected stations (possible network severance).</div>`;
      alertEl.style.display = "none";
      return;
    }

    const { path, totalKm, totalMins } = routeData;
    timeEl.textContent = `${Math.round(totalMins)} mins`;
    distEl.textContent = `${totalKm.toFixed(1)} km`;
    stopsEl.textContent = path.length;

    // Detect Interchanges along path
    const interchanges = [];
    for (let i = 1; i < path.length - 1; i++) {
      const prevLine = path[i - 1].line;
      const nextLine = path[i].line;
      if (prevLine && nextLine && prevLine !== nextLine) {
        interchanges.push({
          station: path[i].station,
          from: prevLine,
          to: nextLine
        });
      }
    }

    if (interchanges.length > 0) {
      alertEl.style.display = "flex";
      alertText.innerHTML = interchanges.map(ic =>
        `Change at <strong>${ic.station}</strong> from <span style="color:var(--purple-line)">${ic.from}</span> to <span style="color:var(--green-line)">${ic.to}</span>.`
      ).join("<br>");
    } else {
      alertEl.style.display = "none";
    }

    // Build itinerary HTML
    listEl.innerHTML = path.map((step, idx) => {
      const isStart = (idx === 0);
      const isEnd = (idx === path.length - 1);
      const isIC = interchanges.some(ic => ic.station === step.station);

      let bulletClass = "purple";
      if (step.line.includes("Green")) bulletClass = "green";
      else if (step.line.includes("Yellow")) bulletClass = "yellow";
      if (isIC) bulletClass = "interchange";

      return `
        <div class="itinerary-step">
          <span class="step-bullet ${bulletClass}"></span>
          <div style="flex: 1;">
            <div style="font-weight: ${isStart || isEnd || isIC ? 'bold' : 'normal'}; color: ${isStart || isEnd ? '#38bdf8' : isIC ? '#f87171' : 'white'};">
              ${step.station} ${isStart ? ' (Origin)' : isEnd ? ' (Destination)' : isIC ? ' [Interchange]' : ''}
            </div>
            ${step.line ? `<div style="font-size: 0.68rem; color: var(--text-dim);">${step.line}</div>` : ''}
          </div>
        </div>
      `;
    }).join("");

    // Highlight route on Leaflet Map with glowing polyline and custom Start/End pins
    if (state.map && state.mapLayers.routeHighlight && state.mapLayers.endpointPins) {
      state.mapLayers.routeHighlight.clearLayers();
      state.mapLayers.endpointPins.clearLayers();

      const latlngs = path.map(p => {
        const n = nodeMap.get(p.station);
        return [n.lat, n.lon];
      });

      // 1. Under-glow polyline
      L.polyline(latlngs, {
        color: "#0284c7",
        weight: 14,
        opacity: 0.45,
        lineCap: "round",
        lineJoin: "round"
      }).addTo(state.mapLayers.routeHighlight);

      // 2. Crisp bright cyan top line
      const highlightLine = L.polyline(latlngs, {
        color: "#38bdf8",
        weight: 6,
        opacity: 1.0,
        lineCap: "round",
        lineJoin: "round"
      }).addTo(state.mapLayers.routeHighlight);

      // 3. Start Station Pin Badge
      const startNode = nodeMap.get(path[0].station);
      if (startNode) {
        const startIcon = L.divIcon({
          className: 'custom-pin-wrap',
          html: `<div class="map-endpoint-pin start">🟢 START: ${startNode.name}</div>`,
          iconAnchor: [0, 0]
        });
        L.marker([startNode.lat, startNode.lon], { icon: startIcon, interactive: false })
          .addTo(state.mapLayers.endpointPins);
      }

      // 4. Destination Station Pin Badge
      const destNode = nodeMap.get(path[path.length - 1].station);
      if (destNode) {
        const destIcon = L.divIcon({
          className: 'custom-pin-wrap',
          html: `<div class="map-endpoint-pin dest">🎯 DESTINATION: ${destNode.name}</div>`,
          iconAnchor: [0, 0]
        });
        L.marker([destNode.lat, destNode.lon], { icon: destIcon, interactive: false })
          .addTo(state.mapLayers.endpointPins);
      }

      // 5. Interchange Pin Badges along journey
      interchanges.forEach(ic => {
        const icNode = nodeMap.get(ic.station);
        if (icNode) {
          const icIcon = L.divIcon({
            className: 'custom-pin-wrap',
            html: `<div class="map-endpoint-pin transfer">🔄 TRANSFER: ${icNode.name}</div>`,
            iconAnchor: [0, 0]
          });
          L.marker([icNode.lat, icNode.lon], { icon: icIcon, interactive: false })
            .addTo(state.mapLayers.endpointPins);
        }
      });

      state.currentRouteBounds = highlightLine.getBounds();
      state.map.fitBounds(state.currentRouteBounds, { padding: [70, 70] });
    }

    state.highlightedPath = path;
    renderMapLayers();
    if (forceGraph) forceGraph.render();

    // Immediately update the live Centrality, Closeness, Betweenness & Station Features HUD
    updateLiveCentralityPanel(path[0].station, path[path.length - 1].station, path);
  }

  function updateLiveCentralityPanel(fromId, toId, path = []) {
    const liveBox = document.getElementById("stationCentralityLiveBox");
    if (!liveBox) return;

    const nFrom = nodeMap.get(fromId);
    const nTo = nodeMap.get(toId);
    if (!nFrom || !nTo) return;

    // Trigger visual pulse animation to alert user of live calculation
    liveBox.classList.remove("flash-update");
    void liveBox.offsetWidth; // trigger browser reflow
    liveBox.classList.add("flash-update");

    // 1. Update Origin Card
    const elFromTitle = document.getElementById("cardFromTitle");
    if (elFromTitle) elFromTitle.textContent = nFrom.name;

    const elFromDeg = document.getElementById("valFromDegree");
    if (elFromDeg) elFromDeg.textContent = `${nFrom.degree} (${nFrom.degree_centrality.toFixed(4)})`;

    const elFromSubDeg = document.getElementById("subFromDegree");
    if (elFromSubDeg) {
      elFromSubDeg.textContent = nFrom.degree >= 3 ? "⭐ Multi-Line Hub" : (nFrom.degree === 1 ? "Terminal Station" : "Corridor Pass-through");
    }

    const barFromDeg = document.getElementById("barFromDegree");
    if (barFromDeg) barFromDeg.style.width = Math.min(100, Math.round((nFrom.degree / 4) * 100)) + "%";

    const elFromClose = document.getElementById("valFromCloseness");
    if (elFromClose) elFromClose.textContent = nFrom.closeness_centrality.toFixed(4);

    const elFromSubClose = document.getElementById("subFromCloseness");
    if (elFromSubClose) {
      elFromSubClose.textContent = nFrom.closeness_centrality >= 0.08 ? "High CBD Access" : (nFrom.closeness_centrality >= 0.05 ? "Intermediate Access" : "Outer Spoke");
    }

    const barFromClose = document.getElementById("barFromCloseness");
    if (barFromClose) barFromClose.style.width = Math.min(100, Math.round((nFrom.closeness_centrality / 0.10) * 100)) + "%";

    const elFromBet = document.getElementById("valFromBetweenness");
    if (elFromBet) elFromBet.textContent = nFrom.betweenness_centrality.toFixed(4);

    const elFromSubBet = document.getElementById("subFromBetweenness");
    if (elFromSubBet) {
      elFromSubBet.textContent = nFrom.betweenness_centrality >= 0.2 ? "Apex Bridge Hub" : (nFrom.betweenness_centrality >= 0.03 ? "Corridor Bridge" : "Local Flow");
    }

    const barFromBet = document.getElementById("barFromBetweenness");
    if (barFromBet) barFromBet.style.width = Math.max(3, Math.min(100, Math.round(nFrom.betweenness_centrality * 100))) + "%";

    const elFromEig = document.getElementById("valFromEigen");
    if (elFromEig) elFromEig.textContent = (nFrom.eigenvector_centrality || 0.0001).toFixed(4);

    const elFromSubEig = document.getElementById("subFromEigen");
    if (elFromSubEig) {
      elFromSubEig.textContent = (nFrom.eigenvector_centrality >= 0.3) ? "👑 Apex Hub Influence" : ((nFrom.eigenvector_centrality >= 0.05) ? "Core Network Influence" : "Peripheral Influence");
    }

    const barFromEig = document.getElementById("barFromEigen");
    if (barFromEig) barFromEig.style.width = Math.max(3, Math.min(100, Math.round(((nFrom.eigenvector_centrality || 0) / 0.58) * 100))) + "%";

    const elFromVuln = document.getElementById("valFromVuln");
    if (elFromVuln) {
      elFromVuln.textContent = nFrom.is_articulation_point ? "Cut Vertex (SPOF)" : "Redundant Loop";
      elFromVuln.className = `cent-mini-val ${nFrom.is_articulation_point ? "vulnerable" : "highlight"}`;
    }

    const barFromV = document.getElementById("barFromVuln");
    if (barFromV) barFromV.style.width = nFrom.is_articulation_point ? "100%" : "20%";

    const pillsFrom = document.getElementById("cardFromLinePills");
    if (pillsFrom) {
      pillsFrom.innerHTML = nFrom.lines.map(l => `<span class="line-badge ${l.toLowerCase().includes('purple') ? 'purple' : l.toLowerCase().includes('green') ? 'green' : 'yellow'}">${l}</span>`).join("");
    }

    // 2. Update Destination Card
    const elToTitle = document.getElementById("cardToTitle");
    if (elToTitle) elToTitle.textContent = nTo.name;

    const elToDeg = document.getElementById("valToDegree");
    if (elToDeg) elToDeg.textContent = `${nTo.degree} (${nTo.degree_centrality.toFixed(4)})`;

    const elToSubDeg = document.getElementById("subToDegree");
    if (elToSubDeg) {
      elToSubDeg.textContent = nTo.degree >= 3 ? "⭐ Multi-Line Hub" : (nTo.degree === 1 ? "Terminal Station" : "Corridor Pass-through");
    }

    const barToDeg = document.getElementById("barToDegree");
    if (barToDeg) barToDeg.style.width = Math.min(100, Math.round((nTo.degree / 4) * 100)) + "%";

    const elToClose = document.getElementById("valToCloseness");
    if (elToClose) elToClose.textContent = nTo.closeness_centrality.toFixed(4);

    const elToSubClose = document.getElementById("subToCloseness");
    if (elToSubClose) {
      elToSubClose.textContent = nTo.closeness_centrality >= 0.08 ? "High CBD Access" : (nTo.closeness_centrality >= 0.05 ? "Intermediate Access" : "Outer Spoke");
    }

    const barToClose = document.getElementById("barToCloseness");
    if (barToClose) barToClose.style.width = Math.min(100, Math.round((nTo.closeness_centrality / 0.10) * 100)) + "%";

    const elToBet = document.getElementById("valToBetweenness");
    if (elToBet) elToBet.textContent = nTo.betweenness_centrality.toFixed(4);

    const elToSubBet = document.getElementById("subToBetweenness");
    if (elToSubBet) {
      elToSubBet.textContent = nTo.betweenness_centrality >= 0.2 ? "Apex Bridge Hub" : (nTo.betweenness_centrality >= 0.03 ? "Corridor Bridge" : "Local Flow");
    }

    const barToBet = document.getElementById("barToBetweenness");
    if (barToBet) barToBet.style.width = Math.max(3, Math.min(100, Math.round(nTo.betweenness_centrality * 100))) + "%";

    const elToEig = document.getElementById("valToEigen");
    if (elToEig) elToEig.textContent = (nTo.eigenvector_centrality || 0.0001).toFixed(4);

    const elToSubEig = document.getElementById("subToEigen");
    if (elToSubEig) {
      elToSubEig.textContent = (nTo.eigenvector_centrality >= 0.3) ? "👑 Apex Hub Influence" : ((nTo.eigenvector_centrality >= 0.05) ? "Core Network Influence" : "Peripheral Influence");
    }

    const barToEig = document.getElementById("barToEigen");
    if (barToEig) barToEig.style.width = Math.max(3, Math.min(100, Math.round(((nTo.eigenvector_centrality || 0) / 0.58) * 100))) + "%";

    const elToVuln = document.getElementById("valToVuln");
    if (elToVuln) {
      elToVuln.textContent = nTo.is_articulation_point ? "Cut Vertex (SPOF)" : "Redundant Loop";
      elToVuln.className = `cent-mini-val ${nTo.is_articulation_point ? "vulnerable" : "highlight"}`;
    }

    const barToV = document.getElementById("barToVuln");
    if (barToV) barToV.style.width = nTo.is_articulation_point ? "100%" : "20%";

    const pillsTo = document.getElementById("cardToLinePills");
    if (pillsTo) {
      pillsTo.innerHTML = nTo.lines.map(l => `<span class="line-badge ${l.toLowerCase().includes('purple') ? 'purple' : l.toLowerCase().includes('green') ? 'green' : 'yellow'}">${l}</span>`).join("");
    }

    // 3. Find Peak Bottleneck along this specific journey path
    let peakStation = nFrom;
    let peakB = nFrom.betweenness_centrality;

    if (path && path.length > 0) {
      path.forEach(step => {
        const stNode = nodeMap.get(step.station);
        if (stNode && stNode.betweenness_centrality > peakB) {
          peakB = stNode.betweenness_centrality;
          peakStation = stNode;
        }
      });
    }

    const elBNeckSt = document.getElementById("textBottleneckStation");
    if (elBNeckSt) elBNeckSt.textContent = peakStation.name;

    const elBNeckScore = document.getElementById("valBottleneckScore");
    if (elBNeckScore) {
      elBNeckScore.textContent = `(Betweenness: ${peakB.toFixed(4)} | ${(peakB * 100).toFixed(1)}% network paths)`;
    }
  }

  /* ========================================================
     5. METRO AUTHORITY TOOLS: LEADERBOARDS & DISRUPTION
     ======================================================== */
  function renderLeaderboard(metric = "betweenness") {
    const tableBody = document.getElementById("rankingTableBody");
    if (!tableBody) return;

    let sorted = [...nodes];
    if (metric === "betweenness") {
      sorted.sort((a, b) => b.betweenness_centrality - a.betweenness_centrality);
    } else if (metric === "degree") {
      sorted.sort((a, b) => b.degree - a.degree);
    } else if (metric === "closeness") {
      sorted.sort((a, b) => b.closeness_centrality - a.closeness_centrality);
    }

    tableBody.innerHTML = sorted.slice(0, 15).map((n, i) => {
      let scoreStr = "";
      if (metric === "betweenness") scoreStr = n.betweenness_centrality.toFixed(4);
      else if (metric === "degree") scoreStr = `${n.degree} (${n.degree_centrality.toFixed(4)})`;
      else scoreStr = n.closeness_centrality.toFixed(4);

      return `
        <tr data-station="${n.id}">
          <td class="rank-badge">${i + 1}</td>
          <td style="font-weight: 600;">${n.name}</td>
          <td style="color: #38bdf8; font-weight: 700;">${scoreStr}</td>
          <td style="font-size: 0.72rem; color: var(--text-dim);">${n.lines.join(", ")}</td>
        </tr>
      `;
    }).join("");

    // Click row to zoom to station
    tableBody.querySelectorAll("tr").forEach(tr => {
      tr.addEventListener("click", () => {
        const stId = tr.getAttribute("data-station");
        const n = nodeMap.get(stId);
        if (n && state.map) {
          state.map.flyTo([n.lat, n.lon], 14, { duration: 1.2 });
          showStationTooltip(n);
        }
      });
    });
  }

  function simulateDisruption(stationId) {
    state.disruptedStation = stationId;

    // Calculate Disconnected Components via BFS
    const adj = buildAdjacencyList(state.isPhase1Only, stationId);
    const visited = new Set();
    const components = [];

    adj.keys().forEach(st => {
      if (!visited.has(st)) {
        const comp = [];
        const queue = [st];
        visited.add(st);

        while (queue.length > 0) {
          const curr = queue.shift();
          comp.push(curr);
          (adj.get(curr) || []).forEach(edge => {
            if (!visited.has(edge.target)) {
              visited.add(edge.target);
              queue.push(edge.target);
            }
          });
        }
        components.push(comp);
      }
    });

    const numComponents = components.length;
    const totalRemaining = nodes.length - 1;
    const largestComp = Math.max(...components.map(c => c.length), 0);
    const severedPct = Math.round((1 - (largestComp / totalRemaining)) * 100);

    // Update UI
    const resultsArea = document.getElementById("disruptionResultsArea");
    resultsArea.style.display = "flex";
    document.getElementById("disruptComponents").textContent = numComponents;
    document.getElementById("disruptIsolated").textContent = `${severedPct}%`;

    const summaryEl = document.getElementById("disruptSummaryText");
    if (stationId === "Nadaprabhu Kempegowda Station Majestic") {
      summaryEl.textContent = `Catastrophic Severance: Disabling Majestic splits Bangalore Metro into 4 isolated corridors. 100% of inter-line trips are halted!`;
    } else {
      summaryEl.textContent = `Station ${stationId} severed. Network split into ${numComponents} isolated segments.`;
    }

    // Re-render map and graph
    renderMapLayers();
    if (forceGraph) forceGraph.buildData();
  }

  function resetDisruption() {
    state.disruptedStation = null;
    const resultsArea = document.getElementById("disruptionResultsArea");
    if (resultsArea) resultsArea.style.display = "none";
    renderMapLayers();
    if (forceGraph) forceGraph.buildData();
  }

  /* ========================================================
     6. URBAN PLANNERS: PROPOSE HYPOTHETICAL LINK
     ======================================================== */
  function testHypotheticalLink(stA, stB) {
    const resultsBox = document.getElementById("newLinkResults");
    if (!resultsBox) return;

    state.hypotheticalEdge = {
      u: stA,
      v: stB,
      dist: 8.5,
      time: 14.0
    };

    resultsBox.style.display = "block";
    renderMapLayers();
    if (forceGraph) forceGraph.buildData();
  }

  /* ========================================================
     7. EVENT LISTENERS & TAB NAVIGATION
     ======================================================== */
  function setupEventListeners() {
    // Stakeholder Tab Switching
    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        const tab = btn.getAttribute("data-tab");
        state.activeTab = tab;

        document.getElementById("viewCommuter").style.display = (tab === "commuter") ? "block" : "none";
        document.getElementById("viewAuthority").style.display = (tab === "authority") ? "block" : "none";
        document.getElementById("viewPlanner").style.display = (tab === "planner") ? "block" : "none";
        document.getElementById("viewResearcher").style.display = (tab === "researcher") ? "block" : "none";
      });
    });

    // View Mode Toggle (Geographic vs Topological Graph)
    const btnGeo = document.getElementById("btnModeGeo");
    const btnGraph = document.getElementById("btnModeGraph");
    const mapEl = document.getElementById("leafletMap");
    const canvasEl = document.getElementById("networkCanvas");
    const canvasControls = document.getElementById("canvasControls");
    const nodeScalingSelectWrap = document.getElementById("nodeScalingSelectWrap");

    btnGeo.addEventListener("click", () => {
      btnGeo.classList.add("active");
      btnGraph.classList.remove("active");
      mapEl.style.display = "block";
      canvasEl.style.display = "none";
      canvasControls.style.display = "none";
      nodeScalingSelectWrap.style.display = "none";
      if (forceGraph) forceGraph.stop();
      if (state.map) state.map.invalidateSize();
    });

    btnGraph.addEventListener("click", () => {
      btnGraph.classList.add("active");
      btnGeo.classList.remove("active");
      mapEl.style.display = "none";
      canvasEl.style.display = "block";
      canvasControls.style.display = "flex";
      nodeScalingSelectWrap.style.display = "flex";
      if (!forceGraph) forceGraph = new ForceGraph("networkCanvas");
      forceGraph.start();
    });

    // Node scale change
    const selectScale = document.getElementById("selectNodeScale");
    if (selectScale) {
      selectScale.addEventListener("change", e => {
        state.selectedNodeScale = e.target.value;
        renderMapLayers();
        if (forceGraph) forceGraph.render();
      });
    }

    // Reset graph controls
    document.getElementById("btnResetGraph").addEventListener("click", () => {
      if (forceGraph) forceGraph.reset();
    });

    document.getElementById("btnFocusMajestic").addEventListener("click", () => {
      const majestic = nodeMap.get("Nadaprabhu Kempegowda Station Majestic");
      if (majestic && state.map) {
        state.map.flyTo([majestic.lat, majestic.lon], 14, { duration: 1.2 });
        showStationTooltip(majestic);
      }
    });

    // Route calculation button
    document.getElementById("btnFindRoute").addEventListener("click", () => {
      triggerAutoRoute();
    });

    // Map Clarity: Toggle Station Labels
    const btnToggleLabels = document.getElementById("btnToggleLabels");
    if (btnToggleLabels) {
      btnToggleLabels.addEventListener("click", () => {
        state.showStationLabels = !state.showStationLabels;
        btnToggleLabels.classList.toggle("active", state.showStationLabels);
        btnToggleLabels.innerHTML = state.showStationLabels ? `<span>🏷️</span> Labels: ON` : `<span>🏷️</span> Labels: OFF`;
        renderMapLayers();
      });
    }

    // Map Clarity: Focus Route (Zoom to Current Journey)
    const btnFitRoute = document.getElementById("btnFitRoute");
    if (btnFitRoute) {
      btnFitRoute.addEventListener("click", () => {
        if (state.currentRouteBounds && state.map) {
          state.map.fitBounds(state.currentRouteBounds, { padding: [70, 70], animate: true, duration: 0.8 });
        } else {
          triggerAutoRoute();
          if (state.currentRouteBounds && state.map) {
            state.map.fitBounds(state.currentRouteBounds, { padding: [70, 70], animate: true, duration: 0.8 });
          }
        }
      });
    }

    // Map Clarity: Line Corridor Visibility Toggles
    document.querySelectorAll("#mapLineToggles .vis-toggle-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const line = chip.getAttribute("data-line");
        if (!line) return;

        if (state.visibleLines.has(line)) {
          if (state.visibleLines.size <= 1) return; // Keep at least one line visible
          state.visibleLines.delete(line);
          chip.classList.remove("active");
          chip.style.opacity = "0.45";
        } else {
          state.visibleLines.add(line);
          chip.classList.add("active");
          chip.style.opacity = "1";
        }

        renderMapLayers();
        if (forceGraph) forceGraph.buildData();
      });
    });

    // Swap From and To button
    const btnSwap = document.getElementById("btnSwapStations");
    if (btnSwap) {
      btnSwap.addEventListener("click", () => {
        const origSel = document.getElementById("selectOrigin");
        const destSel = document.getElementById("selectDest");
        const inputOrig = document.getElementById("inputOriginSearch");
        const inputDest = document.getElementById("inputDestSearch");

        const oldOrig = origSel.value;
        const oldDest = destSel.value;

        origSel.value = oldDest;
        destSel.value = oldOrig;
        if (inputOrig) inputOrig.value = oldDest;
        if (inputDest) inputDest.value = oldOrig;

        updateStationBadges();
        triggerAutoRoute();
      });
    }

    // Auto-update route on select change
    const selOrig = document.getElementById("selectOrigin");
    const selDest = document.getElementById("selectDest");
    const inputOrig = document.getElementById("inputOriginSearch");
    const inputDest = document.getElementById("inputDestSearch");

    if (selOrig) {
      selOrig.addEventListener("change", (e) => {
        if (inputOrig) inputOrig.value = e.target.value;
        updateStationBadges();
        triggerAutoRoute();
      });
    }

    if (selDest) {
      selDest.addEventListener("change", (e) => {
        if (inputDest) inputDest.value = e.target.value;
        updateStationBadges();
        triggerAutoRoute();
      });
    }

    // Search input live autocomplete match
    if (inputOrig) {
      inputOrig.addEventListener("input", (e) => {
        const val = e.target.value.trim().toLowerCase();
        const match = nodes.find(n => n.name.toLowerCase() === val || n.id.toLowerCase() === val);
        if (match) {
          selOrig.value = match.id;
          updateStationBadges();
          triggerAutoRoute();
        }
      });
      inputOrig.addEventListener("change", (e) => {
        const val = e.target.value.trim().toLowerCase();
        const match = nodes.find(n => n.name.toLowerCase().includes(val) || n.id.toLowerCase().includes(val));
        if (match) {
          selOrig.value = match.id;
          inputOrig.value = match.name;
          updateStationBadges();
          triggerAutoRoute();
        }
      });
    }

    if (inputDest) {
      inputDest.addEventListener("input", (e) => {
        const val = e.target.value.trim().toLowerCase();
        const match = nodes.find(n => n.name.toLowerCase() === val || n.id.toLowerCase() === val);
        if (match) {
          selDest.value = match.id;
          updateStationBadges();
          triggerAutoRoute();
        }
      });
      inputDest.addEventListener("change", (e) => {
        const val = e.target.value.trim().toLowerCase();
        const match = nodes.find(n => n.name.toLowerCase().includes(val) || n.id.toLowerCase().includes(val));
        if (match) {
          selDest.value = match.id;
          inputDest.value = match.name;
          updateStationBadges();
          triggerAutoRoute();
        }
      });
    }

    // Line Filter Chips (Filter From/To options by corridor)
    document.querySelectorAll("#lineFilterChips .filter-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        document.querySelectorAll("#lineFilterChips .filter-chip").forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        const filter = chip.getAttribute("data-filter");
        populateDropdowns(filter);
        triggerAutoRoute();
      });
    });

    // Quick commuter chips
    document.querySelectorAll(".route-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const fromSt = chip.getAttribute("data-from");
        const toSt = chip.getAttribute("data-to");
        if (selOrig) selOrig.value = fromSt;
        if (selDest) selDest.value = toSt;
        if (inputOrig) inputOrig.value = fromSt;
        if (inputDest) inputDest.value = toSt;
        updateStationBadges();
        triggerAutoRoute();
      });
    });

    // Metric sorting in Leaderboard
    const selectSort = document.getElementById("selectMetricSort");
    if (selectSort) {
      selectSort.addEventListener("change", e => {
        renderLeaderboard(e.target.value);
      });
    }

    // Disruption Simulator
    document.getElementById("btnSimulateDisruption").addEventListener("click", () => {
      const st = document.getElementById("selectDisruptStation").value;
      simulateDisruption(st);
    });

    document.getElementById("btnResetDisruption").addEventListener("click", () => {
      resetDisruption();
    });

    // Phase 1 / 2 toggle
    document.getElementById("togglePhaseBtn").addEventListener("click", () => {
      state.isPhase1Only = !state.isPhase1Only;
      const statusText = document.getElementById("networkStatusText");
      const btn = document.getElementById("togglePhaseBtn");

      if (state.isPhase1Only) {
        statusText.textContent = "Phase 1 (Purple + Green) Active";
        btn.textContent = "Switch to Phase 2 (with Yellow)";
        document.getElementById("metricStations").textContent = "68";
        document.getElementById("metricDiameter").textContent = "38 Hops";
        document.getElementById("metricAvgPath").textContent = "15.02";
        document.getElementById("metricMajesticB").textContent = "75.3%";
      } else {
        statusText.textContent = "Phase 2 Full Network Active";
        btn.textContent = "Switch to Phase 1 (2 Lines)";
        document.getElementById("metricStations").textContent = "83";
        document.getElementById("metricDiameter").textContent = "44 Hops";
        document.getElementById("metricAvgPath").textContent = "16.68";
        document.getElementById("metricMajesticB").textContent = "73.6%";
      }

      renderMapLayers();
      if (forceGraph) forceGraph.buildData();
    });

    // Hypothetical new link
    document.getElementById("btnTestNewLink").addEventListener("click", () => {
      const stA = document.getElementById("selectNewLinkA").value;
      const stB = document.getElementById("selectNewLinkB").value;
      testHypotheticalLink(stA, stB);
    });

    // Research Plots Lightbox
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImg");
    const modalTitle = document.getElementById("modalTitle");
    const modalClose = document.getElementById("modalClose");

    document.querySelectorAll(".gallery-card").forEach(card => {
      card.addEventListener("click", () => {
        const src = card.getAttribute("data-img");
        const title = card.getAttribute("data-title");
        modalImg.src = src;
        modalTitle.textContent = title;
        modal.classList.add("active");
      });
    });

    modalClose.addEventListener("click", () => modal.classList.remove("active"));
    modal.addEventListener("click", e => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }

  /* ========================================================
     8. APP BOOTSTRAP
     ======================================================== */
  populateDropdowns();
  initLeafletMap();
  renderLeaderboard("betweenness");
  setupEventListeners();

  // Run initial route calculation for default demonstration
  const initialRoute = findShortestPath("Whitefield (Kadugodi)", "Electronic City");
  renderRouteResult(initialRoute);
});
