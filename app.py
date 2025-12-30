"""Simple web interface to collect Facebook comments via the Graph API."""
from __future__ import annotations

import io

from flask import Flask, render_template, request

from collect_comments import CommentCollector, extract_post_id, save_comments_to_csv


app = Flask(__name__)
app.secret_key = "collect-fb-comments"


@app.get("/")
def home():
    return render_template(
        "index.html",
        error=None,
        preview=None,
        csv_content=None,
        csv_name="comments.csv",
        comment_count=0,
        form={"post_url": "", "access_token": "", "post_id": "", "api_version": "v19.0"},
    )


@app.post("/")
def collect_comments():
    form = {
        "post_url": request.form.get("post_url", "").strip(),
        "access_token": request.form.get("access_token", "").strip(),
        "post_id": request.form.get("post_id", "").strip(),
        "api_version": request.form.get("api_version", "v19.0").strip() or "v19.0",
    }
    csv_name = request.form.get("csv_name", "comments.csv").strip() or "comments.csv"

    if not form["post_url"] or not form["access_token"]:
        return render_template(
            "index.html",
            error="L'URL du post et le jeton d'accès sont requis.",
            preview=None,
            csv_content=None,
            csv_name=csv_name,
            comment_count=0,
            form=form,
        )

    try:
        post_id = form["post_id"] or extract_post_id(form["post_url"])
    except ValueError as exc:  # noqa: PERF203 - explicit error mapping for the UI
        return render_template(
            "index.html",
            error=str(exc),
            preview=None,
            csv_content=None,
            csv_name=csv_name,
            comment_count=0,
            form=form,
        )

    collector = CommentCollector(
        access_token=form["access_token"], api_version=form["api_version"]
    )

    try:
        comments = collector.collect(post_id)
    except Exception as exc:  # noqa: BLE001 - surface errors in the UI
        return render_template(
            "index.html",
            error=f"Impossible de récupérer les commentaires : {exc}",
            preview=None,
            csv_content=None,
            csv_name=csv_name,
            comment_count=0,
            form=form,
        )

    preview = comments[:10]

    csv_buffer = io.StringIO()
    save_comments_to_csv(comments, csv_buffer)
    csv_content = csv_buffer.getvalue()

    return render_template(
        "index.html",
        error=None,
        preview=preview,
        csv_content=csv_content,
        csv_name=csv_name,
        comment_count=len(comments),
        form=form,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8060)
