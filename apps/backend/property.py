"""Address resolution for the backend: forward (address -> property) and
reverse (lat/lon -> property) geocoding, plus Portland zoning lookup."""

from __future__ import annotations

import json
import os
import ssl
import urllib.parse
import urllib.request

import certifi

MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")
_CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
_MAPBOX = "https://api.mapbox.com/geocoding/v5/mapbox.places"
_ZONING = "https://www.portlandmaps.com/arcgis/rest/services/Public/Zoning/MapServer"
_SSL = ssl.create_default_context(cafile=certifi.where())
_TIMEOUT = 8


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "permitPDX/1.0"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_SSL) as r:  # noqa: S310
        return json.loads(r.read().decode())


def _query_layer(layer: int, lon: float, lat: float) -> dict:
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    q = urllib.parse.urlencode({
        "geometry": geom, "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
        "returnGeometry": "false", "f": "json",
    })
    feats = _get_json(f"{_ZONING}/{layer}/query?{q}").get("features", [])
    return feats[0].get("attributes", {}) if feats else {}


def _pick(attrs: dict, *keys: str) -> str:
    for k in keys:
        for actual, val in attrs.items():
            if actual.upper() == k.upper() and val not in (None, "", " "):
                return str(val)
    return ""


def _zoning(lon: float, lat: float) -> dict:
    out = {"zone": "", "zone_desc": "", "overlays": "", "comp_plan": ""}
    try:
        z = _query_layer(0, lon, lat)
        out["zone"] = _pick(z, "ZONE", "ZONING", "CLASS_DESC", "ZONE_CLASS")
        out["zone_desc"] = _pick(z, "ZONE_DESC", "ZONE_NAME", "DESCRIPTION")
        out["overlays"] = _pick(z, "OVERLAY", "OVRLY", "ZONE_OVERLAY")
    except Exception:  # noqa: BLE001
        pass
    try:
        out["comp_plan"] = _pick(
            _query_layer(50, lon, lat), "CMP_DESC", "COMP_PLAN", "DESCRIPTION"
        )
    except Exception:  # noqa: BLE001
        pass
    return out


def resolve_address(address: str) -> dict:
    """Forward geocode an address and attach Portland zoning context."""
    full = address.strip()
    if "portland" not in full.lower():
        full = f"{full}, Portland, OR"
    q = urllib.parse.urlencode(
        {"address": full, "benchmark": "Public_AR_Current", "format": "json"}
    )
    matches = _get_json(f"{_CENSUS}?{q}").get("result", {}).get("addressMatches", [])
    if not matches:
        return {"error": f"Could not find address: {address}"}
    m = matches[0]
    lon, lat = m["coordinates"]["x"], m["coordinates"]["y"]
    return {"address": m.get("matchedAddress", address), "lat": lat, "lon": lon,
            **_zoning(lon, lat)}


def reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocode a coordinate (Mapbox) and attach Portland zoning."""
    address = f"{lat:.5f}, {lon:.5f}"
    if MAPBOX_TOKEN:
        try:
            q = urllib.parse.urlencode({"access_token": MAPBOX_TOKEN, "types": "address"})
            feats = _get_json(f"{_MAPBOX}/{lon},{lat}.json?{q}").get("features", [])
            if feats:
                address = feats[0].get("place_name", address)
        except Exception:  # noqa: BLE001
            pass
    return {"address": address, "lat": lat, "lon": lon, **_zoning(lon, lat)}
