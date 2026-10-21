# 🏠 JavaHouse

**Estimation des prix de l'immobilier au Maroc : collecte de données, machine learning et API REST Spring Boot.**

JavaHouse est un projet personnel de bout en bout, **entièrement développé en Java** : collecte d'annonces immobilières, nettoyage des données, entraînement d'un modèle de prédiction de prix, puis exposition via une API REST Java Spring Boot.

> ⚠️ **Statut : en cours de développement.** Les sections marquées 🚧 sont prévues mais pas encore terminées.

---

## 🎯 Objectifs

- Construire un pipeline de données réaliste : collecte → nettoyage → modèle → API
- Exposer un service d'estimation de prix de biens immobiliers au Maroc
- Appliquer de bonnes pratiques d'ingénierie : tests, conteneurisation, CI, documentation d'API

## 🧱 Architecture

```
Collecteur (Python)  →  PostgreSQL
                          ↓
        Entraînement du modèle (Java)
                          ↓
   API Spring Boot (charge le modèle)  →  Clients / démo
```

Projet **100 % Java**, organisé en modules Maven.

| Composant | Rôle | Technologies |
|---|---|---|
| `collector/` | Collecte des annonces et stockage | Python, Selenium |
| `ml/` | Nettoyage, features, entraînement, évaluation | Java, Tablesaw, Tribuo / Smile |
| `api/` | API REST, charge le modèle entraîné et sert les estimations | Java, Spring Boot, Spring Data JPA |
| `db` | Stockage des annonces | PostgreSQL |
| Infra | Lancement de tout le projet | Docker Compose, GitHub Actions 🚧 |

## ✨ Fonctionnalités

- [ ] Collecte et déduplication des annonces
- [ ] Nettoyage des données (prix, surfaces, valeurs aberrantes)
- [ ] Modèle de référence puis modèle amélioré, avec comparaison des métriques
- [ ] `GET /api/listings` : liste paginée et filtrable des annonces
- [ ] `POST /api/estimate` : estimation du prix d'un bien
- [ ] `GET /api/stats/neighborhoods` : prix moyen au m² par quartier
- [ ] Documentation Swagger / OpenAPI
- [ ] Tests unitaires et d'intégration, CI

## 🔌 Exemple d'utilisation de l'API (cible) 🚧

```http
POST /api/estimate
Content-Type: application/json

{
  "city": "Rabat",
  "neighborhood": "Agdal",
  "type": "apartment",
  "surface": 85,
  "rooms": 3,
  "bathrooms": 1
}
```

```json
{
  "estimatedPrice": 1250000,
  "currency": "MAD",
  "range": { "min": 1100000, "max": 1400000 }
}
```

## 🚀 Lancer le projet 🚧

```bash
git clone https://github.com/aalachi/javahouse.git
cd javahouse
docker compose up --build
```



## ⚖️ Données, éthique et limites

- Le projet est **non commercial** et à visée pédagogique.
- Seules les **caractéristiques des biens** sont conservées (prix, surface, localisation, type, nombre de pièces). Aucune donnée personnelle (téléphone, nom de vendeur) n'est collectée ni stockée.
- La collecte est **limitée et espacée** pour ne pas surcharger les sites sources, et respecte leurs conditions d'utilisation.
- Le **jeu de données n'est pas publié** dans ce dépôt.
- Les prix collectés sont des **prix demandés** et non des prix de vente réels : les estimations reflètent donc le marché des annonces, pas les transactions.

## 🗺️ Feuille de route

1. Collecteur et schéma de base de données
2. Nettoyage et analyse exploratoire
3. Modèle de référence et évaluation
4. API Spring Boot et service de prédiction
5. Docker Compose, tests, CI
6. Démo en ligne et documentation finale



