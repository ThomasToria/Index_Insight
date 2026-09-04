# Dictionnaire de données — `LLM_Tagged_Database`

Chaque fichier de la base principale est un objet JSON. Les valeurs sont en français, car le corpus et l'index cible sont francophones.

## Champs d'extraction

| Champ | Type attendu | Description | Exemple |
|---|---|---|---|
| `titre` | texte | Titre de la ressource ou de l'initiative. | `ATELIER « HABITAT : LES CLEFS DE MA SANTÉ »` |
| `territoire` | texte ou liste | Territoire concerné lorsqu'il est identifiable. | `['Gironde', 'Landes']` |
| `echelle` | liste | Échelle territoriale. | `['départementale', 'régionale']` |
| `public_vise` | texte | Public principal issu du prompt. | `ainés` |
| `nature_initiative` | texte | Type d'initiative brut proposé par le LLM. | `atelier` |
| `description` | objet | Sous-champs descriptifs ci-dessous. | objet JSON |
| `porteur_initiative` | texte | Structure porteuse. | `Caisse nationale de l'Assurance retraite` |
| `date` | liste | Date ou période explicitement associée à l'initiative. | `['2023']` |
| `thematique` | liste | Thèmes bruts issus de l'extraction. | `['santé et prévention']` |
| `source_site` | texte | Source documentaire. | `CNAV` |

## Sous-champs de `description`

| Sous-champ | Description |
|---|---|
| `description_generale` | Présentation factuelle de l'initiative. |
| `contexte` | Contexte explicite de mise en œuvre. |
| `problematique` | Besoin ou enjeu identifié dans le document. |
| `solution_envisagee` | Réponse ou action proposée. |
| `objectifs` | Finalités explicites. |

Une valeur vide indique une absence, une ambiguïté ou une information non déductible de façon fiable dans le document. Elle ne signifie pas nécessairement que l'information n'existe pas dans le monde réel.

## Normalisation et provenance

| Champ | Type | Rôle |
|---|---|---|
| `thematique_normalisee` | liste | Thèmes contrôlés pour filtres et statistiques. |
| `nature_initiative_normalisee` | texte | Nature contrôlée unique. |
| `version_taxonomie` | texte | Version appliquée, actuellement `v1.0`. |
| `source_url` | URL | Adresse de la page ou du document d'origine. |
| `original_title` | texte | Titre tel que collecté. |
| `collection_date` | date ISO | Date de collecte ; incomplète dans l'état actuel. |
| `fichier_source` | chemin | Fichier texte utilisé pour l'extraction. |
| `nom_fichier` | texte | Nom local de la ressource. |
| `statut_action` | texte | Statut de l'action lorsqu'il est disponible. |

Pour les filtres et statistiques, privilégier les champs normalisés. Pour tout usage public, conserver `source_url`, `original_title`, `collection_date` et `source_site` afin d'assurer attribution et vérifiabilité.
