# Taux souverains à 10 ans — sources officielles

Registre vérifié le 6 octobre 2026. Le fichier `10y.json` alimente l’onglet Taux d’emprunt de Visactu. Les rendements sont exprimés en %, sans changement d’échelle.

| Pays | Source et identifiant | Fréquence des observations retenues |
| --- | --- | --- |
| France | Euronext, TEC 10, rediffusé par Webstat — `FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA` | Quotidienne, jours cotés |
| Allemagne | Deutsche Bundesbank — `BBSSY.D.REN.EUR.A630.000000WT1010.A` | Quotidienne, jours cotés |
| Italie | Banque de France, Webstat — `FM.M.IT.EUR.FR2.BB.IT10YT_RR.YLD` | Moyenne mensuelle |
| Espagne | Banco de España, tableau TI_1_3 — `D_G0B1F0ZP` | Quotidienne, jours cotés |
| Portugal | Banque de France, Webstat — `FM.M.PT.EUR.FR2.BB.PT10YT_RR.YLD` | Moyenne mensuelle |
| Grèce | Banque de Grèce, Greek government securities, colonne 10 years / Yield (%) | Quotidienne, jours cotés |
| Belgique | Banque nationale de Belgique — `BE2:DF_IROLOBE2(1.0)/D.10Y.F` | Quotidienne, jours cotés |

Les URL exactes sont conservées dans `scripts/sovereign_yields.py`, dans `SOURCES`, et reproduites dans le JSON. Les trois séries Webstat sont diffusées par la Banque de France. La source du TEC 10 français est Euronext (`EUXT`). Les séries concernant l’Italie et le Portugal ne doivent pas être attribuées directement à leurs banques centrales nationales.

## Actualisation

Le workflow `sovereign-yields.yml` vérifie les sept sources chaque jour du lundi au vendredi à 19 h 43 UTC (21 h 43 à Paris en été, 20 h 43 en hiver). La planification GitHub peut être retardée. Une vérification quotidienne des séries mensuelles permet d’intégrer une publication ou une révision dès sa disponibilité ; elle ne transforme pas la moyenne mensuelle en taux quotidien. Le workflow peut aussi être déclenché manuellement depuis Actions.

Le site relit le JSON à l’ouverture de l’onglet, à chaque changement de période et toutes les heures tant que l’onglet est monté. Le processus de collecte fonctionne indépendamment des visiteurs, sans clé ni secret externe. Il nécessite les GitHub Actions activées et la permission `contents: write` du jeton du workflow.

## Dates, erreurs et comparabilité

- `fetchedAt` : date de la collecte, jamais date du taux.
- `checkedAt` : dernière tentative par source ; `lastSuccessAt` : dernier succès.
- `lastObservation` : dernière date ou mois publié par la source.
- `status=error` : échec de lecture/validation ; le dernier historique valide est conservé.
- `status=stale` : dernier taux quotidien âgé de plus de 10 jours calendaires, ou début du dernier mois observé de plus de 75 jours. Ces seuils sont des alertes, pas une promesse de publication.
- Une régression de la date la plus récente est refusée. Les révisions de valeurs sont acceptées. Les valeurs manquantes ne deviennent jamais des zéros. Les rendements négatifs sont autorisés.
- En cas d’incident partiel, le JSON est publié avec l’état de chaque source avant que le workflow soit marqué en échec. Les autres pays continuent à être actualisés.
- Aucun historique quotidien n’est fusionné avec une série mensuelle. Le tableau grec fournit les 30 dernières séances ; l’historique est accumulé à partir de la mise en service. Les autres historiques sont limités à six ans pour permettre un affichage de cinq ans.
- La France utilise depuis le 6 octobre 2026 le TEC 10 quotidien ; l’historique mensuel a été remplacé intégralement, sans interpolation de points quotidiens. Le TEC 10 est un rendement à échéance constante de 10 ans, distinct du rendement de l’emprunt phare précédemment utilisé.
- Les écarts avec l’Allemagne ne sont affichés qu’à date ET fréquence identiques. Les classements globaux sont masqués lorsque les dates diffèrent. La Belgique utilise une durée résiduelle fixe ; les définitions nationales ne sont pas parfaitement harmonisées.
- Sur l’axe du graphique, une moyenne mensuelle est positionnée à la fin de son mois. Sa date reste libellée comme un mois et non comme une cotation journalière.
- Si le JSON ne peut pas être chargé, le site utilise explicitement les moyennes mensuelles Eurostat du proxy existant, avec leurs dates et un message de secours.

## France : TEC 10 quotidien

La source affichée est **Euronext**. Les données sont récupérées depuis l’export officiel Webstat et actualisées les jours ouvrés. Documentation du taux : https://www.aft.gouv.fr/fr/oat-tec-10 .

## Autres sources et choix méthodologiques

- **Italie** : l’export officiel Banque d’Italie `BMK0200`, série `MFN_BMK.D.020.922.0.EUR.210`, comporte des observations quotidiennes mais s’arrêtait au 31 août 2026 lors de la vérification. La série mensuelle Webstat était déjà disponible pour septembre. Export documenté : https://a2a.bancaditalia.it/infostat/dataservices/export/EN/CSV/ALL/CUBE/BANKITALIA/DIFF/BMK0200 . Ne pas confondre fréquence des observations et délai de diffusion.
- **Portugal** : le tableau BPstat 484 publie des moyennes mensuelles ; son API n’a pas pu être validée depuis l’environnement de mise en place (HTTP 403). Utilisation du flux officiel Webstat vérifié, sans identifiant BPstat supposé.
- **Eurostat** : `irt_lt_mcby_m`, mensuel, conservé en secours. L’API existante était encore à août lors de la vérification.
- **Webstat** : utilisation des exports CSV publics du catalogue actuel ; pas de dépendance à l’ancienne API `/api/v2.1/series/.../observations` ni à une clé privée.

## Vérification / exploitation

```sh
python -m unittest discover -s scripts -p 'test_sovereign_yields.py'
python scripts/sovereign_yields.py
```

Les fixtures sont de petits extraits des fichiers officiels recueillis le 4 octobre 2026. En cas d’alerte, consulter `countries` dans le JSON et le journal Actions. Corriger le parseur si le format officiel a changé, puis relancer. Le fichier existant doit rester en place pour conserver les dernières valeurs et l’historique grec.

