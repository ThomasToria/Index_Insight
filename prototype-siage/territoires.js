const records = window.initiativesData.filter((initiative) => initiative.city && initiative.coordinates);
const grouped = records.reduce((groups, initiative) => { (groups[initiative.city] ??= []).push(initiative); return groups; }, {});
const fmt = new Intl.NumberFormat("fr-FR");
document.querySelector("#localized-count").textContent = fmt.format(records.length);
document.querySelector("#city-count").textContent = `${Object.keys(grouped).length} territoires repérés`;

const list = document.querySelector("#territory-list");
Object.entries(grouped).sort(([, a], [, b]) => b.length - a.length || a[0].city.localeCompare(b[0].city, "fr")).forEach(([city, initiatives]) => {
  const link = document.createElement("a");
  link.href = `index.html?city=${encodeURIComponent(city)}`;
  link.innerHTML = `<span>${city}</span><strong>${initiatives.length}</strong><small>initiative${initiatives.length > 1 ? "s" : ""} →</small>`;
  list.append(link);
});

const svg = document.querySelector("#territories-map");
const regions = window.franceRegions.features.filter((feature) => Number(feature.properties.code) >= 11 && Number(feature.properties.code) <= 94);
const featureCollection = { type: "FeatureCollection", features: regions };
const projection = d3.geoConicConformal().parallels([44, 49]).rotate([0, 0]).fitSize([720, 520], featureCollection);
const path = d3.geoPath(projection);
const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
svg.append(layer);
regions.forEach((feature) => { const node = document.createElementNS("http://www.w3.org/2000/svg", "path"); node.setAttribute("class", "region"); node.setAttribute("d", path(feature)); layer.append(node); });
Object.entries(grouped).forEach(([city, initiatives]) => {
  const [x, y] = projection(initiatives[0].coordinates);
  const point = document.createElementNS("http://www.w3.org/2000/svg", "g");
  point.setAttribute("class", "map-point"); point.setAttribute("role", "link"); point.setAttribute("tabindex", "0"); point.setAttribute("aria-label", `${city}, ${initiatives.length} initiatives`); point.setAttribute("transform", `translate(${x},${y})`);
  point.innerHTML = `<circle class="point-ring" r="11"></circle><circle class="point-dot" r="7"></circle><text class="point-count" y=".5">${initiatives.length}</text>`;
  const open = () => { window.location.href = `index.html?city=${encodeURIComponent(city)}`; };
  point.addEventListener("click", open); point.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } });
  layer.append(point);
});
d3.select(svg).call(d3.zoom().scaleExtent([1, 8]).on("zoom", (event) => layer.setAttribute("transform", event.transform)));
