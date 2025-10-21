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
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    # Ladda befintliga fakturor
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    
    if 'upcoming_bills' not in data:
        data['upcoming_bills'] = {'bills': []}
    elif 'bills' not in data['upcoming_bills']:
        data['upcoming_bills']['bills'] = []
    
    # Konvertera Bill till dictionary
    bill_dict = {
        'name': bill.name,
        'amount': float(bill.amount),
        'due_date': bill.due_date.isoformat(),
        'category': bill.category,
        'recurring': bill.recurring,
        'frequency': bill.frequency,
        'paid': bill.paid
    }
    
    if bill.payment_date:
        bill_dict['payment_date'] = bill.payment_date.isoformat()
    
    # Lägg till fakturan
    data['upcoming_bills']['bills'].append(bill_dict)
    
    # Spara tillbaka
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def get_upcoming_bills(month: str) -> List[Bill]:
    """
    Returnerar alla fakturor för vald månad.
    
    Hämtar och filtrerar fakturor som förfaller under den angivna månaden.
    
    Args:
        month: Månad i format YYYY-MM
        
    Returns:
        Lista med Bill-objekt
    """
    import yaml
    from pathlib import Path
    from datetime import datetime
    from decimal import Decimal
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'upcoming_bills' not in data or 'bills' not in data['upcoming_bills']:
        return []
    
    bills = []
    for bill_dict in data['upcoming_bills']['bills']:
        try:
            # Parsa due_date
            due_date = datetime.fromisoformat(bill_dict['due_date']).date()
            
            # Filtrera på månad om specificerat
            if month:
                bill_month = due_date.strftime('%Y-%m')
                if bill_month != month:
                    continue
            
            # Konvertera till Bill-objekt
            payment_date = None
            if 'payment_date' in bill_dict and bill_dict['payment_date']:
                payment_date = datetime.fromisoformat(bill_dict['payment_date']).date()
            
            bill = Bill(
                name=bill_dict['name'],
                amount=Decimal(str(bill_dict['amount'])),
                due_date=due_date,
                category=bill_dict['category'],
                recurring=bill_dict.get('recurring', False),
                frequency=bill_dict.get('frequency'),
                paid=bill_dict.get('paid', False),
                payment_date=payment_date
            )
            bills.append(bill)
        except Exception as e:
            print(f"Kunde inte parsa faktura: {e}")
            continue
    
    return bills


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
    try:
        # Pydantic validerar automatiskt vid skapande
        # Extra affärslogik kan läggas till här
        
        # Kontrollera att namn inte är tomt
        if not bill.name or not bill.name.strip():
            return False
        
        # Kontrollera att belopp är positivt (redan validerat av Pydantic)
        if bill.amount <= 0:
            return False
        
        # Kontrollera att kategori finns
        if not bill.category or not bill.category.strip():
            return False
        
        # Om återkommande, måste frekvens anges
        if bill.recurring and not bill.frequency:
            return False
        
        # Om betald, måste betalningsdatum anges
        if bill.paid and not bill.payment_date:
            return False
        
        return True
    except Exception:
        return False
