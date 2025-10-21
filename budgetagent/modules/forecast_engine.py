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
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    from decimal import Decimal
    
    if data.empty:
        return {}
    
    # Säkerställ att date-kolumnen är datetime
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
    else:
        return {}
    
    # Filtrera data till de senaste X månaderna
    cutoff_date = datetime.now() - relativedelta(months=window)
    filtered_data = data[data['date'] >= cutoff_date]
    
    # Filtrera endast utgifter (negativa belopp)
    expenses = filtered_data[filtered_data['amount'] < 0].copy()
    
    if expenses.empty:
        return {}
    
    # Gruppera per kategori och beräkna genomsnitt
    if 'category' not in expenses.columns:
        return {}
    
    # Konvertera belopp till absoluta värden för utgifter
    expenses['abs_amount'] = expenses['amount'].abs()
    
    # Gruppera per kategori och månad för att få månadsgenomsnitt
    expenses['month'] = expenses['date'].dt.to_period('M')
    monthly_by_category = expenses.groupby(['category', 'month'])['abs_amount'].sum().reset_index()
    
    # Beräkna genomsnitt per kategori
    averages = {}
    for category in monthly_by_category['category'].unique():
        category_data = monthly_by_category[monthly_by_category['category'] == category]
        avg = category_data['abs_amount'].mean()
        averages[category] = float(avg)
    
    return averages


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
    from decimal import Decimal
    from collections import defaultdict
    
    cashflow = defaultdict(lambda: {'income': Decimal(0), 'expenses': Decimal(0)})
    
    # Lägg till inkomster
    for inc in income:
        month_key = inc.date.strftime('%Y-%m')
        cashflow[month_key]['income'] += inc.amount
    
    # Lägg till fakturor
    for bill in bills:
        if not bill.paid:  # Endast obetalda fakturor
            month_key = bill.due_date.strftime('%Y-%m')
            cashflow[month_key]['expenses'] += bill.amount
    
    # Konvertera till vanlig dict med float-värden
    result = {}
    for month, values in cashflow.items():
        result[month] = {
            'income': float(values['income']),
            'expenses': float(values['expenses']),
            'net': float(values['income'] - values['expenses'])
        }
    
    return result


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
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from decimal import Decimal
    from . import income_tracker, upcoming_bills, parse_transactions, account_manager
    
    # Hämta framtida inkomster och fakturor
    future_income = income_tracker.forecast_income(months)
    
    # Ladda historiska transaktioner för att beräkna genomsnittliga utgifter
    historical_transactions = parse_transactions.load_transactions()
    
    # Konvertera till DataFrame för analys
    if historical_transactions:
        hist_data = pd.DataFrame([{
            'date': t.date,
            'amount': float(t.amount),
            'category': t.category
        } for t in historical_transactions])
        
        # Beräkna genomsnittliga utgifter från historik
        historical_avg = calculate_historical_average(hist_data, window=3)
        # Summera genomsnittliga utgifter per månad
        avg_monthly_expenses = sum(Decimal(str(v)) for v in historical_avg.values()) if historical_avg else Decimal(0)
    else:
        # Ingen historik finns - använd 0 istället för fallback
        avg_monthly_expenses = Decimal(0)
    
    # Ladda aktuellt totalt saldo från alla konton
    accounts = account_manager.load_accounts()
    current_balance = Decimal(0)
    
    if accounts:
        for account_name, account in accounts.items():
            if account.current_balance is not None:
                current_balance += account.current_balance
    
    forecast_data = []
    today = datetime.now().date()
    
    for month_offset in range(months):
        forecast_date = today + relativedelta(months=month_offset)
        month_key = forecast_date.strftime('%Y-%m')
        
        # Beräkna inkomster för månaden
        monthly_income = Decimal(0)
        for inc in future_income:
            if inc.date.strftime('%Y-%m') == month_key:
                monthly_income += inc.amount
        
        # Hämta fakturor för månaden
        monthly_bills = upcoming_bills.get_upcoming_bills(month_key)
        monthly_expenses = sum(bill.amount for bill in monthly_bills)
        
        # Lägg till genomsnittliga övriga utgifter (från historik)
        total_expenses = Decimal(monthly_expenses) + avg_monthly_expenses
        
        # Beräkna nytt saldo
        current_balance = current_balance + monthly_income - total_expenses
        
        # Skapa ForecastData-objekt
        forecast = ForecastData(
            date=forecast_date,
            balance=current_balance,
            income=monthly_income,
            expenses=total_expenses,
            category_breakdown={},
            confidence=0.8
        )
        forecast_data.append(forecast)
    
    return forecast_data


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
    results = {}
    
    for scenario in scenarios:
        # För varje scenario, kör en modifierad simulering
        # Detta är en förenklad implementation
        # I en fullständig version skulle vi modifiera inkomster/utgifter baserat på scenario
        
        forecast = simulate_monthly_balance(6)  # 6 månaders prognos
        
        # Applicera scenario-justeringar på prognosen
        # (förenklad - i verkligheten skulle vi modifiera underliggande data)
        for forecast_data in forecast:
            # Applicera inkomstjusteringar
            for person, adjustment in scenario.income_adjustments.items():
                forecast_data.income += adjustment
                forecast_data.balance += adjustment
            
            # Applicera utgiftsjusteringar
            for category, adjustment in scenario.expense_adjustments.items():
                forecast_data.expenses += adjustment
                forecast_data.balance -= adjustment
        
        results[scenario.name] = forecast
    
    return results
