"""
Modul för att tolka och besvara användarfrågor i naturligt språk.

Denna modul fungerar som en parser och controller för agentfrågor.
Den tolkar användarens fråga, identifierar intent och parametrar,
och anropar rätt moduler för att generera svar.

Stödjer frågor som:
- "Visa alla fakturor i december"
- "Hur mycket har vi kvar i januari?"
- "Vad händer om vi får 5000 kr extra?"
- "Hur mycket spenderar vi på mat per månad?"
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from .models import Bill, Income, Transaction, ForecastData, Scenario
from . import upcoming_bills, income_tracker, forecast_engine, alerts_and_insights


class QueryIntent:
    """
    Definierar olika typer av frågeintentioner.
    """
    SHOW_BILLS = "show_bills"
    SHOW_INCOME = "show_income"
    CALCULATE_BALANCE = "calculate_balance"
    FORECAST_SCENARIO = "forecast_scenario"
    CATEGORY_SPENDING = "category_spending"
    ALERT_CHECK = "alert_check"
    UNKNOWN = "unknown"


def parse_query(query: str) -> Dict[str, Any]:
    """
    Parsar användarfråga och identifierar intent och parametrar.
    
    Analyserar naturlig språkfråga och extraherar:
    - Intent (t.ex. "show_bills", "calculate_balance")
    - Parametrar (t.ex. månad, kategori, belopp)
    
    Args:
        query: Användarens fråga i naturligt språk
        
    Returns:
        Dictionary med "intent" och "params"
        
    Exempel:
        >>> parse_query("Visa alla fakturor i december")
        {"intent": "show_bills", "params": {"month": "december"}}
    """
    query_lower = query.lower()
    params = {}
    
    # Identifiera intent baserat på nyckelord
    if any(word in query_lower for word in ["faktura", "räkning", "bill", "fakturor"]):
        intent = QueryIntent.SHOW_BILLS
        # Extrahera månad om specificerad
        month = extract_month(query_lower)
        if month:
            params["month"] = month
            
    elif any(word in query_lower for word in ["inkomst", "lön", "income"]):
        intent = QueryIntent.SHOW_INCOME
        month = extract_month(query_lower)
        if month:
            params["month"] = month
            
    elif any(word in query_lower for word in ["kvar", "saldo", "balance"]):
        intent = QueryIntent.CALCULATE_BALANCE
        month = extract_month(query_lower)
        if month:
            params["month"] = month
            
    elif any(word in query_lower for word in ["vad händer om", "scenario", "extra"]):
        intent = QueryIntent.FORECAST_SCENARIO
        # Extrahera belopp
        amount = extract_amount(query_lower)
        if amount:
            params["amount"] = amount
        month = extract_month(query_lower)
        if month:
            params["month"] = month
            
    elif any(word in query_lower for word in ["spenderar", "utgift", "kostnad"]):
        intent = QueryIntent.CATEGORY_SPENDING
        # Extrahera kategori
        category = extract_category(query_lower)
        if category:
            params["category"] = category
            
    elif any(word in query_lower for word in ["varning", "alert", "problem"]):
        intent = QueryIntent.ALERT_CHECK
        
    else:
        intent = QueryIntent.UNKNOWN
    
    return {
        "intent": intent,
        "params": params,
        "original_query": query
    }


def extract_month(text: str) -> Optional[str]:
    """
    Extraherar månad från text.
    
    Letar efter månadsnamn i texten och returnerar standardiserat format.
    
    Args:
        text: Text att söka i
        
    Returns:
        Månad i format "YYYY-MM" eller månadsnamn, None om ingen månad hittas
    """
    months = {
        "januari": "01",
        "februari": "02",
        "mars": "03",
        "april": "04",
        "maj": "05",
        "juni": "06",
        "juli": "07",
        "augusti": "08",
        "september": "09",
        "oktober": "10",
        "november": "11",
        "december": "12"
    }
    
    for month_name, month_num in months.items():
        if month_name in text:
            current_year = datetime.now().year
            return f"{current_year}-{month_num}"
    
    return None


def extract_amount(text: str) -> Optional[float]:
    """
    Extraherar belopp från text.
    
    Letar efter numeriska belopp i texten, hanterar både
    heltal och decimaltal.
    
    Args:
        text: Text att söka i
        
    Returns:
        Belopp som float, None om inget belopp hittas
    """
    # Matcha belopp som "5000", "5000 kr", "5000.50"
    pattern = r'(\d+(?:[.,]\d+)?)\s*(?:kr|kronor)?'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '.')
        return float(amount_str)
    
    return None


def extract_category(text: str) -> Optional[str]:
    """
    Extraherar kategori från text.
    
    Letar efter kända utgiftskategorier i texten.
    
    Args:
        text: Text att söka i
        
    Returns:
        Kategorinamn eller None om ingen kategori hittas
    """
    categories = ["mat", "boende", "transport", "nöje", "försäkring", "kläder", "hälsa"]
    
    for category in categories:
        if category in text:
            return category.capitalize()
    
    return None


def execute_query(intent: str, params: Dict) -> str:
    """
    Exekverar tolkad fråga och returnerar svar.
    
    Anropar relevanta moduler baserat på intent och parametrar
    för att generera ett svar på användarens fråga.
    
    Args:
        intent: Identifierad intent från parse_query()
        params: Parametrar extraherade från frågan
        
    Returns:
        Svar som formaterad text
    """
    if intent == QueryIntent.SHOW_BILLS:
        return handle_show_bills(params)
    elif intent == QueryIntent.SHOW_INCOME:
        return handle_show_income(params)
    elif intent == QueryIntent.CALCULATE_BALANCE:
        return handle_calculate_balance(params)
    elif intent == QueryIntent.FORECAST_SCENARIO:
        return handle_forecast_scenario(params)
    elif intent == QueryIntent.CATEGORY_SPENDING:
        return handle_category_spending(params)
    elif intent == QueryIntent.ALERT_CHECK:
        return handle_alert_check(params)
    else:
        return ("Jag förstår tyvärr inte frågan. Försök med något som:\n"
                "- 'Visa alla fakturor i december'\n"
                "- 'Hur mycket har vi kvar i januari?'\n"
                "- 'Vad händer om vi får 5000 kr extra?'\n"
                "- 'Hur mycket spenderar vi på mat per månad?'")


def handle_show_bills(params: Dict) -> str:
    """
    Hanterar frågor om fakturor.
    
    Anropar upcoming_bills-modulen för att hämta och formatera
    information om kommande fakturor.
    
    Args:
        params: Parametrar som månad, kategori etc.
        
    Returns:
        Formaterad sträng med fakturainformation
    """
    from . import upcoming_bills
    
    month = params.get("month")
    bills = upcoming_bills.get_upcoming_bills(month) if month else upcoming_bills.get_upcoming_bills(None)
    
    if not bills:
        return f"Inga fakturor hittades{' för ' + month if month else ''}."
    
    result = f"Fakturor{' för ' + month if month else ''}:\n\n"
    total = 0
    for bill in bills:
        result += f"  • {bill.name:20s} {bill.amount:>8.2f} SEK  (förfaller {bill.due_date})\n"
        total += float(bill.amount)
    
    result += f"\nTotalt: {total:.2f} SEK"
    return result


def handle_show_income(params: Dict) -> str:
    """
    Hanterar frågor om inkomster.
    
    Args:
        params: Parametrar som månad, person etc.
        
    Returns:
        Formaterad sträng med inkomstinformation
    """
    month = params.get("month")
    if month:
        return f"Här är inkomsterna för {month}:\n(Implementation krävs)"
    else:
        return "Här är alla registrerade inkomster:\n(Implementation krävs)"


def handle_calculate_balance(params: Dict) -> str:
    """
    Hanterar frågor om saldo och ekonomisk situation.
    
    Args:
        params: Parametrar som månad etc.
        
    Returns:
        Formaterad sträng med saldoinformation
    """
    from . import forecast_engine
    from datetime import datetime
    
    month = params.get("month")
    
    # Generera prognos
    forecast = forecast_engine.simulate_monthly_balance(12)
    
    if month:
        # Hitta den specifika månaden
        for f in forecast:
            if f.date.strftime('%Y-%m') == month:
                return (f"Prognostiserat saldo för {month}:\n\n"
                       f"  Saldo: {f.balance:.2f} SEK\n"
                       f"  Inkomster: {f.income:.2f} SEK\n"
                       f"  Utgifter: {f.expenses:.2f} SEK\n"
                       f"  Netto: {f.income - f.expenses:.2f} SEK")
        return f"Ingen prognos tillgänglig för {month}"
    else:
        # Visa nuvarande månad
        current_month = datetime.now().strftime('%Y-%m')
        for f in forecast:
            if f.date.strftime('%Y-%m') == current_month:
                return (f"Prognostiserat saldo för innevarande månad ({current_month}):\n\n"
                       f"  Saldo: {f.balance:.2f} SEK\n"
                       f"  Inkomster: {f.income:.2f} SEK\n"
                       f"  Utgifter: {f.expenses:.2f} SEK")
        return "Ingen prognos tillgänglig för innevarande månad"


def handle_forecast_scenario(params: Dict) -> str:
    """
    Hanterar scenariofrågor ("vad händer om").
    
    Args:
        params: Parametrar som belopp, månad etc.
        
    Returns:
        Formaterad sträng med scenarioanalys
    """
    amount = params.get("amount", 0)
    month = params.get("month", "nästa månad")
    
    return f"Om ni får {amount} kr extra i {month}:\n(Implementation krävs)"


def handle_category_spending(params: Dict) -> str:
    """
    Hanterar frågor om utgifter per kategori.
    
    Args:
        params: Parametrar som kategori, period etc.
        
    Returns:
        Formaterad sträng med utgiftsinformation
    """
    from . import import_bank_data, categorize_expenses
    from pathlib import Path
    import yaml
    
    category = params.get("category", "alla kategorier")
    
    try:
        # Försök ladda exempel-data
        data_path = Path(__file__).parent.parent / "data" / "example_bank_data.csv"
        if data_path.exists():
            # Ladda kategoriseringsregler
            config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                rules = config.get('categories', {})
            
            # Importera och kategorisera
            transactions = import_bank_data.import_and_parse(str(data_path))
            categorized = categorize_expenses.categorize_transactions(transactions, rules)
            
            # Filtrera på kategori om specificerad
            if category != "alla kategorier":
                filtered = [t for t in categorized if t.category and t.category.lower() == category.lower()]
            else:
                filtered = categorized
            
            # Beräkna utgifter (negativa belopp)
            expenses = [t for t in filtered if t.amount < 0]
            
            if not expenses:
                return f"Inga utgifter hittades för {category}"
            
            total = sum(abs(float(t.amount)) for t in expenses)
            avg = total / len(expenses)
            
            return (f"Utgifter för {category}:\n\n"
                   f"  Totalt: {total:.2f} SEK\n"
                   f"  Antal transaktioner: {len(expenses)}\n"
                   f"  Genomsnitt per transaktion: {avg:.2f} SEK")
        else:
            return f"Utgifter för {category}: Ingen data tillgänglig"
    except Exception as e:
        return f"Kunde inte hämta utgifter: {e}"


def handle_alert_check(params: Dict) -> str:
    """
    Hanterar frågor om varningar och problem.
    
    Args:
        params: Parametrar för varningskontroll
        
    Returns:
        Formaterad sträng med varningar
    """
    return "Aktuella varningar:\n(Implementation krävs)"


def answer_query(query: str) -> str:
    """
    Huvudfunktion för att besvara en användarfråga.
    
    Kombinerar parsing och exekvering för att ge ett komplett svar.
    
    Args:
        query: Användarens fråga i naturligt språk
        
    Returns:
        Svar som formaterad text
    """
    parsed = parse_query(query)
    intent = parsed["intent"]
    params = parsed["params"]
    
    return execute_query(intent, params)
