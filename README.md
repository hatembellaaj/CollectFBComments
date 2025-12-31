# CollectFBComments

Un petit script Python en ligne de commande pour récupérer les commentaires d'une publication Facebook via l'API Graph. Une interface web simplifiée est également disponible (port 8060) pour déclencher la collecte et télécharger le CSV.

## Prérequis
- Python 3.9+
- Un jeton d'accès Graph API avec la permission `pages_read_engagement` (ou équivalent) permettant de lire les commentaires.
- Pas de dépendances externes (tout repose sur la bibliothèque standard).

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

## Interface web (port 8060)

```bash
export FLASK_APP=app.py
flask run --host 0.0.0.0 --port 8060
```

Ouvrez ensuite http://localhost:8060 et renseignez l'URL de la publication ainsi que votre jeton. Les 10 premiers commentaires sont affichés, et un bouton permet de télécharger le CSV généré.

Pour accepter des connexions HTTPS (utile si votre navigateur force le chiffrement), vous pouvez :

- fournir vos propres fichiers de certificat et de clé via `SSL_CERT_FILE` et `SSL_KEY_FILE`, ou
- définir `USE_HTTPS=1` pour générer automatiquement un certificat de développement (dépend de la bibliothèque `cryptography`).

## Docker

Une image Docker prête à l'emploi expose l'interface web sur le port 8060.

```bash
docker build -t collect-fb-comments .
docker run --rm -p 8060:8060 collect-fb-comments
```
