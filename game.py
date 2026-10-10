"""Box Fight 2D Windows app with a GitHub Releases auto-updater."""
import os
import re
import sys
import json
import time
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

import webview

# CHANGE THESE TWO SETTINGS before building the public version.
GITHUB_OWNER = "Janot155"
GITHUB_REPO = "BOXFIGHT2D"
APP_VERSION = "1.0.0"
RELEASE_ASSET_NAME = "BoxFight2D.exe"
USER_AGENT = "BoxFight2D-Updater/1.0"
MAX_DOWNLOAD_BYTES = 600 * 1024 * 1024  # safety limit: 600 MB


def resource_path(filename: str) -> Path:
    """Find a file both in development and inside a PyInstaller bundle."""
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / filename
    return Path(__file__).resolve().parent / filename


def version_parts(value: str) -> tuple[int, ...]:
    """Compare common release tags such as v1.2.3, 1.2.3 or 1.2."""
    parts = re.findall(r"\d+", value or "")
    return tuple(int(p) for p in parts) if parts else (0,)


def is_newer(remote: str, local: str) -> bool:
    a, b = version_parts(remote), version_parts(local)
    length = max(len(a), len(b))
    return a + (0,) * (length - len(a)) > b + (0,) * (length - len(b))


def github_is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO and GITHUB_OWNER != "YOUR_GITHUB_USERNAME")


def github_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })


def read_latest_release() -> dict[str, Any]:
    if not github_is_configured():
        raise RuntimeError("Automatické aktualizace ještě nejsou propojené s GitHubem. V game.py nastav GITHUB_OWNER a GITHUB_REPO a vytvoř veřejný GitHub repozitář.")
    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    request = github_request(api_url)
    with urllib.request.urlopen(request, timeout=12) as response:
        release = json.loads(response.read().decode("utf-8"))
    if release.get("draft") or release.get("prerelease"):
        raise RuntimeError("Poslední GitHub vydání je draft nebo prerelease; vytvoř běžné vydání.")
    return release


class AppApi:
    def __init__(self) -> None:
        self.window = None
        self._latest_release: dict[str, Any] | None = None

    def check_updates(self) -> dict[str, Any]:
        if not github_is_configured():
            return {"ok": False, "configured": False, "currentVersion": APP_VERSION,
                    "message": "Aktualizace nejsou propojené. V game.py nastav GITHUB_OWNER a GITHUB_REPO; návod je v NAVOD.txt."}
        try:
            release = read_latest_release()
            latest = str(release.get("tag_name", "")).strip()
            if not latest:
                raise RuntimeError("GitHub vydání nemá vyplněný tag verze.")
            assets = release.get("assets") or []
            asset = next((a for a in assets if a.get("name") == RELEASE_ASSET_NAME), None)
            if is_newer(latest, APP_VERSION) and not asset:
                raise RuntimeError(f"Vydání {latest} neobsahuje soubor {RELEASE_ASSET_NAME}. Nahraj EXE jako release asset.")
            self._latest_release = release
            return {"ok": True, "configured": True, "currentVersion": APP_VERSION,
                    "latestVersion": latest, "updateAvailable": is_newer(latest, APP_VERSION),
                    "notes": str(release.get("body") or "")[:2000]}
        except Exception as exc:
            return {"ok": False, "configured": True, "currentVersion": APP_VERSION,
                    "error": f"{type(exc).__name__}: {exc}"}

    def install_update(self) -> dict[str, Any]:
        """Download the newest release and use PowerShell to replace this EXE after exit."""
        if not getattr(sys, "frozen", False):
            return {"ok": False, "error": "Aktualizace EXE fungují až v sestavené aplikaci BoxFight2D.exe."}
        if not github_is_configured():
            return {"ok": False, "error": "Aktualizace nejsou propojené s GitHubem. Viz NAVOD.txt."}
        try:
            release = self._latest_release or read_latest_release()
            latest = str(release.get("tag_name", "")).strip()
            if not is_newer(latest, APP_VERSION):
                return {"ok": False, "error": "Novější verze už není dostupná."}
            asset = next((a for a in (release.get("assets") or []) if a.get("name") == RELEASE_ASSET_NAME), None)
            if not asset:
                return {"ok": False, "error": f"Vydání {latest} neobsahuje {RELEASE_ASSET_NAME}."}
            asset_size = int(asset.get("size") or 0)
            if asset_size and asset_size > MAX_DOWNLOAD_BYTES:
                return {"ok": False, "error": "Aktualizace je nečekaně velká; stahování bylo zastaveno."}

            temp_dir = Path(tempfile.gettempdir()) / "BoxFight2DUpdater"
            temp_dir.mkdir(parents=True, exist_ok=True)
            safe_version = re.sub(r"[^A-Za-z0-9._-]", "_", latest)
            download_path = temp_dir / f"BoxFight2D-{safe_version}.exe"
            request = urllib.request.Request(str(asset.get("browser_download_url", "")), headers={"User-Agent": USER_AGENT})
            written = 0
            with urllib.request.urlopen(request, timeout=45) as response, open(download_path, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_DOWNLOAD_BYTES:
                        raise RuntimeError("Stažený soubor je větší než povolený limit.")
                    output.write(chunk)
            if written < 100_000:
                raise RuntimeError("Stažený soubor je podezřele malý; aktualizace nebyla spuštěna.")

            target_exe = Path(sys.executable).resolve()
            script_path = temp_dir / f"apply_update_{os.getpid()}.ps1"
            def ps_quote(value: str) -> str:
                return "'" + value.replace("'", "''") + "'"
            # The helper waits for the current app to exit, retries the file replacement,
            # then starts the newly downloaded application and cleans up temporary files.
            script = f"""$ErrorActionPreference = 'Stop'
$OldProcessId = {os.getpid()}
$Downloaded = {ps_quote(str(download_path))}
$Target = {ps_quote(str(target_exe))}
$Helper = {ps_quote(str(script_path))}
while (Get-Process -Id $OldProcessId -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 500 }}
$Replaced = $false
for ($i = 0; $i -lt 30; $i++) {{
  try {{ Copy-Item -LiteralPath $Downloaded -Destination $Target -Force; $Replaced = $true; break }}
  catch {{ Start-Sleep -Seconds 1 }}
}}
if ($Replaced) {{ Start-Process -FilePath $Target }}
Start-Sleep -Seconds 2
Remove-Item -LiteralPath $Downloaded -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $Helper -Force -ErrorAction SilentlyContinue
"""
            script_path.write_text(script, encoding="utf-8-sig")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True, creationflags=creationflags,
            )
            # Let the JS API call return before closing the current process.
            threading.Timer(1.2, lambda: os._exit(0)).start()
            return {"ok": True, "message": f"Instaluji verzi {latest}. Aplikace se za chvíli restartuje."}
        except Exception as exc:
            return {"ok": False, "error": f"Aktualizaci se nepodařilo nainstalovat: {type(exc).__name__}: {exc}"}


html_file = resource_path("index.html")
if not html_file.exists():
    raise FileNotFoundError(f"Soubor hry nebyl nalezen: {html_file}")
api = AppApi()
window = webview.create_window(
    title=f"Box Fight 2D v{APP_VERSION}",
    url=html_file.as_uri(),
    width=1280,
    height=800,
    min_size=(800, 550),
    background_color="#07101f",
    js_api=api,
)
api.window = window
webview.start()
