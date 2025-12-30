# CollectFBComments

Un petit script Python en ligne de commande pour récupérer les commentaires d'une publication Facebook via l'API Graph.

## Prérequis
- Python 3.9+
- Un jeton d'accès Graph API avec la permission `pages_read_engagement` (ou équivalent) permettant de lire les commentaires.
- Pas de dépendances externes (tout repose sur la bibliothèque standard).

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
# Aucune installation de package n'est nécessaire
```

## Utilisation
```bash
python collect_comments.py "URL_DE_LA_PUBLICATION" "VOTRE_JETON" --csv sortie.csv
```

Options principales :
- `--post-id` : renseignez directement l'identifiant du post si le script n'arrive pas à l'extraire de l'URL.
- `--api-version` : préfixe de version de l'API Graph (par défaut `v19.0`).
- `--csv` : nom du fichier CSV de sortie (par défaut `comments.csv`).

La commande affiche les 10 premiers commentaires dans le terminal et écrit l'ensemble des commentaires dans le fichier CSV indiqué.

## Champs exportés
Le CSV comporte les colonnes suivantes : `comment_id`, `created_time`, `author_id`, `author_name`, `message`, `parent_id`, `like_count`.
