"""
Modul för hantering av framtida fakturor med belopp, förfallodatum och kategori.

Denna modul hanterar registrering och spårning av kommande fakturor
och betalningar. Den använder YAML för persistent lagring av fakturor.

Exempel på YAML-konfiguration (upcoming_bills.yaml):
    upcoming_bills:
      bills:
        - name: "Elräkning"
          amount: 900
          due_date: "2025-11-30"
          category: "Boende"
        - name: "Internet"
          amount: 399
          due_date: "2025-11-15"
          category: "Boende"
"""

from typing import List, Dict


def add_bill(name: str, amount: float, due_date: str, category: str) -> None:
    """
    Lägger till ny faktura i YAML.
    
    Registrerar en ny kommande faktura med alla nödvändiga detaljer
    och sparar den i YAML-konfigurationsfilen.
    
    Args:
        name: Fakturans namn/beskrivning
        amount: Belopp i kronor
        due_date: Förfallodatum i format YYYY-MM-DD
        category: Kategori, t.ex. "Boende", "Nöje"
    """
    pass


def get_upcoming_bills(month: str) -> List[Dict]:
    """
    Returnerar alla fakturor för vald månad.
    
    Hämtar och filtrerar fakturor som förfaller under den angivna månaden.
    
    Args:
        month: Månad i format YYYY-MM
        
    Returns:
        Lista med fakturor som dictionary-objekt
    """
    pass


def validate_bill_format(bill: Dict) -> bool:
    """
    Säkerställer korrekt struktur.
    
    Validerar att en faktura har alla nödvändiga fält och
    att de har korrekt format och värden.
    
    Args:
        bill: Dictionary med fakturadata
        
    Returns:
        True om fakturastrukturen är korrekt, annars False
    """
    pass
