const detailRoot = document.querySelector("#initiative-detail");
const initiativeId = Number(new URLSearchParams(window.location.search).get("id"));
const initiative = window.initiativesData.find((item) => item.id === initiativeId);

const labels = {
  description_generale: "Description générale",
  contexte: "Contexte",
  problematique: "Problématique",
  solution_envisagee: "Solution envisagée",
  objectifs: "Objectifs"
};

const escapeHtml = (value) => String(value || "").replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
const list = (items, fallback = "Non renseigné") => items?.length ? items.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("") : `<span class="detail-empty">${fallback}</span>`;
const text = (value) => value ? escapeHtml(value) : "Non renseigné";

if (!initiative) {
  detailRoot.innerHTML = `
    <section class="not-found">
      <p class="eyebrow">Annuaire SIAGE</p>
      <h1>Initiative introuvable</h1>
      <p>Cette fiche n’existe pas ou n’est plus disponible.</p>
      <a class="back-link" href="index.html">← Retour à l’annuaire</a>
    </section>`;
} else {
  document.title = `${initiative.title} — Chaire SIAGE`;
  detailRoot.innerHTML = `
    <a class="back-link" href="index.html">← Retour à l’annuaire</a>
    <article class="detail-layout">
      <div class="detail-main">
        <div class="detail-illustration illustration-${escapeHtml(initiative.category)}" aria-hidden="true"></div>
        <p class="eyebrow">${escapeHtml(initiative.source || "Initiative")}</p>
        <h1>${escapeHtml(initiative.title)}</h1>
        <div class="detail-content">
          <section class="detail-section">
            <h2>Texte intégral de la source</h2>
            <p class="full-text" id="full-text">Chargement du texte intégral…</p>
          </section>
        </div>
      </div>
      <aside class="detail-aside" aria-label="Informations pratiques">
        <h2>Informations clés</h2>
        <dl>
          <div><dt>Catégories</dt><dd class="category-list">${list(initiative.themes)}</dd></div>
          <div><dt>Territoire</dt><dd>${text(initiative.territory)}</dd></div>
          <div><dt>Échelle</dt><dd>${list(initiative.scales)}</dd></div>
          <div><dt>Public visé</dt><dd>${text(initiative.audience)}</dd></div>
          <div><dt>Porteur de l’initiative</dt><dd>${text(initiative.organization)}</dd></div>
          <div><dt>Période</dt><dd>${list(initiative.dates)}</dd></div>
          <div><dt>Source</dt><dd>${text(initiative.source)}</dd></div>
        </dl>
      </aside>
    </article>`;
  loadFullText(initiative);
}

function loadFullText(item) {
  const target = document.querySelector("#full-text");
  const fallback = Object.values(item.description || {}).filter(Boolean).join("\n\n") || item.audience || "Texte non disponible.";
  window.initiativeFullText = "";
  const script = document.createElement("script");
  script.src = `assets/texts/${item.id}.js`;
  script.onload = () => { target.textContent = window.initiativeFullText || fallback; };
  script.onerror = () => { target.textContent = fallback; };
  document.head.append(script);
}
