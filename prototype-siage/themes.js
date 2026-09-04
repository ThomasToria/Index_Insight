const themes = {
  autonomie: "Autonomie", sante: "Santé", "lien-social": "Lien social", habitat: "Habitat", inclusion: "Inclusion", mobilite: "Mobilité", numerique: "Numérique", aidants: "Aidants", vieillissement: "Vieillissement"
};
const themeDirectory = document.querySelector("#theme-directory");
Object.entries(themes).forEach(([key, label]) => {
  const count = window.initiativesData.filter((initiative) => initiative.themes.some((theme) => theme.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase() === label.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase())).length;
  const link = document.createElement("a");
  link.className = "theme-tile";
  link.href = `index.html?theme=${encodeURIComponent(key)}`;
  link.innerHTML = `<div class="theme-tile-image illustration-${key}" aria-hidden="true"></div><div><h2>${label}</h2><p>${new Intl.NumberFormat("fr-FR").format(count)} initiatives</p><span>Explorer →</span></div>`;
  themeDirectory.append(link);
});
