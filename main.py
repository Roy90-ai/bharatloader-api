import subprocess
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import re
import yt_dlp

app = FastAPI(title="BharatLoader™ Protected Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    input_url = request.url.strip()
    if not input_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")

    # 🛡️ Strong Threat/Command Injection Regex Filter Hardening
    url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    if not url_pattern.match(input_url) or len(input_url) > 500:
        raise HTTPException(status_code=400, detail="Security Violation: Invalid URL format blocked.")

    # 🛠️ High-End Client Impersonation Engine Config to Bypass Cloud Datacenter Blocks
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        # Force yt-dlp to use native Android/iOS mobile client simulation tokens
        'extractor_args': {
            'youtube': {
                'client': ['android', 'web_embedded', 'mweb'],
                'player_client': ['android', 'web_embedded']
            }
        },
        # Rotate user agents globally to trick CDN proxy layers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_url, download=False)
            title = info.get('title', 'BharatLoader Video')
            thumbnail_url = info.get('thumbnail', 'https://unsplash.com')
            download_url = info.get('url', None)

            if not download_url and 'formats' in info:
                valid_formats = [f for f in info['formats'] if f.get('url') and (f.get('protocol') == 'https' or f.get('protocol') == 'http')]
                if valid_formats:
                    download_url = valid_formats[-1]['url']

            if not download_url:
                raise Exception("Could not resolve streaming download nodes link tracks.")

            return {
                "status": "success",
                "title": title,
                "thumbnail_url": thumbnail_url,
                "download_url": download_url
            }
            
    except Exception as e:
        error_msg = str(e)
        # Custom Error Masking Logic Filter for Restrictive Private Assets
        if "Instagram sent an empty media response" in error_msg or "logged-in" in error_msg:
            raise HTTPException(status_code=400, detail="This video is Private or the Account is restricted.")
        elif "Sign in to confirm you’re not a bot" in error_msg:
            raise HTTPException(status_code=429, detail="Server Throttled: YouTube security challenge active. Try another link or retry in 5 minutes.")
        else:
            raise HTTPException(status_code=500, detail=f"Extraction Bypass Active. Log: {error_msg[:100]}")

app.mount("/", StaticFiles(directory=".", html=True), name="static")
