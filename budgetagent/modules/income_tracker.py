"""
Modul för registrering av inkomster per person, både återkommande och engångs.

Denna modul hanterar spårning av inkomster för olika personer i hushållet.
Den stödjer både återkommande inkomster (t.ex. lön) och engångsinkomster
(t.ex. frilansuppdrag eller bonus).

Exempel på YAML-konfiguration (income_tracker.yaml):
    income_tracker:
      people:
        - name: "Robin"
          recurring_income:
            - source: "Lön"
              amount: 28000
              frequency: "monthly"
          one_time_income:
            - source: "Frilans"
              amount: 5000
              date: "2025-12-10"
"""

from typing import Dict, Optional


def add_income(person: str, source: str, amount: float, date: str, recurring: bool) -> None:
    """
    Sparar inkomst i YAML.
    
    Registrerar en ny inkomst för en person och sparar den i
    YAML-konfigurationsfilen.
    
    Args:
        person: Personens namn
        source: Inkomstkälla, t.ex. "Lön", "Frilans"
        amount: Belopp i kronor
        date: Datum i format YYYY-MM-DD (används för engångsinkomster)
        recurring: True för återkommande, False för engång
    """
    pass


def get_monthly_income(person: str, month: str) -> float:
    """
    Summerar inkomster för vald månad.
    
    Beräknar total inkomst för en person under en specifik månad,
    inklusive både återkommande och engångsinkomster.
    
    Args:
        person: Personens namn
        month: Månad i format YYYY-MM
        
    Returns:
        Total inkomst i kronor för månaden
    """
    pass


def forecast_income(months: int) -> Dict:
    """
    Skapar framtida inkomstprognos.
    
    Genererar en prognos för framtida inkomster baserat på
    återkommande inkomster och planerade engångsinkomster.
    
    Args:
        months: Antal månader framåt att prognostisera
        
    Returns:
        Dictionary med prognostiserade inkomster per månad och person
    """
    pass
