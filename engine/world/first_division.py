"""Memberships de primeira divisão usados como entrada de normalização.

As listas são fontes de importação versionadas; em runtime, somente os IDs
normalizados e persistidos no GameState são consumidos pelo motor.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class FirstDivisionSource:
    country_id: int
    country_code: str
    competition_name: str
    season_label: str
    clubs: tuple[str, ...]
    source_url: str


FIRST_DIVISION_SOURCES: tuple[FirstDivisionSource, ...] = (
    FirstDivisionSource(29, "BRA", "Campeonato Brasileiro Série A", "2026", (
        "Palmeiras", "Flamengo", "Athletico Paranaense", "Fluminense", "Cruzeiro", "Bahia", "Red Bull Bragantino", "Coritiba SAF", "Atlético Mineiro", "Corinthians", "Botafogo", "Vitória", "São Paulo", "Santos FC", "Grêmio", "Internacional", "Mirassol", "Remo", "Vasco da Gama Saf", "Chapecoense",
    ), "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a"),
    FirstDivisionSource(104, "ITA", "Serie A", "2026/27", (
        "Roma", "Inter", "Napoli", "Lecce", "Milan", "Atalanta", "Cagliari", "Juventus", "Lazio", "Como", "Udinese", "Sassuolo", "Torino", "Frosinone", "Parma", "Bologna", "Genoa", "Venezia", "Monza", "Fiorentina",
    ), "https://en.legaseriea.it/serie-a/standings"),
    FirstDivisionSource(65, "ESP", "LALIGA EA SPORTS", "2026/27", (
        "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Celta", "Deportivo Alavés", "Elche CF", "FC Barcelona", "Getafe CF", "Levante UD", "Málaga CF", "R. Racing Club", "Rayo Vallecano", "RC Deportivo", "RCD Espanyol de Barcelona", "Real Betis", "Real Madrid", "Real Sociedad", "Sevilla FC", "Valencia CF", "Villarreal CF",
    ), "https://www.laliga.com/en-GB/laliga-easports/clubs"),
    FirstDivisionSource(154, "POR", "Liga Portugal Betclic", "2025/26", (
        "Porto", "Sporting CP", "Benfica", "Braga", "Famalicão", "Gil Vicente", "Moreirense", "Arouca", "Vitória de Guimarães", "Estoril Praia", "Alverca", "Rio Ave", "Santa Clara", "Nacional", "Estrela da Amadora", "Casa Pia", "Tondela", "AVS",
    ), "https://pt.wikipedia.org/wiki/Primeira_Liga_de_2025%E2%80%9326"),
)


def normalize_club_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b(saf|fc|cf|sc|ac|ud|r\.?|rcd|rc|ca|cd|sd|futebol clube|club de futbol|clube)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


ALIASES = {
    normalize_club_name("Atlético Mineiro"): {"atletico mg", "atletico mineiro"},
    normalize_club_name("Athletico Paranaense"): {"athletico pr", "athletico paranaense", "atletico paranaense"},
    normalize_club_name("Vasco da Gama Saf"): {"vasco", "vasco da gama"},
    normalize_club_name("Coritiba SAF"): {"coritiba"},
    normalize_club_name("Red Bull Bragantino"): {"bragantino", "red bull bragantino", "rb bragantino"},
    normalize_club_name("Atlético de Madrid"): {"atletico madrid", "atletico de madrid"},
    normalize_club_name("Inter"): {"internazionale"},
    normalize_club_name("Como"): {"como 1907"},
    normalize_club_name("Udinese"): {"udinese calcio"},
    normalize_club_name("Parma"): {"parma calcio"},
    normalize_club_name("Athletic Club"): {"athletic bilbao"},
    normalize_club_name("Celta"): {"celta de vigo"},
    normalize_club_name("Deportivo Alavés"): {"alaves"},
    normalize_club_name("Villarreal CF"): {"villareal"},
    normalize_club_name("Braga"): {"sporting braga"},
    normalize_club_name("Estoril Praia"): {"estoril"},
    normalize_club_name("Estrela da Amadora"): {"estrela amadora"},
    normalize_club_name("AVS"): {"desportivo aves"},
    normalize_club_name("R. Racing Club"): {"racing santander", "racing club"},
    normalize_club_name("RC Deportivo"): {"deportivo la coruna", "deportivo"},
    normalize_club_name("RCD Espanyol de Barcelona"): {"espanyol", "rcd espanyol"},
    normalize_club_name("Vitória de Guimarães"): {"vitoria guimaraes", "vitoria de guimaraes"},
    normalize_club_name("Sporting CP"): {"sporting", "sporting cp"},
}


def resolve_first_division_members(connection, country_id: int) -> dict:
    source = next((item for item in FIRST_DIVISION_SOURCES if item.country_id == int(country_id)), None)
    if source is None:
        raise ValueError("FIRST_DIVISION_SOURCE_NOT_FOUND")
    rows = connection.execute("SELECT time_id,nome,pais_id FROM times WHERE pais_id=? ORDER BY time_id", (source.country_id,)).fetchall()
    by_name: dict[str, list[dict]] = {}
    for row in rows:
        by_name.setdefault(normalize_club_name(row[1]), []).append({"teamId": int(row[0]), "name": row[1], "countryId": int(row[2])})
    matched = []
    unmatched = []
    ambiguous = []
    for source_name in source.clubs:
        key = normalize_club_name(source_name)
        candidates = by_name.get(key, [])
        if not candidates:
            aliases = ALIASES.get(key, set())
            candidates = [item for candidate_key, values in by_name.items() if candidate_key in aliases for item in values]
        if len(candidates) == 1:
            matched.append({"sourceName": source_name, **candidates[0]})
        elif len(candidates) > 1:
            ambiguous.append({"sourceName": source_name, "candidates": candidates})
        else:
            unmatched.append(source_name)
    return {"countryId": source.country_id, "countryCode": source.country_code, "competitionName": source.competition_name, "seasonLabel": source.season_label, "sourceUrl": source.source_url, "expected": len(source.clubs), "matched": matched, "unmatched": unmatched, "ambiguous": ambiguous}
