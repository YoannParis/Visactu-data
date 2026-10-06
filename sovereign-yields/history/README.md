# Historique quotidien italien à 10 ans — recherche du 6 octobre 2026

Ces fichiers sont les archives sources du raccordement quotidien publié le 6 octobre 2026. Le collecteur utilise Countryeconomy jusqu’au 30 septembre et Investing.com seulement du 1er au 5 octobre ; MTS/Euronext prend le relais à partir du 6 octobre. Les CSV bruts restent inchangés et séparés.

## Countryeconomy

`italy-10y-countryeconomy.csv` : 1 678 observations datées du 17 juillet 2020 au 30 septembre 2026, dont 1 348 depuis le 6 octobre 2021. Rendements en pourcentage, deux décimales. Extraction des tableaux de données des graphiques publics, sans interpolation ni transformation des dates. Les observations datées du samedi par le fournisseur sont conservées comme telles.

Pages utilisées :
- https://countryeconomy.com/bonds/italy
- https://countryeconomy.com/bonds/italy?dr=2025-08
- https://countryeconomy.com/bonds/italy?dr=2024-08
- https://countryeconomy.com/bonds/italy?dr=2023-08
- https://countryeconomy.com/bonds/italy?dr=2022-08
- https://countryeconomy.com/bonds/italy?dr=2021-08

Vérifications : dates uniques et triées ; aucun conflit de valeur entre les pages qui se recouvrent ; écart maximal de quatre jours calendaires entre observations sur la période de cinq ans. Cette continuité ne garantit pas une observation à chaque séance. Comparaison avec la Banque d’Italie BMK0200 sur 1 242 dates communes : écart absolu médian de 3,0265 points de base, maximum de 47,683 points de base. Les séries ne sont donc pas interchangeables : heures de relevé, obligation de référence et méthodes peuvent différer ; l’origine de chaque écart n’a pas été établie.

## Investing.com

`italy-10y-investing-recent.csv` : 22 observations quotidiennes du 7 septembre au 6 octobre 2026, récupérées dans les données structurées de la page publique. Valeur du 6 octobre au moment de l’extraction : 4,559 %. Cette valeur ne correspond pas au relevé MTS de 17 h 30 (4,524 %). La date du jour peut encore être révisée par le fournisseur.

https://www.investing.com/rates-bonds/italy-10-year-bond-yield-historical-data

Instrument identifié par le site : 23738, Italy 10-Year Bond Yield. Champ extrait : `last_close`, daté par `rowDateTimestamp`. Le téléchargement complet de longue période depuis l’API n’a pas été validé.

## Raccordement publié

Un historique quotidien sur cinq ans est effectivement récupérable, contrairement à l’historique MTS public qui n’a pas été trouvé. Les deux CSV restent séparés et ne sont pas présentés comme une série MTS/Euronext. Les sources et dates de changement sont documentées dans les métadonnées du JSON (`countries.IT.segments`), le libellé de source et la note de l’Italie. Les données originales sont conservées et aucun point manquant n’est interpolé. La Banque d’Italie reste une autre source officielle d’historique quotidien, disponible jusqu’au 31 août 2026 lors du contrôle.
