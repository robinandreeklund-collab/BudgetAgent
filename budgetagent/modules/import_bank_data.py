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
from typing import Optional, List
from .models import Transaction


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


def import_and_parse(file_path: str) -> List[Transaction]:
    """
    Importerar och konverterar bankdata till Transaction-objekt.
    
    Huvudfunktion som kombinerar filimport, formatdetektering och
    konvertering till standardiserade Transaction-objekt.
    
    Args:
        file_path: Sökväg till filen att importera
        
    Returns:
        Lista med Transaction-objekt
    """
    pass
