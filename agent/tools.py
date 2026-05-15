"""Agent tools. `resolve_property` turns a street address into Portland
zoning context so the agent can give property-specific answers.

Both upstream services are free and need no API key:
  - US Census geocoder      → address to lat/lon
  - PortlandMaps ArcGIS     → lat/lon to zoning / comp-plan attributes
"""

from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request

import certifi
from strands import tool

_CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
_ZONING = "https://www.portlandmaps.com/arcgis/rest/services/Public/Zoning/MapServer"
_TIMEOUT = 8
_SSL = ssl.create_default_context(cafile=certifi.where())


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "permitPDX/1.0"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_SSL) as r:  # noqa: S310
        return json.loads(r.read().decode())


def _geocode(address: str) -> tuple[float, float, str] | None:
    """Address -> (lon, lat, matched_address) via the Census geocoder."""
    # The Census one-line geocoder needs city/state to match reliably.
    full = address.strip()
    if "portland" not in full.lower():
        full = f"{full}, Portland, OR"
    elif "or" not in full.lower().split("portland")[-1].lower():
        full = f"{full}, OR"
    q = urllib.parse.urlencode(
        {"address": full, "benchmark": "Public_AR_Current", "format": "json"}
    )
    data = _get_json(f"{_CENSUS}?{q}")
    matches = data.get("result", {}).get("addressMatches", [])
    if not matches:
        return None
    m = matches[0]
    c = m["coordinates"]
    return c["x"], c["y"], m.get("matchedAddress", address)


def _query_layer(layer: int, lon: float, lat: float) -> dict:
    """Return the attributes of the feature at (lon, lat) for an ArcGIS layer."""
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    q = urllib.parse.urlencode({
        "geometry": geom,
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
    })
    data = _get_json(f"{_ZONING}/{layer}/query?{q}")
    feats = data.get("features", [])
    return feats[0].get("attributes", {}) if feats else {}


def _pick(attrs: dict, *keys: str) -> str:
    """First non-empty value among the candidate attribute keys."""
    for k in keys:
        for actual, val in attrs.items():
            if actual.upper() == k.upper() and val not in (None, "", " "):
                return str(val)
    return ""


@tool
def resolve_property(address: str) -> dict:
    """Resolve a Portland street address to its zoning context.

    Use this when the user gives an address and the answer depends on the
    specific lot (zoning, overlays, comprehensive plan, historic status).

    Args:
        address: A street address in Portland, OR (e.g. "2819 SE Brooklyn St").

    Returns:
        A dict with: address, lat, lon, zone, zone_desc, overlays,
        comp_plan, historic. Fields are empty strings when unavailable.
    """
    geo = _geocode(address)
    if not geo:
        return {"error": f"Could not find address: {address}", "address": address}
    lon, lat, matched = geo

    result = {
        "address": matched,
        "lat": lat,
        "lon": lon,
        "zone": "",
        "zone_desc": "",
        "overlays": "",
        "comp_plan": "",
        "historic": "",
    }
    try:
        z = _query_layer(0, lon, lat)
        result["zone"] = _pick(z, "ZONE", "ZONING", "CLASS_DESC", "ZONE_CLASS")
        result["zone_desc"] = _pick(z, "ZONE_DESC", "ZONE_NAME", "DESCRIPTION")
        result["overlays"] = _pick(z, "OVERLAY", "OVRLY", "ZONE_OVERLAY")
    except Exception:  # noqa: BLE001 — zoning lookup is best-effort
        pass
    try:
        cp = _query_layer(50, lon, lat)
        result["comp_plan"] = _pick(cp, "CMP_DESC", "COMP_PLAN", "DESCRIPTION", "CLASS_DESC")
    except Exception:  # noqa: BLE001
        pass
    return result
