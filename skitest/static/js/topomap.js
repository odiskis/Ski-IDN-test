// topomap.js
// Zoomable topo map viewer built on Leaflet, using real EPSG:25833 (UTM33N)
// coordinates directly as the map's coordinate system -- no lat/lon
// reprojection, so a marker at [northing, easting] lands exactly where
// it should relative to the Unity terrain (same source coordinates).
//
// Requires Leaflet (CSS + JS) to already be loaded on the page.
//
// Usage:
//   initTopoMap('map-topp', MAPS_META_URL, MAPS_IMG_BASE, [
//     { label: 'Topp', easting: 123209.04, northing: 6841950.12, color: '#C0392B' }
//   ]);

function initTopoMap(containerId, metadataUrl, imageBaseUrl, markers, circles) {
  fetch(metadataUrl)
    .then(r => r.json())
    .then(meta => buildTopoMap(containerId, meta, imageBaseUrl, markers || [], circles || []))
    .catch(err => {
      console.error('Kunne ikke laste kartmetadata:', err);
      const el = document.getElementById(containerId);
      if (el) el.innerHTML = '<p style="padding:20px;color:#900;">Kartet kunne ikke lastes.</p>';
    });
}

function buildTopoMap(containerId, meta, imageBaseUrl, markers, circles) {
  // meta.levels is expected in overview -> most-zoomed order, matching
  // the output of generate_topo_maps.py (01_overview ... 04_zoom).
  const levels = meta.levels;

  const boundsFor = (lvl) => L.latLngBounds(
    [lvl.bbox.ymin, lvl.bbox.xmin],
    [lvl.bbox.ymax, lvl.bbox.xmax]
  );

  const map = L.map(containerId, {
    crs: L.CRS.Simple,
    zoomSnap: 1,
    zoomDelta: 1,
    minZoom: -10,
    attributionControl: false,
  });
  map.invalidateSize();

  // Fit to the overview level first to establish a sensible base zoom
  // for the current container size.
  const overviewBounds = boundsFor(levels[0]);
  map.fitBounds(overviewBounds, { animate: false }); // Fit to overview level first to establish base zoom
  const baseZoom = map.getZoom();

  map.setMinZoom(baseZoom);
  map.setMaxZoom(baseZoom + levels.length - 1);
  
  const extentM = overviewBounds.getEast() - overviewBounds.getWest();
  const tightPx = Math.round(extentM * Math.pow(2, baseZoom));
  const containerEl = document.getElementById(containerId);
  containerEl.style.width = tightPx + 'px';
  containerEl.style.height = tightPx + 'px';
  containerEl.style.margin = '0 auto';
  map.invalidateSize();

  let currentBase = null;
  let currentSteepness = null;
  let steepnessOn = false;

  function levelIndexForZoom(zoom) {
    const idx = zoom - baseZoom;
    return Math.max(0, Math.min(levels.length - 1, idx));
  }

  function showLevel(levelIndex) {
    const lvl = levels[levelIndex];
    const bounds = boundsFor(lvl);

    if (currentBase) map.removeLayer(currentBase);
    if (currentSteepness) map.removeLayer(currentSteepness);

    currentBase = L.imageOverlay(`${imageBaseUrl}/${lvl.label}_base.png`, bounds);
    currentBase.addTo(map);

    currentSteepness = L.imageOverlay(`${imageBaseUrl}/${lvl.label}_steepness.png`, bounds, {
      opacity: steepnessOn ? 0.5 : 0,
    });
    currentSteepness.addTo(map);
  }

  showLevel(0);

  map.on('zoomend', () => {
    showLevel(levelIndexForZoom(map.getZoom()));
  });

  // Steepness toggle control (top-right corner of the map)
  const ToggleControl = L.Control.extend({
    options: { position: 'topright' },
    onAdd: function () {
      const div = L.DomUtil.create('div');
      div.style.background = 'white';
      div.style.padding = '6px 10px';
      div.style.borderRadius = '8px';
      div.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)';
      div.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
      div.style.fontSize = '0.85rem';
      div.innerHTML = `<label style="display:flex;align-items:center;gap:6px;cursor:pointer;margin:0;">
        <input type="checkbox" id="${containerId}-steepness-cb"> Bratthet
      </label>`;
      L.DomEvent.disableClickPropagation(div);
      return div;
    },
  });
  map.addControl(new ToggleControl());

  document.getElementById(`${containerId}-steepness-cb`).addEventListener('change', (e) => {
    steepnessOn = e.target.checked;
    if (currentSteepness) currentSteepness.setOpacity(steepnessOn ? 0.5 : 0);
  });

  // Markers, placed by real UTM coordinates
  markers.forEach(m => {
    if (m.easting == null || m.northing == null) return;
    const marker = L.circleMarker([m.northing, m.easting], {
      radius: m.radius || 8,
      color: 'white',
      weight: 3,
      fillColor: m.color || '#C0392B',
      fillOpacity: m.fillOpacity != null ? m.fillOpacity : 1,
    }).addTo(map);
    if (m.label) {
      marker.bindTooltip(m.label, {
        permanent: true,
        direction: 'top',
        offset: [0, -10],
        className: 'topomap-label',
      });
    }
  });

  // Circles — e.g. precision boundaries around a target. Radius in meters
  // matches directly since CRS.Simple here uses raw UTM meter units.
  (circles || []).forEach(c => {
    if (c.easting == null || c.northing == null) return;
    L.circle([c.northing, c.easting], {
      radius: c.radius,
      color: c.color || '#1A3C5E',
      weight: c.weight || 1.5,
      fill: false,
      dashArray: c.dashArray || '5,5',
    }).addTo(map);
  });

  return map;
}
