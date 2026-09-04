# Guide d'annotation — évaluation des métadonnées LLM

## Objectif

Ce jeu d'annotation sert à évaluer la qualité factuelle des métadonnées
produites par le pipeline LLM. Il ne mesure pas la complétude : chaque valeur
prédite doit être confrontée au texte source correspondant.

L'unité d'évaluation est une valeur de champ pour un document. Les 60 documents
sont tirés de façon aléatoire et reproductible, à raison de 10 par source.

## Fichier à annoter

Lancer `Scripts/create_llm_evaluation_sample.py`. Le classeur produit contient :

- `Documents` : le texte source complet et les chemins des fichiers ;
- `Annotations` : une ligne par document et par champ à évaluer.

Dans `Annotations`, remplir uniquement les colonnes **gold_value** et
**judgment** (et, si utile, **notes**). Ne pas modifier `document_id`,
`field` ou `predicted_value`.

## Champs et valeur de référence

Pour `public_vise`, `echelle` et `nature_initiative`, renseigner une valeur de
référence dans `gold_value`, même lorsque le modèle a tort. Utiliser :

- `public_vise` : `ainés`, `ainés et autres`, `professionnels`, `autre` ou
  `public non connu` ;
- `echelle` : une ou plusieurs valeurs séparées par ` | ` parmi `quartier`,
  `communale`, `intercommunale`, `départementale`, `régionale`, `nationale`,
  `internationale` ;
- `nature_initiative` : la nature principale explicitement décrite. Si aucune
  nature n'est identifiable, écrire `ABSENT`.

Pour `territoire`, `porteur_initiative`, `date` et `thematique`, renseigner une
valeur courte de référence lorsque cela est possible. Les thèmes peuvent être
séparés par ` | `. Si l'information n'est pas présente dans le texte, écrire
`ABSENT`.

## Jugement de la prédiction

Choisir exactement l'une de ces valeurs :

- `correct` : la valeur est exacte et explicitement soutenue par le texte ;
- `partiel` : la valeur est globalement justifiée mais incomplète, trop vague
  ou contient un élément discutable ;
- `incorrect` : la valeur est erronée, non justifiée ou inventée ;
- `absence_correcte` : le modèle ne fournit pas de valeur et le texte ne permet
  pas d'en fournir une ;
- `non_evaluable` : le texte est trop dégradé ou ambigu pour conclure.

Une information seulement « fortement implicite » ne doit être considérée
correcte que si un lecteur indépendant peut raisonnablement parvenir à la même
conclusion à partir du texte. En cas de doute, préférer `partiel` et expliquer
le cas dans `notes`.

## Contrôle de reproductibilité et accord

Conserver le classeur annoté sous un nouveau nom, par exemple
`Evaluation/llm_annotations_reviewer1.xlsx`. Si possible, faire annoter au
moins 15 des 60 mêmes documents par une seconde personne, sans lui montrer vos
annotations. L'accord inter-annotateur peut alors être calculé sur les trois
champs catégoriels et sur le jugement binaire « correct / non correct ».

## Résultats à rapporter dans le mémoire

Pour les trois champs catégoriels, rapporter par champ la précision, le rappel,
le F1 micro et la proportion de correspondances exactes. Pour les quatre autres
champs, rapporter la part de jugements `correct` ou `absence_correcte`, les
parts `partiel` et `incorrect`, et le nombre de cas non évaluables. Toujours
indiquer la taille de l'échantillon, son tirage stratifié, le modèle, le prompt
et la date d'exécution.
