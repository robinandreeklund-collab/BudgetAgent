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

from typing import Dict, Optional, List
from .models import Income


def add_income(income: Income) -> None:
    """
    Sparar inkomst i YAML.
    
    Registrerar en ny inkomst för en person och sparar den i
    YAML-konfigurationsfilen.
    
    Args:
        income: Income-objekt med inkomstinformation
    """
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "income_tracker.yaml"
    
    # Ladda befintlig data
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    
    if 'income_tracker' not in data:
        data['income_tracker'] = {'incomes': []}
    elif 'incomes' not in data['income_tracker']:
        data['income_tracker']['incomes'] = []
    
    # Konvertera Income till dictionary
    income_dict = {
        'person': income.person,
        'source': income.source,
        'amount': float(income.amount),
        'date': income.date.isoformat(),
        'recurring': income.recurring,
        'frequency': income.frequency,
        'category': income.category
    }
    
    # Lägg till inkomsten
    data['income_tracker']['incomes'].append(income_dict)
    
    # Spara tillbaka
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


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
    import yaml
    from pathlib import Path
    from datetime import datetime
    from decimal import Decimal
    
    config_path = Path(__file__).parent.parent / "config" / "income_tracker.yaml"
    
    if not config_path.exists():
        return 0.0
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'income_tracker' not in data or 'incomes' not in data['income_tracker']:
        return 0.0
    
    total = Decimal(0)
    
    for income_dict in data['income_tracker']['incomes']:
        # Filtrera på person
        if income_dict['person'] != person:
            continue
        
        # Parsa datum
        income_date = datetime.fromisoformat(income_dict['date']).date()
        income_month = income_date.strftime('%Y-%m')
        
        # Kontrollera om inkomsten är för rätt månad
        if income_dict.get('recurring', False):
            # Återkommande inkomst - inkludera om den startade före eller under månaden
            if income_month <= month:
                total += Decimal(str(income_dict['amount']))
        else:
            # Engångsinkomst - inkludera endast om den är exakt denna månad
            if income_month == month:
                total += Decimal(str(income_dict['amount']))
    
    return float(total)


def forecast_income(months: int) -> List[Income]:
    """
    Skapar framtida inkomstprognos.
    
    Genererar en prognos för framtida inkomster baserat på
    återkommande inkomster och planerade engångsinkomster.
    
    Args:
        months: Antal månader framåt att prognostisera
        
    Returns:
        Lista med prognostiserade Income-objekt per månad och person
    """
    import yaml
    from pathlib import Path
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    from decimal import Decimal
    
    config_path = Path(__file__).parent.parent / "config" / "income_tracker.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'income_tracker' not in data or 'incomes' not in data['income_tracker']:
        return []
    
    forecasted_incomes = []
    today = datetime.now().date()
    
    # Generera prognos för varje månad
    for month_offset in range(months):
        forecast_date = today + relativedelta(months=month_offset)
        
        # Gå igenom alla inkomster
        for income_dict in data['income_tracker']['incomes']:
            income_date = datetime.fromisoformat(income_dict['date']).date()
            
            if income_dict.get('recurring', False):
                # Återkommande inkomst - lägg till för varje månad
                frequency = income_dict.get('frequency', 'monthly')
                
                if frequency == 'monthly':
                    # Lägg till om startdatum är före eller under prognosmånaden
                    if income_date <= forecast_date:
                        forecasted_income = Income(
                            person=income_dict['person'],
                            source=income_dict['source'],
                            amount=Decimal(str(income_dict['amount'])),
                            date=forecast_date,
                            recurring=True,
                            frequency='monthly',
                            category=income_dict.get('category')
                        )
                        forecasted_incomes.append(forecasted_income)
                elif frequency == 'yearly':
                    # Lägg endast till om det är samma månad som startmånaden
                    if income_date.month == forecast_date.month and income_date <= forecast_date:
                        forecasted_income = Income(
                            person=income_dict['person'],
                            source=income_dict['source'],
                            amount=Decimal(str(income_dict['amount'])),
                            date=forecast_date,
                            recurring=True,
                            frequency='yearly',
                            category=income_dict.get('category')
                        )
                        forecasted_incomes.append(forecasted_income)
            else:
                # Engångsinkomst - lägg till endast om den är i framtiden och inom prognosperioden
                if income_date >= today and income_date <= (today + relativedelta(months=months)):
                    if income_date.year == forecast_date.year and income_date.month == forecast_date.month:
                        forecasted_income = Income(
                            person=income_dict['person'],
                            source=income_dict['source'],
                            amount=Decimal(str(income_dict['amount'])),
                            date=income_date,
                            recurring=False,
                            category=income_dict.get('category')
                        )
                        forecasted_incomes.append(forecasted_income)
    
    return forecasted_incomes
