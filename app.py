from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    path_name = Path(parsed.path).name or "downloaded_file"
    safe_name = secure_filename(path_name)
    return safe_name or "downloaded_file"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/download")
def download_from_url():
    url = request.form.get("url", "").strip()
    if not url:
        flash("يرجى إدخال الرابط أولاً.", "error")
        return redirect(url_for("index"))

    if not (url.startswith("http://") or url.startswith("https://")):
        flash("الرابط يجب أن يبدأ بـ http:// أو https://.", "error")
        return redirect(url_for("index"))

    filename = _filename_from_url(url)
    destination = DOWNLOAD_DIR / filename

    try:
        response = requests.get(url, stream=True, timeout=25)
        response.raise_for_status()

        content_disposition = response.headers.get("content-disposition", "")
        if "filename=" in content_disposition:
            header_name = content_disposition.split("filename=")[-1].strip('"\' ')
            if header_name:
                filename = secure_filename(header_name)
                destination = DOWNLOAD_DIR / filename

        with destination.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_obj.write(chunk)
    except requests.RequestException:
        flash("تعذر تحميل الملف من الرابط. تأكد من صحة الرابط وحاول مرة أخرى.", "error")
        return redirect(url_for("index"))

    mime_type, _ = mimetypes.guess_type(str(destination))
    return send_file(
        destination,
        as_attachment=True,
        download_name=destination.name,
        mimetype=mime_type or "application/octet-stream",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
