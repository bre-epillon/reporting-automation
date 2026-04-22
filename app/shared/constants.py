LOB = [
    {"ENTOT": "Energy"},
    {"LITOT": "Life"},
    {"PRTOT": "Property"},
    {"DCTOT": "Discontinued"},
]

LOB_MAPPING = {
    "Energy": ["ENOFF", "ENONS", "ENCON", "ENOTH"],
    "Life": ["LIIND", "LIMLT", "LISHT", "LIMED"],
    "Property": ["PRTOT"],
    "Discontinued": [
        "DCMAR",
        "DCENR",
        "DCPRO",
        "DCBON",
        "DCFIL",
        "DCSPE",
        "DCLIA",
        "DCFRO",
    ],
}

SUBLOBS = [
    "ENOFF",
    "ENONS",
    "ENCON",
    "ENOTH",
    "LIIND",
    "LIMLT",
    "LISHT",
    "LIMED",
    "PRTOT",
    "DCMAR",
    "DCENR",
    "DCPRO",
    "DCBON",
    "DCFIL",
    "DCSPE",
    "DCLIA",
    "DCFRO",
]

YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

formats = {
    "millions": lambda x: f"{x / 1e6:.1f}m",
    "default": lambda x: f"{x:.2f}",
    "thousands": lambda x: f"{x / 1e3:.1f}k",
    "billions": lambda x: f"{x / 1e9:.2f}b",
}
