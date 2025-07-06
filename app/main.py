import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import requests

load_dotenv()

API_TOKEN = os.getenv("TRAVELPAYOUTS_API_TOKEN")
PARTNER_ID = os.getenv("TRAVELPAYOUTS_PARTNER_ID")

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Home page with search form
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Flight search API
@app.post("/api/flights/search")
def search_flights(
    origin: str = Form(...),
    destination: str = Form(...),
    departure_at: str = Form(...),
    return_at: str = Form(None),
    one_way: bool = Form(True),
    currency: str = Form("usd"),
    limit: int = Form(5)
):
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    headers = {"X-Access-Token": API_TOKEN}
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_at,
        "currency": currency,
        "limit": limit,
        "one_way": str(one_way).lower(),
        "market": "us"
    }
    if not one_way and return_at:
        params["return_at"] = return_at
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    # Add partner_id to booking links
    for f in data.get("data", []):
        link = f.get("link", "")
        if link:
            if "?" in link:
                link += f"&partner_id={PARTNER_ID}"
            else:
                link += f"?partner_id={PARTNER_ID}"
            f["booking_link"] = f"https://www.aviasales.com{link}"
    return JSONResponse(data)

# Hotel search API
@app.post("/api/hotels/search")
def search_hotels(
    location: str = Form(...),
    check_in: str = Form(...),
    check_out: str = Form(...),
    currency: str = Form("usd"),
    adults: int = Form(2),
    limit: int = Form(5)
):
    url = "https://api.travelpayouts.com/v2/hotels/search"
    headers = {"X-Access-Token": API_TOKEN}
    params = {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "currency": currency,
        "adults": adults,
        "limit": limit
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    # Add partner_id to booking links
    for h in data.get("results", []):
        url = h.get("booking_url", "")
        if url:
            if "?" in url:
                url += f"&partner_id={PARTNER_ID}"
            else:
                url += f"?partner_id={PARTNER_ID}"
            h["booking_url"] = url
    return JSONResponse(data)

# Combined search API
@app.post("/api/search/combined")
def combined_search(
    origin: str = Form(...),
    destination: str = Form(...),
    departure_at: str = Form(...),
    return_at: str = Form(None),
    one_way: bool = Form(True),
    currency: str = Form("usd"),
    check_in: str = Form(None),
    check_out: str = Form(None),
    adults: int = Form(2),
    limit: int = Form(5)
):
    # Flights
    url_f = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    headers = {"X-Access-Token": API_TOKEN}
    params_f = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_at,
        "currency": currency,
        "limit": limit,
        "one_way": str(one_way).lower(),
        "market": "us"
    }
    if not one_way and return_at:
        params_f["return_at"] = return_at
    r_f = requests.get(url_f, headers=headers, params=params_f)
    flights = r_f.json().get("data", [])
    for f in flights:
        link = f.get("link", "")
        if link:
            if "?" in link:
                link += f"&partner_id={PARTNER_ID}"
            else:
                link += f"?partner_id={PARTNER_ID}"
            f["booking_link"] = f"https://www.aviasales.com{link}"
    # Hotels
    hotels = []
    if check_in and check_out:
        url_h = "https://api.travelpayouts.com/v2/hotels/search"
        params_h = {
            "location": destination,
            "check_in": check_in,
            "check_out": check_out,
            "currency": currency,
            "adults": adults,
            "limit": limit
        }
        r_h = requests.get(url_h, headers=headers, params=params_h)
        hotels = r_h.json().get("results", [])
        for h in hotels:
            url = h.get("booking_url", "")
            if url:
                if "?" in url:
                    url += f"&partner_id={PARTNER_ID}"
                else:
                    url += f"?partner_id={PARTNER_ID}"
                h["booking_url"] = url
    return JSONResponse({"flights": flights, "hotels": hotels}) 