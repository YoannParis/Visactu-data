# Taux souverains à 10 ans — sources officielles

Registre vérifié le 6 octobre 2026. Le fichier `10y.json` alimente l’onglet Taux d’emprunt de Visactu. Les rendements sont exprimés en %, sans changement d’échelle.

| Pays | Source et identifiant | Fréquence des observations retenues |
| --- | --- | --- |
| France | Euronext, TEC 10, rediffusé par Webstat — `FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA` | Quotidienne, jours cotés |
| Allemagne | Deutsche Bundesbank — `BBSSY.D.REN.EUR.A630.000000WT1010.A` | Quotidienne, jours cotés |
| Italie | Banque de France, Webstat — `FM.M.IT.EUR.FR2.BB.IT10YT_RR.YLD` | Moyenne mensuelle |
| Espagne | Banco de España, tableau TI_1_3 — `D_G0B1F0ZP` | Quotidienne, jours cotés |
| Portugal | Banco de Portugal, BPstat (données LSEG) — `12099459` | Quotidienne, diffusion hebdomadaire |
| Grèce | Banque de Grèce, Greek government securities, colonne 10 years / Yield (%) | Quotidienne, jours cotés |
| Belgique | Banque nationale de Belgique — `BE2:DF_IROLOBE2(1.0)/D.10Y.F` | Quotidienne, jours cotés |

Les URL exactes sont conservées dans `scripts/sovereign_yields.py`, dans `SOURCES`, et reproduites dans le JSON. Les deux séries Webstat sont diffusées par la Banque de France. La source du TEC 10 français est Euronext (`EUXT`). La série concernant l’Italie ne doit pas être attribuée directement à sa banque centrale nationale. Le Portugal utilise directement BPstat, dont le fournisseur identifié est LSEG.

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
- **Portugal** : série quotidienne BPstat `12099459`, rendement des obligations du Trésor à taux fixe et maturité résiduelle de 10 ans, en pourcentage. API officielle du domaine 26, jeu `690b7b36fd36c0dbe249c48cbbc39524`. Accès HTTP 200 vérifié le 6 octobre 2026 depuis le serveur GitHub Actions de collecte ; le 403 concernait l’environnement local de mise en place. Les observations quotidiennes sont diffusées le premier jour ouvré de la semaine et le deuxième jour ouvré du mois ([calendrier BPstat](https://bpstat.bportugal.pt/api/media/files/Calendario_BPstat_data.html)). Le contrôle quotidien intègre chaque lot disponible. L’historique mensuel Webstat est remplacé intégralement à la première collecte BPstat réussie ; en cas d’échec de cette migration, il est conservé avec sa source et sa fréquence mensuelles explicites. Après migration, un incident conserve le dernier historique quotidien valide.
- **Eurostat** : `irt_lt_mcby_m`, mensuel, conservé en secours. L’API existante était encore à août lors de la vérification.
- **Webstat** : utilisation des exports CSV publics du catalogue actuel ; pas de dépendance à l’ancienne API `/api/v2.1/series/.../observations` ni à une clé privée.

## Vérification / exploitation

```sh
python -m unittest discover -s scripts -p 'test_sovereign_yields.py'
python scripts/sovereign_yields.py
```

Les fixtures sont de petits extraits des fichiers officiels recueillis les 4 et 6 octobre 2026 ; `PT.json` couvre plusieurs maturités pour vérifier la sélection exclusive du 10 ans quotidien. En cas d’alerte, consulter `countries` dans le JSON et le journal Actions. Corriger le parseur si le format officiel a changé, puis relancer. Le fichier existant doit rester en place pour conserver les dernières valeurs et l’historique grec.



## Test de la source quotidienne italienne MTS — 6 octobre 2026

Test uniquement, sans modification du collecteur ni des taux publiés. Deux lectures de https://www.mtsmarkets.com/ depuis GitHub Actions ont répondu HTTP 200. L’extraction des données structurées de la page identifie exactement une ligne italienne à 10 ans : `AA_Spread_IT`, `Italy (3.8% 1 Jul 2036)`, champ `avg_yield=4.524` (%), relevé affiché le 6 octobre 2026 à 17 h 30 CET/CEST. Le champ `close=4.611` est distinct et ne doit pas remplacer le rendement courant. Le timestamp technique correspond à 17 h 40 min 46 s, pas à l’heure du relevé affiché.

La page testée contient un seul instantané pour 35 instruments, pas un historique quotidien. MTS présente l’historique dans un service distinct (livraisons de fichiers ponctuelles ou abonnement, HTTPS/SFTP/Snowflake) : https://static-prod.mtsmarkets.com/public/2024-09/MTS_Historical-Data_Factsheet.pdf . Aucun export public complet de l’historique italien n’a été validé. Une collecte régulière pourrait accumuler les prochains relevés. L’historique quotidien Banque d’Italie reste disponible jusqu’au 31 août 2026, mais son raccordement à MTS nécessite d’expliciter le changement de source et la période manquante ; ne pas interpoler les jours absents.

Test d’extraction : https://github.com/YoannParis/Visactu-data/actions/runs/37521791232 . Le workflow temporaire de diagnostic a été retiré après le test.
