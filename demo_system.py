#!/usr/bin/env python3
"""
Demo script som visar BudgetAgent-systemets funktionalitet.

Detta script demonstrerar hela arbetsflödet från import av transaktioner
till prognosgenerering och agentfrågor.
"""

import sys
from pathlib import Path
import yaml
from decimal import Decimal
from datetime import date

# Lägg till budgetagent till Python-sökvägen
sys.path.insert(0, str(Path(__file__).parent))

from budgetagent.modules.import_bank_data import import_and_parse
from budgetagent.modules.categorize_expenses import categorize_transactions
from budgetagent.modules.models import Bill, Income
from budgetagent.modules.upcoming_bills import add_bill, get_upcoming_bills
from budgetagent.modules.income_tracker import add_income, get_monthly_income, forecast_income
from budgetagent.modules.forecast_engine import simulate_monthly_balance
from budgetagent.modules.net_balance_splitter import split_balance
from budgetagent.modules.query_parser import answer_query
from budgetagent.modules.alerts_and_insights import check_budget_thresholds, generate_insights
from budgetagent.modules.models import AlertConfig

def print_section(title):
    """Hjälpfunktion för att skriva ut sektionstitlar."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def main():
    print_section("💸 BudgetAgent - Systemdemo")
    
    # 1. Importera och kategorisera transaktioner
    print_section("1. Import och kategorisering av transaktioner")
    
    # Ladda kategoriseringsregler
    with open('budgetagent/config/categorization_rules.yaml', 'r') as f:
        config = yaml.safe_load(f)
        rules = config['categories']
    
    # Importera transaktioner
    transactions = import_and_parse('budgetagent/data/example_bank_data.csv')
    print(f"✓ Importerade {len(transactions)} transaktioner")
    
    # Kategorisera
    categorized = categorize_transactions(transactions, rules)
    print(f"✓ Kategoriserade {len(categorized)} transaktioner\n")
    
    # Visa exempel
    print("Exempel på kategoriserade transaktioner:")
    for t in categorized[:5]:
        print(f"  {t.date}: {t.description:30s} -> {t.category:15s} ({t.amount} SEK)")
    
    # 2. Lägg till fakturor
    print_section("2. Hantering av kommande fakturor")
    
    bills_to_add = [
        Bill(
            name='Internet',
            amount=Decimal('399'),
            due_date=date(2025, 12, 15),
            category='Boende',
            recurring=True,
            frequency='monthly'
        ),
        Bill(
            name='Försäkring',
            amount=Decimal('450'),
            due_date=date(2025, 12, 20),
            category='Försäkring',
            recurring=True,
            frequency='monthly'
        )
    ]
    
    for bill in bills_to_add:
        try:
            add_bill(bill)
            print(f"✓ Lade till faktura: {bill.name} ({bill.amount} SEK)")
        except ValueError as e:
            print(f"  (Faktura redan tillagd eller fel: {e})")
    
    # Hämta fakturor för december
    december_bills = get_upcoming_bills('2025-12')
    print(f"\n✓ Totalt {len(december_bills)} fakturor för december 2025:")
    for bill in december_bills[:5]:
        print(f"  {bill.name:20s} {bill.amount:>8} SEK  (förfaller {bill.due_date})")
    
    # 3. Registrera inkomster
    print_section("3. Inkomstspårning")
    
    incomes_to_add = [
        Income(
            person='Robin',
            source='Lön',
            amount=Decimal('28000'),
            date=date(2025, 12, 25),
            recurring=True,
            frequency='monthly'
        ),
        Income(
            person='Partner',
            source='Lön',
            amount=Decimal('25000'),
            date=date(2025, 12, 25),
            recurring=True,
            frequency='monthly'
        )
    ]
    
    for income in incomes_to_add:
        try:
            add_income(income)
            print(f"✓ Registrerade inkomst: {income.person} - {income.source} ({income.amount} SEK)")
        except Exception as e:
            print(f"  (Inkomst redan registrerad eller fel: {e})")
    
    # 4. Generera prognos
    print_section("4. Ekonomisk prognos")
    
    forecast = simulate_monthly_balance(6)
    print(f"✓ Genererade 6-månaders prognos:\n")
    print(f"{'Månad':<12} {'Saldo':>12} {'Inkomster':>12} {'Utgifter':>12}")
    print("-" * 50)
    for f in forecast:
        print(f"{f.date.strftime('%Y-%m'):<12} {f.balance:>12.0f} {f.income:>12.0f} {f.expenses:>12.0f}")
    
    # 5. Saldofördelning
    print_section("5. Saldofördelning mellan personer")
    
    total_income = {'Robin': 28000, 'Partner': 25000}
    total_expenses = {'Robin': 15000, 'Partner': 12000}
    
    # Testa olika fördelningsregler
    rules_to_test = ['equal_split', 'income_weighted', 'needs_based']
    
    for rule in rules_to_test:
        distribution = split_balance(total_income, total_expenses, rule)
        print(f"\nFördelningsregel: {rule}")
        for person, amount in distribution.items():
            print(f"  {person:15s}: {amount:>10.2f} SEK")
    
    # 6. Varningar och insikter
    print_section("6. Varningar och insikter")
    
    # Skapa en enkel DataFrame för att testa
    import pandas as pd
    test_data = pd.DataFrame([
        {'date': date(2025, 11, 15), 'amount': -3500, 'description': 'Mat', 'category': 'Mat'},
        {'date': date(2025, 11, 16), 'amount': -1200, 'description': 'Transport', 'category': 'Transport'},
        {'date': date(2025, 11, 18), 'amount': -500, 'description': 'Nöje', 'category': 'Nöje'},
    ])
    
    # Generera insikter
    insights = generate_insights(test_data)
    print("Insikter från transaktionsdata:")
    for insight in insights:
        print(f"  {insight}")
    
    # 7. Agentfrågor
    print_section("7. Agentfrågor - Naturligt språkgränssnitt")
    
    queries = [
        "Visa alla fakturor i december",
        "Hur mycket har vi kvar i januari?",
        "Hur mycket spenderar vi på mat per månad?"
    ]
    
    for query in queries:
        print(f"\n❓ Fråga: {query}")
        response = answer_query(query)
        print(f"💬 Svar: {response}")
    
    # 8. Sammanfattning
    print_section("✅ Systemdemo slutförd")
    
    print("Alla moduler har körts framgångsrikt!")
    print("\nFör att starta den interaktiva dashboarden, kör:")
    print("  python start_dashboard.py")
    print("\nDashboarden kommer att vara tillgänglig på http://localhost:8050")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fel under demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
