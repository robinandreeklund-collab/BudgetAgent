"""
Modul för simulering av framtida saldo baserat på historik och planerade inkomster/fakturor.

Denna modul hanterar prognostisering av framtida ekonomisk situation genom
att analysera historiska utgiftsmönster och kombinera dessa med planerade
inkomster och fakturor.

Exempel på YAML-konfiguration (forecast_engine.yaml):
    forecast_engine:
      historical_window: 6  # månader
      confidence_interval: 0.95
      category_averages:
        mat: 4500
        transport: 1200
        nöje: 2000
"""

import pandas as pd
from typing import Dict, List
from .models import Bill, Income, ForecastData, Scenario, Transaction


def calculate_historical_average(data: pd.DataFrame, window: int) -> Dict:
    """
    Beräknar genomsnitt per kategori.
    
    Analyserar historiska utgifter över ett specificerat tidsfönster
    och beräknar genomsnittliga utgifter per kategori.
    
    Args:
        data: DataFrame med historisk transaktionsdata
        window: Antal månader bakåt att inkludera i beräkningen
        
    Returns:
        Dictionary med genomsnittliga utgifter per kategori
    """
    pass


def inject_future_income_and_bills(income: List[Income], bills: List[Bill]) -> Dict:
    """
    Skapar framtida kassaflöde.
    
    Kombinerar planerade inkomster och fakturor för att skapa
    en prognos över framtida kassaflöde.
    
    Args:
        income: Lista med Income-objekt
        bills: Lista med Bill-objekt
        
    Returns:
        Dictionary med projicerat kassaflöde per månad
    """
    pass


def simulate_monthly_balance(months: int) -> List[ForecastData]:
    """
    Returnerar saldo per månad.
    
    Simulerar månatligt saldo framåt i tiden baserat på historiska
    genomsnitt och planerade in- och utbetalningar.
    
    Args:
        months: Antal månader framåt att simulera
        
    Returns:
        Lista med ForecastData-objekt per månad
    """
    pass


def compare_scenarios(scenarios: List[Scenario]) -> Dict[str, List[ForecastData]]:
    """
    Jämför olika scenarier, t.ex. "Vad händer om vi får 5000 kr extra i januari?".
    
    Kör simuleringar för olika hypotetiska scenarier och jämför resultaten
    för att stödja ekonomiskt beslutsfattande.
    
    Args:
        scenarios: Lista med Scenario-objekt
        
    Returns:
        Dictionary med scenarionamn som nyckel och prognosdata som värde
    """
    pass
