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
from .models import Bill


def add_bill(bill: Bill) -> None:
    """
    Lägger till ny faktura i YAML.
    
    Registrerar en ny kommande faktura med alla nödvändiga detaljer
    och sparar den i YAML-konfigurationsfilen.
    
    Args:
        bill: Bill-objekt med fakturainformation
    """
    pass


def get_upcoming_bills(month: str) -> List[Bill]:
    """
    Returnerar alla fakturor för vald månad.
    
    Hämtar och filtrerar fakturor som förfaller under den angivna månaden.
    
    Args:
        month: Månad i format YYYY-MM
        
    Returns:
        Lista med Bill-objekt
    """
    pass


def validate_bill_format(bill: Bill) -> bool:
    """
    Säkerställer korrekt struktur.
    
    Validerar att en faktura har alla nödvändiga fält och
    att de har korrekt format och värden. Pydantic validerar
    automatiskt, men denna funktion kan lägga till extra affärslogik.
    
    Args:
        bill: Bill-objekt att validera
        
    Returns:
        True om fakturastrukturen är korrekt, annars False
    """
    pass
