from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import requests
import logging
import dns.resolver

app = FastAPI()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


@app.get("/", response_class=PlainTextResponse)
def root():
    return """✅ API is up!

To use this API, make a request like:
curl "https://your-domain.up.railway.app/resolve?domain=example.com"

To check for a CNAME match, use:
curl "https://your-domain.up.railway.app/check-cname?domain=custom.lemlist.com&expected_cname=lemlist.map.fastly.net"
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
            logging.warning(f"SSL error for {url}, retrying without verification.")
            response = requests.get(url, allow_redirects=True, timeout=5, verify=False)

        return {
            "final_url": response.url,
            "status_code": response.status_code,
            "history": [resp.url for resp in response.history]
        }
    except requests.RequestException as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/check-cname")
async def check_cname(domain: str, expected_cname: str):
    try:
        answers = dns.resolver.resolve(domain, 'CNAME')
        for rdata in answers:
            if expected_cname.strip('.') == str(rdata.target).strip('.'):
                return {"match": True}
        return {"match": False}
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return {"match": False}
    except Exception as e:
        return {"error": str(e)}
