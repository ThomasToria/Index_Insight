const initiatives = window.initiativesData;

const categoryLabels = {
  autonomie: "Autonomie", sante: "Santé", "lien-social": "Lien social", habitat: "Habitat", inclusion: "Inclusion", mobilite: "Mobilité", numerique: "Numérique", aidants: "Aidants", vieillissement: "Vieillissement"
};

const grid = document.querySelector("#initiative-grid");
const template = document.querySelector("#initiative-card-template");
const searchInput = document.querySelector("#initiative-search");
const territoryFilter = document.querySelector("#territory-filter");
const statusFilter = document.querySelector("#status-filter");
const sortSelect = document.querySelector("#sort-select");
const resultCount = document.querySelector("#result-count");
const emptyState = document.querySelector("#empty-state");
const loadMore = document.querySelector("#load-more");
const filterPanel = document.querySelector("#filter-panel");
const filterToggle = document.querySelector("#filter-toggle");
const mapSvg = document.querySelector("#france-map");
const mapTooltip = document.querySelector("#map-tooltip");
const mapTotal = document.querySelector("#map-total");
const mapDialog = document.querySelector("#map-dialog");
const expandedMapSvg = document.querySelector("#france-map-expanded");
const expandedMapTooltip = document.querySelector("#expanded-map-tooltip");
let mapZoom = null;
let visibleCount = 12;

const normalise = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const shorten = (value, max = 180) => value && value.length > max ? `${value.slice(0, max).trimEnd()}…` : value;
const descriptionText = (initiative) => Object.values(initiative.description || {}).filter(Boolean).join(" ");
const summaryFor = (initiative) => shorten(initiative.description?.description_generale || initiative.description?.objectifs || initiative.audience || "Description à consulter dans la fiche détaillée.");
const yearFor = (initiative) => Number((initiative.dates || []).join(" ").match(/20\d{2}|19\d{2}/)?.[0] || 0);
const territoryFor = (initiative) => initiative.city || initiative.scales?.[0] || "Territoire non précisé";

Object.entries(categoryLabels).forEach(([value, label]) => {
  const option = document.createElement("label");
  option.innerHTML = `<input type="checkbox" value="${value}"><span>${label}</span>`;
  document.querySelector("#theme-options").append(option);
});

[...new Set(initiatives.map((initiative) => initiative.city).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fr")).forEach((city) => {
  territoryFilter.add(new Option(city, city));
});

[...new Set(initiatives.map((initiative) => initiative.source).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fr")).forEach((source) => {
  statusFilter.add(new Option(source, source));
});

const query = new URLSearchParams(window.location.search);
const queryTheme = query.get("theme");
const queryCity = query.get("city");
if (queryTheme) {
  const themeInput = document.querySelector(`#theme-options input[value="${CSS.escape(queryTheme)}"]`);
  if (themeInput) themeInput.checked = true;
}
if (queryCity && [...territoryFilter.options].some((option) => option.value === queryCity)) territoryFilter.value = queryCity;

function filteredInitiatives() {
  const search = normalise(searchInput.value.trim());
  const chosenThemes = [...document.querySelectorAll("#theme-options input:checked")].map((input) => input.value);
  let results = initiatives.filter((initiative) => {
    const searchable = normalise([initiative.title, initiative.territory, initiative.audience, initiative.organization, initiative.source, ...initiative.themes, descriptionText(initiative)].join(" "));
    const themeMatches = !chosenThemes.length || chosenThemes.some((key) => initiative.themes.some((theme) => normalise(theme) === normalise(categoryLabels[key])));
    return (!search || searchable.includes(search)) && (!territoryFilter.value || initiative.city === territoryFilter.value) && (!statusFilter.value || initiative.source === statusFilter.value) && themeMatches;
  });
  if (sortSelect.value === "recent") results.sort((a, b) => yearFor(b) - yearFor(a));
  if (sortSelect.value === "alpha") results.sort((a, b) => a.title.localeCompare(b.title, "fr"));
  return results;
}

function render() {
  const results = filteredInitiatives();
  const shown = results.slice(0, visibleCount);
  grid.replaceChildren();
  shown.forEach((initiative) => {
    const card = template.content.cloneNode(true);
    const illustration = card.querySelector(".card-illustration");
    illustration.classList.add(`illustration-${initiative.category}`);
    card.querySelector("h2").textContent = initiative.title;
    card.querySelector(".summary").textContent = summaryFor(initiative);
    card.querySelector(".place").textContent = territoryFor(initiative);
    const status = card.querySelector(".status");
    status.lastElementChild.textContent = initiative.source || "SIAGE";
    initiative.themes.slice(0, 2).forEach((tag) => {
      const tagElement = document.createElement("span");
      tagElement.className = "tag";
      tagElement.textContent = tag;
      card.querySelector(".tags").append(tagElement);
    });
    const cardElement = card.querySelector(".initiative-card");
    cardElement.setAttribute("role", "link");
    cardElement.setAttribute("tabindex", "0");
    const openDetail = () => { window.location.href = `initiative.html?id=${initiative.id}`; };
    cardElement.addEventListener("click", openDetail);
    cardElement.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openDetail(); } });
    grid.append(card);
  });
  resultCount.textContent = results.length === initiatives.length ? `${new Intl.NumberFormat("fr-FR").format(initiatives.length)} initiatives` : `${results.length} initiative${results.length > 1 ? "s" : ""} trouvée${results.length > 1 ? "s" : ""}`;
  emptyState.hidden = results.length !== 0;
  loadMore.hidden = !results.length || visibleCount >= results.length;
  renderMap(results);
}

