from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import HttpUrl, ValidationError
from typing import Optional
import requests
import logging

# Initialize FastAPI
app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

@app.get("/", response_class=PlainTextResponse)
def root():
    return """✅ API is up!

To use this API, make a request like:
curl "http://localhost:8000/resolve?domain=example.com"
"""


@app.get("/resolve")
def resolve_domain(domain: str = Query(..., description="Domain to resolve, e.g., example.com")):
    # Prepend scheme if missing
    if not domain.startswith(("http://", "https://")):
        url = f"https://{domain}"
    else:
        url = domain

    try:
        response = requests.get(url, allow_redirects=True, timeout=5)

        # Log the redirect chain
        for i, step in enumerate(response.history):
            logging.info(f"[Redirect {i+1}] {step.status_code} - {step.url}")

        logging.info(f"[Final URL] {response.status_code} - {response.url}")

        return {
            "input": domain,
            "final_url": response.url,
            "status_code": response.status_code,
            "status": "success"
        }

    except requests.exceptions.SSLError:
        return JSONResponse(status_code=400, content={
            "input": domain,
            "error": "SSL certificate error",
            "status": "error"
        })

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
