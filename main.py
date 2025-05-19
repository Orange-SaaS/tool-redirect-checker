from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import requests
import logging

app = FastAPI()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


@app.get("/", response_class=PlainTextResponse)
def root():
    return """✅ API is up!

To use this API, make a request like:
curl "https://your-domain.up.railway.app/resolve?domain=example.com"
"""


@app.get("/resolve")
def resolve_domain(domain: str = Query(..., description="Domain to resolve, e.g., example.com")):
    # Add scheme if not present
    if not domain.startswith(("http://", "https://")):
        url = f"https://{domain}"
    else:
        url = domain

    try:
        try:
            # Try with SSL verification ON
            response = requests.get(url, allow_redirects=True, timeout=5)
        except requests.exceptions.SSLError:
            # Retry with SSL verification OFF (unsafe)
            logging.warning(f"SSL error for {url}, retrying with verify=False")
            response = requests.get(url, allow_redirects=True, timeout=5, verify=False)

        # Log redirect chain
        for i, step in enumerate(response.history):
            logging.info(f"[Redirect {i+1}] {step.status_code} - {step.url}")

        logging.info(f"[Final URL] {response.status_code} - {response.url}")

        return {
            "input": domain,
            "final_url": response.url,
            "status_code": response.status_code,
            "status": "success"
        }

    except requests.exceptions.TooManyRedirects:
        return JSONResponse(status_code=400, content={
            "input": domain,
            "error": "Too many redirects",
            "status": "error"
        })

    except requests.exceptions.ConnectionError:
        return JSONResponse(status_code=400, content={
            "input": domain,
            "error": "Domain unreachable or DNS error",
            "status": "error"
        })

    except requests.exceptions.Timeout:
        return JSONResponse(status_code=400, content={
            "input": domain,
            "error": "Request timed out",
            "status": "error"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "input": domain,
            "error": str(e),
            "status": "error"
        })
