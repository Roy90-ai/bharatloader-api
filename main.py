from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import subprocess
import asyncio
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

app = FastAPI(title="BharatLoader India API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

SUPPORTED_HOSTS = ("youtube.com", "youtu.be", "instagram.com", "sharechat.com", "mojapp.in", "myjosh.in", "joshapp.com", "facebook.com", "fb.watch", "fb.com")

def validate_media_url(value):
    invalid = "Security Violation: Invalid URL format blocked."
    if not isinstance(value, str) or len(value) > 500:
        raise HTTPException(status_code=400, detail=invalid)
    value = value.strip()
    try:
        if not value or re.search(r"[\s\x00-\x1f\x7f<>\"'`\\|;${}]", value) or re.search(r"%(?![0-9a-fA-F]{2})", value):
            raise ValueError()
        decoded = value
        for _ in range(3):
            decoded = unquote(decoded)
        if re.search(r"[\x00-\x1f\x7f<>\"'`\\|;${}]", decoded) or re.search(r"(?:javascript|vbscript|data):", decoded, re.I):
            raise ValueError()
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in ("http", "https") or parsed.username is not None or parsed.password is not None or parsed.port not in (None, 80, 443):
            raise ValueError()
        # Restrict this downloader to its advertised platforms, blocking direct
        # localhost/private-address requests and lookalike hostnames.
        if not any(host == domain or host.endswith("." + domain) for domain in SUPPORTED_HOSTS):
            raise ValueError()
    except (ValueError, UnicodeError):
        raise HTTPException(status_code=400, detail=invalid) from None
    return value

class DownloadRequest(BaseModel):
    url: str

async def auto_upgrade_ytdlp():
    while True:
        try:
            print("[SYSTEM] Running automated background self-upgrade: pip install --upgrade yt-dlp...")
            process = await asyncio.create_subprocess_exec(
                "pip", "install", "--upgrade", "yt-dlp",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            print(f"[EXCEPTION] Auto-upgrade failed: {str(e)}")
        await asyncio.sleep(86400)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_upgrade_ytdlp())

@app.post("/api/download")
async def extract_media_link(request: DownloadRequest):
    input_url = validate_media_url(request.url)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_url, download=False)
            title = info.get('title', 'BharatLoader Video')
            thumbnail_url = info.get('thumbnail', 'https://unsplash.com')
            download_url = info.get('url', None)

            if not download_url and 'formats' in info:
                valid_formats = [f for f in info['formats'] if f.get('url')]
                if valid_formats:
                    download_url = valid_formats[-1]['url']

            if not download_url:
                raise Exception("Could not resolve download URL.")

            return {
                "status": "success",
                "title": title,
                "thumbnail_url": thumbnail_url,
                "download_url": download_url
            }
    except Exception as e:
        error_message = str(e).lower()
        if (
            "instagram sent an empty media response" in error_message
            or "check if this post is accessible in your browser without being logged-in" in error_message
        ):
            raise HTTPException(
                status_code=400,
                detail="This video is Private or the Account is restricted."
            ) from None
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse(Path(__file__).resolve().parent / "index.html", headers={"Cache-Control": "no-store"})
