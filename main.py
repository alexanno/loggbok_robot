#!/usr/bin/env python3
"""
Generate creative ship log entries in Norwegian using weather and location data.

The script:
1. Selects a random lighthouse from the Sørland fjords (from geojson)
2. Fetches weather data from Met.no API
3. Generates a creative ship log entry using Ollama
4. Outputs via webhook, markdown file, or shell
"""

import json
import random
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
import ollama


def load_geojson(filepath: str = "fyrlykter_sorlandet.geojson") -> dict:
    """Load and parse the lighthouse geojson file."""
    with open(filepath) as f:
        return json.load(f)


def select_random_location(geojson_data: dict) -> tuple[dict, dict]:
    """
    Select a random lighthouse from the geojson.
    Returns: (feature_properties, coordinates)
    """
    features = geojson_data["features"]
    feature = random.choice(features)
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]  # [lon, lat]
    return props, coords


def fetch_weather_data(latitude: float, longitude: float) -> dict:
    """Fetch weather data from Met.no API for the given coordinates."""
    url = f"https://api.met.no/weatherapi/nowcast/2.0/complete?lat={latitude}&lon={longitude}"
    headers = {"User-Agent": "loggbok-robot (https://github.com/alexandesn/loggbok_robot)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract first timeseries entry
        if data.get("properties", {}).get("timeseries"):
            first_entry = data["properties"]["timeseries"][0]
            return first_entry
        return {}
    except Exception as e:
        print(f"Warning: Could not fetch weather data: {e}", file=sys.stderr)
        return {}


def format_weather_description(weather_data: dict) -> str:
    """Format weather data into a human-readable description."""
    if not weather_data:
        return "No weather data available"
    
    data = weather_data.get("data", {})
    instant = data.get("instant", {}).get("details", {})
    next_1h = data.get("next_1h", {}).get("details", {})
    
    details = []
    
    if "air_temperature" in instant:
        temp = instant["air_temperature"]
        details.append(f"Temperature: {temp}°C")
    
    if "wind_speed" in instant:
        wind = instant["wind_speed"]
        details.append(f"Wind speed: {wind} m/s")
    
    if "relative_humidity" in instant:
        humidity = instant["relative_humidity"]
        details.append(f"Humidity: {humidity}%")
    
    if "precipitation_amount" in next_1h:
        precip = next_1h["precipitation_amount"]
        details.append(f"Precipitation: {precip} mm")
    
    if "summary" in next_1h:
        details.append(f"Summary: {next_1h['summary']}")
    
    return " | ".join(details) if details else "No specific weather details"


def get_system_prompt() -> str:
    """Get the system prompt with examples for ship log generation."""
    return """
Du er kaptein på en skute som seiler langs kysten på Sørlandet i Norge fra perioden 1500-1800.
Din oppgave er å skrive autentiske og kreative skipsdagbøker på norsk som er:
- Skrevet i autentisk stil fra gamle skipsdagbøker
- Basert på reelle værdata og geografiske koordinater
- Rimelig nøyaktige geografisk og meteorologisk
- Kreativ men troverdig - som fra en virkelig kaptein
- Ta gjerne med små dikt, historier
- Ta med observasjoner av naturen når det passer
- Signer med kapteinens navn


Eksempler på stilmåte fra gamle engelsk-norske skipsdagbøker:

9th Monday First part of these 24 hours commences with moderate breezy. Tack ship she knock off. At 8 tack ship again. Middle part tack ship. After Dinner set Top gallant sail and fly jib. Latter part furled top gallants and fly jib. So ends with a stiff breeze. Latt 19=56

10th Tuesday First part of these 24 hours commences with a stiff breezze. Middle part tack ship after dinner. Tack to the westward. Latter part tack to the eastward. Steering E by S.   Lat 14.30N Long 162-12 West

Oktober 10, 1827: Gode handelsvinder med pent vær. Fortopmast-seilene ut. Styrende SE.
Natt stormfull. Tok inn seil.

Oktober 11: Fine briser, behagelig vær. Ingenting verdt å merke. Styrende SE ved Ø.

Oktober 12: Vakkert vær. Lett bris. Styrende SE ved Ø. Natt: Kastet jardene. Kurs SW. 
Endret kurs på grunn av at vi befant oss ved kysten av Barbaria. Ti grader østover fra der vi burde være, 
på grunn av en feil i månefasene.

Oktober 13: Klart vær. Moderat vinder. Alt seil satt. Så delfiner og krysset grønt vann.
Bredde 19°4' Lengde 14°16'

Oktober 14: Vannet er igjen farget dypgrønt. Mellom 3-4 på ettermiddagen så vi en stor pottfisk. 
Senket ned 3 båter. Sjøen går høyt. Kunne ikke komme innpå den. Satte all seil igjen og fortsatte kursen. 
Vinden gunstig. Vær: Skyet. Slutt.

November 15, Fredag kveld (Dag 118)

Etter en uke med liten fremgang og tiltagende frustrasjon i mannskapet, samlet vi oss ved baugen under lanternens skinn. **Fallo** leste høyt fra sin gamle bok med sjøfortellinger - en uvanlig ro senket seg over skuta, selv med skipets skråstilling. **Peter** og **Astrid** gjorde et nytt forsøk på å sondere bunnen med provisorisk dregg, uten hell. Vinden dreide vestlig, men forble svak.

April, Lørdag (Dag 119)

Tidlig morgen med dis og fukt i tauverket. Temperaturen rundt 11 °C.
**Farfar** tok initiativ til å bygge en lettere rampe for å frakte redskaper fra lasterommet opp på dekk, og **Marit** organiserte proviant og gjorde telling av brød og fisk.

Vinden tok seg noe opp til 5 m/s fra sørvest. **Peter** og jeg forsøkte å vippe skuta med hjelp av jolle og tau - uten resultat. Vi observerte måkeskrik og et glimt av en **havørn** i nord.

På ettermiddagen samlet vi drivved og laget bål på berget. **Astrid** kokte fiskesuppe, og **Fallo** delte ut tørket eple. Stemningen steg.


"""


def generate_ship_log(
    location_name: str,
    location_details: str,
    coordinates: tuple[float, float],
    weather_desc: str,
    model: str = "gemma4:31b-cloud"
) -> str:
    """Generate a ship log entry using Ollama."""
    
    lon, lat = coordinates
    
    prompt = f"""
PLASSERING:
- Stedsnavn: {location_name}
- Detaljer: {location_details}
- Koordinater: {lat}°, {lon}°
- Region: Kysten av Sørlandet, Norge

VÆRDATA:
{weather_desc}

Skriv en kreativ og troverdig dagbokoppføring (3-15 linjer). 

SKRIV KUN DAGBOKOPPFERINGEN, IKKE METADATA.
"""

    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            system=get_system_prompt(),
            stream=False,
        )
        return response.get("response", "").strip()
    except Exception as e:
        print(f"Error generating log entry: {e}", file=sys.stderr)
        return ""


