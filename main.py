from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
import random

app = FastAPI(title="YT-DLP API")

POT_SERVER = os.getenv("POT_SERVER", "http://127.0.0.1:4416")

# Webshare proxies (10)
PROXIES = [
    "http://apkzckku-1:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-2:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-3:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-4:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-5:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-6:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-7:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-8:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-9:wvooiacgae9n@p.webshare.io:80",
    "http://apkzckku-10:wvooiacgae9n@p.webshare.io:80",
]


def get_ydl_opts(fmt="bv*+ba/b", proxy=None):
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
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
    """Webshare proxies rotate cheyy until success"""
    errors = []

    # Shuffle so we don't always hit proxy 1
    proxies = PROXIES.copy()
    random.shuffle(proxies)

    for i, proxy in enumerate(proxies):
        try:
            print(f"Trying proxy {i+1}/{len(proxies)}: {proxy.split('@')[1]}")
            with yt_dlp.YoutubeDL(get_ydl_opts(fmt, proxy)) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"✅ Success with proxy {i+1}")
                return info
        except Exception as e:
            err = str(e)[:120]
            print(f"❌ Proxy {i+1} failed: {err}")
            errors.append(f"proxy{i+1}: {err}")
            continue

    raise Exception("All proxies failed. Errors: " + " | ".join(errors[-3:]))


class VideoRequest(BaseModel):
    url: str
    format: str = "bv*+ba/b"


@app.get("/")
def root():
    return {"status": "ok", "service": "yt-dlp-api"}


@app.get("/test-proxy")
def test_proxy():
    """Webshare proxy test cheyy"""
    import requests
    results = []
    for i, proxy in enumerate(PROXIES):
        try:
            r = requests.get(
                "https://ipv4.webshare.io/",
                proxies={"http": proxy, "https": proxy},
                timeout=10,
            )
            results.append({
                "proxy": i + 1,
                "ip": r.text.strip(),
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "proxy": i + 1,
                "status": "fail",
                "error": str(e)[:80]
            })
    return {"results": results}


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
