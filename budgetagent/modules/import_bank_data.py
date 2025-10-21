"""
Modul för import av bankutdrag från olika format (CSV, Excel, JSON).

Denna modul hanterar inläsning och normalisering av banktransaktioner från olika
svenska banker som Swedbank, SEB, Revolut och andra. Modulen identifierar automatiskt
bankformatet och standardiserar kolumnnamn för enhetlig vidare bearbetning.

Exempel på YAML-konfiguration (settings_panel.yaml):
    settings_panel:
      import_format:
        type: dropdown
        options: ["Swedbank CSV", "SEB Excel", "Revolut JSON"]
"""

import pandas as pd
from typing import Optional


def load_file(path: str) -> pd.DataFrame:
    """
    Läser in filen och returnerar rådata.
    
    Args:
        path: Sökväg till filen som ska läsas in
        
    Returns:
        DataFrame med rådata från filen
    """
    pass


def detect_format(data: pd.DataFrame) -> str:
    """
    Identifierar bankformat (Swedbank, SEB, Revolut etc.).
    
    Analyserar strukturen och innehållet i DataFrame för att identifiera
    vilken bank som har skapat utdraget.
    
    Args:
        data: DataFrame med rådata
        
    Returns:
        Sträng med banknamn, t.ex. "Swedbank", "SEB", "Revolut"
    """
    pass


def normalize_columns(data: pd.DataFrame, format: str) -> pd.DataFrame:
    """
    Standardiserar kolumnnamn till date, amount, description, currency.
    
    Konverterar bankspecifika kolumnnamn till standardiserade namn för
    enhetlig bearbetning i resten av systemet.
    
    Args:
        data: DataFrame med rådata
        format: Bankformat identifierat av detect_format()
        
    Returns:
        DataFrame med standardiserade kolumnnamn
    """
    pass
