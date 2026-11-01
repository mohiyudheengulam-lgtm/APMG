"""`agent-on-duty` — start the app (API + web UI) in one process and open it in the browser."""

import argparse
import json
import threading
import urllib.request
import webbrowser

MODELS = ("qwen3:1.7b", "nomic-embed-text")


def _ollama_models(base: str) -> list[str] | None:
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.load(r).get("models", [])]
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(prog="agent-on-duty", description="Local procurement verification with human approval.")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to allow other devices on your network")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    from agent_on_duty import paths

    for d in (paths.PACKAGES, paths.UPLOADS, paths.CONTRACTS, paths.RESULTS):
        d.mkdir(parents=True, exist_ok=True)
    print(f"Agent On Duty — data folder: {paths.HOME}")
    models = _ollama_models("http://127.0.0.1:11434")
    if models is None:
        print("! Ollama is not running. Install it from https://ollama.com and start it, then verifications will work.")
    else:
        for m in MODELS:
            if not any(x in (m, f"{m}:latest") for x in models):
                print(f"! Model missing — run:  ollama pull {m}")
    if not (paths.WEB_BUILD / "index.html").exists():
        print("! Web app not bundled (source checkout?) — run scripts/build_app.sh, or use scripts/dev.sh")

    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(f"Open {url}   (Ctrl-C to stop)")
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    import uvicorn

    uvicorn.run("agent_on_duty.api:app", host=args.host, port=args.port, timeout_keep_alive=75, log_level="warning")


if __name__ == "__main__":
    main()
