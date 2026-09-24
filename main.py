from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
import random
import requests
import time

app = FastAPI(title="YT-DLP API")

POT_SERVER = os.getenv("POT_SERVER", "http://127.0.0.1:4416")

# Proxy cache
_proxy_cache = {"list": [], "fetched_at": 0}


def fetch_free_proxies():
    """Free proxy list fetch cheyy (multiple sources)"""
    now = time.time()
    # 10 min cache
    if _proxy_cache["list"] and (now - _proxy_cache["fetched_at"]) < 600:
        return _proxy_cache["list"]

    proxies = []

    # Source 1: ProxyScrape
    try:
        r = requests.get(
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            timeout=15,
        )
        for line in r.text.strip().split("\n"):
            line = line.strip()
            if line and ":" in line:
                proxies.append(f"http://{line}")
    except Exception as e:
        print(f"ProxyScrape fail: {e}")

    # Source 2: TheSpeedX GitHub
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            timeout=15,
        )
        for line in r.text.strip().split("\n"):
            line = line.strip()
            if line and ":" in line:
                proxies.append(f"http://{line}")
    except Exception as e:
        print(f"SpeedX fail: {e}")

    # Dedupe
    proxies = list(set(proxies))
    random.shuffle(proxies)

    _proxy_cache["list"] = proxies
    _proxy_cache["fetched_at"] = now

    print(f"Fetched {len(proxies)} proxies")
    return proxies


def get_ydl_opts(fmt="bv*+ba/b", proxy=None):
    """yt-dlp options build cheyy"""
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 15,
        "retries": 2,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "web"],
            },
            "youtubepot-bgutilhttp": {
                "base_url": [POT_SERVER]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
        },
    }

    if proxy:
        opts["proxy"] = proxy

    return opts


def try_extract(url, fmt="bv*+ba/b"):
    """Multiple proxies try cheyy until success"""
    proxies = fetch_free_proxies()
    errors = []

    # Try direct first (no proxy)
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(fmt)) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        errors.append(f"direct: {str(e)[:100]}")

    # Try proxies
    # Only try first 20 (timeout prevent)
    for i, proxy in enumerate(proxies[:20]):
        try:
            print(f"Trying proxy {i+1}: {proxy}")
            with yt_dlp.YoutubeDL(get_ydl_opts(fmt, proxy)) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"✅ Success with {proxy}")
                return info
        except Exception as e:
            errors.append(f"{proxy}: {str(e)[:80]}")
            continue

    raise Exception("All proxies failed. Last errors: " + " | ".join(errors[-3:]))


class VideoRequest(BaseModel):
    url: str
    format: str = "bv*+ba/b"


@app.get("/")
def root():
    return {"status": "ok", "service": "yt-dlp-api"}


@app.post("/info")
def get_info(req: VideoRequest):
    try:
        info = try_extract(req.url)

        formats = []
        for f in info.get("formats", []):
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution"),
                "filesize": f.get("filesize"),
                "url": f.get("url"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
            })

        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
            "formats": formats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
def get_download_url(req: VideoRequest):
    try:
        info = try_extract(req.url, req.format)
        return {
            "title": info.get("title"),
            "url": info.get("url"),
            "ext": info.get("ext"),
            "filesize": info.get("filesize"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/proxies")
def list_proxies():
    """Debug: ethra proxies und ennu kaanan"""
    proxies = fetch_free_proxies()
    return {"count": len(proxies), "sample": proxies[:5]}