function renderMap(results) {
  drawMap(mapSvg, mapTooltip, results, { width: 340, height: 286, expanded: false });
  const localized = results.filter((initiative) => initiative.coordinates).length;
  mapTotal.textContent = `${localized} localisées`;
}

function drawMap(svg, tooltip, results, { width, height, expanded }) {
  const metropolitanRegions = window.franceRegions.features.filter((feature) => Number(feature.properties.code) >= 11 && Number(feature.properties.code) <= 94);
  const featureCollection = { type: "FeatureCollection", features: metropolitanRegions };
  const projection = d3.geoConicConformal().parallels([44, 49]).rotate([0, 0]).fitSize([width, height], featureCollection);
  const path = d3.geoPath(projection);
  const byCity = results.filter((initiative) => initiative.coordinates).reduce((groups, initiative) => {
    (groups[initiative.city] ??= []).push(initiative);
    return groups;
  }, {});

  svg.replaceChildren();
  const mapLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  mapLayer.classList.add("map-layer");
  svg.append(mapLayer);
  metropolitanRegions.forEach((feature) => {
    const region = document.createElementNS("http://www.w3.org/2000/svg", "path");
    region.setAttribute("class", "region");
    region.setAttribute("d", path(feature));
    mapLayer.append(region);
  });

  Object.entries(byCity).forEach(([city, items]) => {
    const [x, y] = projection(items[0].coordinates);
    const point = document.createElementNS("http://www.w3.org/2000/svg", "g");
    point.setAttribute("class", "map-point");
    point.setAttribute("role", "button");
    point.setAttribute("tabindex", "0");
    point.setAttribute("aria-label", `${city} : ${items.length} initiative${items.length > 1 ? "s" : ""}`);
    point.setAttribute("transform", `translate(${x},${y})`);
    point.innerHTML = `<circle class="point-ring" r="9"></circle><circle class="point-dot" r="6"></circle>${items.length > 1 ? `<text class="point-count" y=".5">${items.length}</text>` : ""}`;
    const showTooltip = () => {
      tooltip.textContent = `${city} · ${items.length} initiative${items.length > 1 ? "s" : ""}`;
      tooltip.hidden = false;
      tooltip.style.left = `${Math.min(width - 150, Math.max(8, x - 45))}px`;
      tooltip.style.top = `${Math.max(0, y - 34)}px`;
    };
    const hideTooltip = () => { tooltip.hidden = true; };
    const applyTerritory = (event) => { event?.stopPropagation(); searchInput.value = city; visibleCount = 12; if (mapDialog.open) mapDialog.close(); render(); };
    point.addEventListener("mouseenter", showTooltip);
    point.addEventListener("mouseleave", hideTooltip);
    point.addEventListener("focus", showTooltip);
    point.addEventListener("blur", hideTooltip);
    point.addEventListener("click", applyTerritory);
    point.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); applyTerritory(event); } });
    mapLayer.append(point);
  });
  const zoomBehavior = d3.zoom().scaleExtent([1, 8]).on("zoom", (event) => {
    mapLayer.setAttribute("transform", event.transform);
  });
  const selection = d3.select(svg).call(zoomBehavior).on("dblclick.zoom", null);
  if (expanded) mapZoom = { selection, zoomBehavior };
  if (!expanded) {
    svg.onclick = (event) => {
      if (!event.target.closest(".map-point")) openExpandedMap();
    };
  }
}

function openExpandedMap() {
  drawMap(expandedMapSvg, expandedMapTooltip, filteredInitiatives(), { width: 720, height: 490, expanded: true });
  mapDialog.showModal();
}

function resetFilters() {
  searchInput.value = "";
  territoryFilter.value = "";
  statusFilter.value = "";
  sortSelect.value = "relevance";
  document.querySelectorAll("#theme-options input").forEach((input) => { input.checked = false; });
  visibleCount = 12;
  render();
}

function onFilterChange() { visibleCount = 12; render(); }
[searchInput, territoryFilter, statusFilter, sortSelect].forEach((element) => element.addEventListener(element === searchInput ? "input" : "change", onFilterChange));
document.querySelector("#theme-options").addEventListener("change", onFilterChange);
document.querySelector("#reset-filters").addEventListener("click", resetFilters);
document.querySelectorAll("[data-action='open-filter']").forEach((button) => button.addEventListener("click", () => { filterPanel.hidden = false; filterToggle.setAttribute("aria-expanded", "true"); filterPanel.scrollIntoView({ behavior: "smooth", block: "nearest" }); }));
filterToggle.addEventListener("click", () => { filterPanel.hidden = !filterPanel.hidden; filterToggle.setAttribute("aria-expanded", String(!filterPanel.hidden)); });
loadMore.addEventListener("click", () => { visibleCount += 12; render(); });
document.querySelector("#map-close").addEventListener("click", () => mapDialog.close());
document.querySelector("#zoom-in").addEventListener("click", () => mapZoom?.selection.transition().duration(180).call(mapZoom.zoomBehavior.scaleBy, 1.5));
document.querySelector("#zoom-out").addEventListener("click", () => mapZoom?.selection.transition().duration(180).call(mapZoom.zoomBehavior.scaleBy, 1 / 1.5));
document.querySelector("#zoom-reset").addEventListener("click", () => mapZoom?.selection.transition().duration(180).call(mapZoom.zoomBehavior.transform, d3.zoomIdentity));
render();