def save_to_markdown(log_entry: str, metadata: dict) -> str:
    """Save log entry to markdown file with datetime in filename."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = logs_dir / f"skipsdagbok_{timestamp}.md"
    
    content = f"""# Skipsdagbokoppføring
**Dato**: {datetime.now().isoformat()}

## Plassering
- **Navn**: {metadata.get('location_name', 'N/A')}
- **Koordinater**: {metadata.get('latitude', 'N/A')}°, {metadata.get('longitude', 'N/A')}°
- **Region**: Sørlandske fjorder

## Værdata
{metadata.get('weather', 'N/A')}

## Dagbokoppføring
{log_entry}
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Update registry
    update_registry(filename)
    return str(filename)


def update_registry(filename: str) -> None:
    """Add filename to registry.json."""
    registry_file = Path("registry.json")
    
    # Initialize with empty registry
    registry = {"entries": []}
    
    # Try to load existing registry, but handle corruption gracefully
    if registry_file.exists():
        try:
            with open(registry_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "entries" in data:
                    registry = data
        except (json.JSONDecodeError, ValueError):
            # Registry is corrupted, start fresh
            print("Warning: registry.json was corrupted, starting fresh", file=sys.stderr)
            registry = {"entries": []}
    
    # Ensure filename is a string
    filename_str = str(filename)
    
    registry["entries"].append({
        "filename": filename_str,
        "timestamp": datetime.now().isoformat()
    })
    
    # Write to temporary file first, then rename (atomic operation)
    temp_file = registry_file.with_suffix(".json.tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        # Atomic rename
        temp_file.replace(registry_file)
    except Exception as e:
        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()
        print(f"Error updating registry: {e}", file=sys.stderr)


def call_webhook(log_entry: str, metadata: dict, webhook_url: str) -> bool:
    """Send log entry to webhook endpoint."""
    payload = {
        "timestamp": datetime.now().isoformat(),
        "location": metadata.get("location_name"),
        "coordinates": {
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude")
        },
        "log_entry": log_entry
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending to webhook: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate creative ship log entries in Norwegian"
    )
    parser.add_argument(
        "--output",
        choices=["shell", "markdown", "webhook"],
        default="shell",
        help="Output method (default: shell)"
    )
    parser.add_argument(
        "--webhook-url",
        help="Webhook URL for output (required if --output webhook)"
    )
    parser.add_argument(
        "--model",
        #default="gemma4:31b-cloud",
        default="gemma4:31b-cloud",
        help="Ollama model to use (default: gemma4:31b-cloud)"
    )
    
    args = parser.parse_args()
    
    # Load data
    geojson = load_geojson()
    location_props, coords = select_random_location(geojson)
    
    # Extract location info
    lon, lat = coords
    location_name = location_props.get("navn", "Ukjent")
    location_details = f"{location_props.get('sted', '')} - {location_props.get('beliggenhet', '')}"
    
    # Fetch weather
    weather_data = fetch_weather_data(lat, lon)
    weather_desc = format_weather_description(weather_data)
    
    # Generate log entry
    log_entry = generate_ship_log(
        location_name,
        location_details,
        coords,
        weather_desc,
        model=args.model
    )
    
    if not log_entry:
        print("Error: Failed to generate log entry", file=sys.stderr)
        sys.exit(1)
    
    # Prepare metadata
    metadata = {
        "location_name": location_name,
        "latitude": lat,
        "longitude": lon,
        "weather": weather_desc
    }
    
    # Output
    if args.output == "shell":
        print(f"📍 {location_name} ({lat}°, {lon}°)")
        print(f"🌦️  {weather_desc}\n")
        print("📖 Dagbokoppføring:")
        print(log_entry)
    
    elif args.output == "markdown":
        filename = save_to_markdown(log_entry, metadata)
        print(f"✅ Saved to: {filename}")
    
    elif args.output == "webhook":
        if not args.webhook_url:
            print("Error: --webhook-url required for webhook output", file=sys.stderr)
            sys.exit(1)
        
        success = call_webhook(log_entry, metadata, args.webhook_url)
        if success:
            print("✅ Sent to webhook")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
