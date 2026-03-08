"""Calcul de matrice de temps de trajet en voiture entre deux listes d'adresses.

Source temps: OSRM public (router.project-osrm.org).
Geocodage: Nominatim (OpenStreetMap).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
import time

import requests


OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MAX_COORDS_PER_REQUEST = 100


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float


def geocode_address(
    address: str,
    *,
    session: requests.Session,
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_seconds: float = 1.0,
) -> GeoPoint:
    """Geocode une adresse via Nominatim.

    Le parametre sleep_seconds aide a respecter le rate limit de Nominatim.
    """
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": user_agent}

    response = session.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    results = response.json()
    if not results:
        raise RuntimeError(f"Adresse introuvable: {address}")

    point = GeoPoint(lat=float(results[0]["lat"]), lon=float(results[0]["lon"]))

    if sleep_seconds > 0:
        time.sleep(sleep_seconds)

    return point


def _format_coords(points: Sequence[GeoPoint]) -> str:
    return ";".join(f"{p.lon},{p.lat}" for p in points)


def _osrm_table(
    sources: Sequence[GeoPoint],
    destinations: Sequence[GeoPoint],
    *,
    session: requests.Session,
) -> List[List[float]]:
    coords = list(sources) + list(destinations)
    if len(coords) > MAX_COORDS_PER_REQUEST:
        raise RuntimeError(
            f"Trop de coordonnees pour une requete: {len(coords)} > {MAX_COORDS_PER_REQUEST}"
        )

    sources_idx = ";".join(str(i) for i in range(len(sources)))
    destinations_idx = ";".join(
        str(i) for i in range(len(sources), len(sources) + len(destinations))
    )

    url = f"{OSRM_TABLE_URL}/{_format_coords(coords)}"
    params = {
        "sources": sources_idx,
        "destinations": destinations_idx,
        "annotations": "duration",
    }

    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "durations" not in data or data.get("code") not in ("Ok", None):
        raise RuntimeError(f"Reponse OSRM invalide: {data}")

    return data["durations"]


def _chunked(seq: Sequence[GeoPoint], size: int) -> Iterable[Sequence[GeoPoint]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def temps_trajet_matrice(
    origins: Sequence[str],
    destinations: Sequence[str],
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_seconds: float = 1.0,
) -> List[List[float]]:
    """Calcule la matrice des temps (en secondes) entre deux listes d'adresses.

    Retourne une matrice de taille len(origins) x len(destinations).
    """
    if not origins or not destinations:
        return [[0.0 for _ in destinations] for _ in origins]

    with requests.Session() as session:
        origin_points = [
            geocode_address(
                addr,
                session=session,
                user_agent=user_agent,
                sleep_seconds=sleep_seconds,
            )
            for addr in origins
        ]
        destination_points = [
            geocode_address(
                addr,
                session=session,
                user_agent=user_agent,
                sleep_seconds=sleep_seconds,
            )
            for addr in destinations
        ]

        max_sources = MAX_COORDS_PER_REQUEST - min(len(destination_points), MAX_COORDS_PER_REQUEST - 1)
        max_destinations = MAX_COORDS_PER_REQUEST - min(len(origin_points), MAX_COORDS_PER_REQUEST - 1)

        if len(origin_points) + len(destination_points) <= MAX_COORDS_PER_REQUEST:
            return _osrm_table(origin_points, destination_points, session=session)

        matrix: List[List[float]] = [
            [0.0 for _ in range(len(destination_points))] for _ in range(len(origin_points))
        ]

        for i, origin_chunk in enumerate(_chunked(origin_points, max(1, max_sources))):
            for j, dest_chunk in enumerate(
                _chunked(destination_points, max(1, max_destinations))
            ):
                block = _osrm_table(origin_chunk, dest_chunk, session=session)
                for oi, row in enumerate(block):
                    for dj, value in enumerate(row):
                        matrix[i * max_sources + oi][j * max_destinations + dj] = value

        return matrix


if __name__ == "__main__":
    # Exemple rapide d'utilisation.
    orig = ["EPFL, Lausanne", "Ecole Polytechnique, Palaiseau", "Lycée du Parc, Lyon"]
    dest = ["Gare Part-Dieu", "Gare de Genève", "Gare de Renens"]
    mat = temps_trajet_matrice(orig, dest)
    
    def format_time(seconds: float) -> str:
        res = ""
        if seconds >= 3600:
            res += f"{int(seconds // 3600)}h "
            seconds %= 3600
        if seconds >= 60:
            res += f"{int(seconds // 60)}m "
            seconds %= 60
        res += f"{int(seconds)}s"
        return res
    
    print("Matrice des temps de trajet:")
    print(" " * 33 + " | ".join(f"{d:>15}" for d in dest))
    for o, row in zip(orig, mat):
        print(f"{o:>30} | " + " | ".join(f"{format_time(value):>15}" for value in row))
