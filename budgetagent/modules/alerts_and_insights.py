"""
Modul för generering av varningar och insikter baserat på regler och forecast.

Denna modul analyserar budgetdata och genererar automatiska varningar
när tröskelvärden överskrids samt ger insikter och rekommendationer
för att förbättra den ekonomiska situationen.

Exempel på YAML-konfiguration kan hämtas från settings_panel.yaml:
    settings_panel:
      alert_threshold:
        type: slider
        min: 0
        max: 100
        default: 80
        unit: "%"
"""

import pandas as pd
from typing import List, Dict
from .models import AlertConfig, Transaction, Bill


def check_budget_thresholds(data: pd.DataFrame, alert_config: AlertConfig) -> List[str]:
    """
    Kontrollerar budgettrösklar och genererar varningar, t.ex. "Matkostnad över 4000 kr!".
    
    Jämför faktiska utgifter mot definierade tröskelvärden och
    skapar varningsmeddelanden när gränser överskrids.
    
    Args:
        data: DataFrame med utgiftsdata
        alert_config: AlertConfig-objekt med tröskelvärden och inställningar
        
    Returns:
        Lista med varningsmeddelanden
    """
    alerts = []
    
    if data.empty or 'category' not in data.columns or 'amount' not in data.columns:
        return alerts
    
    # Filtrera utgifter (negativa belopp)
    expenses = data[data['amount'] < 0].copy()
    
    if expenses.empty:
        return alerts
    
    # Konvertera till absoluta värden
    expenses['abs_amount'] = expenses['amount'].abs()
    
    # Gruppera per kategori
    category_totals = expenses.groupby('category')['abs_amount'].sum()
    
    # Kontrollera mot kategorigränser
    for category, limit in alert_config.category_limits.items():
        if category in category_totals:
            actual = category_totals[category]
            if actual > float(limit):
                alerts.append(
                    f"⚠️ {category}: {actual:.2f} kr överstiger budgeten på {float(limit):.2f} kr"
                )
            elif actual > float(limit) * (alert_config.threshold_percentage / 100):
                percentage = (actual / float(limit)) * 100
                alerts.append(
                    f"⚡ {category}: {actual:.2f} kr ({percentage:.0f}% av budget)"
                )
    
    return alerts


def generate_insights(data: pd.DataFrame) -> List[str]:
    """
    Genererar insikter, t.ex. "Du spenderar 20% mer på nöje än genomsnittet".
    
    Analyserar utgiftsmönster och jämför med genomsnitt eller tidigare
    perioder för att ge användbar information.
    
    Args:
        data: DataFrame med utgiftsdata och historik
        
    Returns:
        Lista med insiktsmeddelanden
    """
    insights = []
    
    if data.empty or 'category' not in data.columns or 'amount' not in data.columns:
        return insights
    
    # Filtrera utgifter
    expenses = data[data['amount'] < 0].copy()
    
    if expenses.empty:
        return insights
    
    # Konvertera till absoluta värden
    expenses['abs_amount'] = expenses['amount'].abs()
    
    # Totala utgifter
    total_expenses = expenses['abs_amount'].sum()
    
    if total_expenses == 0:
        return insights
    
    # Utgifter per kategori
    category_totals = expenses.groupby('category')['abs_amount'].sum().sort_values(ascending=False)
    
    # Insikt 1: Största utgiftskategorin
    if not category_totals.empty:
        top_category = category_totals.index[0]
        top_amount = category_totals.iloc[0]
        top_percentage = (top_amount / total_expenses) * 100
        insights.append(
            f"💡 Din största utgiftskategori är {top_category} med {top_amount:.2f} kr ({top_percentage:.0f}% av totala utgifter)"
        )
    
    # Insikt 2: Antal transaktioner per kategori
    transaction_counts = expenses.groupby('category').size().sort_values(ascending=False)
    if not transaction_counts.empty:
        most_frequent = transaction_counts.index[0]
        count = transaction_counts.iloc[0]
        insights.append(
            f"📊 Du har flest transaktioner i kategorin {most_frequent} ({count} st)"
        )
    
    # Insikt 3: Genomsnittligt transaktionsbelopp
    avg_transaction = expenses['abs_amount'].mean()
    insights.append(
        f"💰 Genomsnittligt transaktionsbelopp: {avg_transaction:.2f} kr"
    )
    
    return insights


def recommend_actions(insight: str) -> str:
    """
    Rekommenderar åtgärder, t.ex. "Överväg att minska streamingkostnader".
    
    Baserat på en given insikt, generera konkreta rekommendationer
    för hur användaren kan förbättra sin ekonomiska situation.
    
    Args:
        insight: Insiktsmeddelande från generate_insights()
        
    Returns:
        Rekommendation som sträng
    """
    insight_lower = insight.lower()
    
    # Mönsterbaserade rekommendationer
    if 'nöje' in insight_lower or 'streaming' in insight_lower:
        return "💡 Rekommendation: Granska dina prenumerationstjänster och avsluta de du inte använder regelbundet."
    
    elif 'mat' in insight_lower or 'food' in insight_lower:
        return "💡 Rekommendation: Planera måltider i förväg och handla med lista för att minska impulsköp."
    
    elif 'transport' in insight_lower or 'bensin' in insight_lower:
        return "💡 Rekommendation: Överväg kollektivtrafik eller samåkning för att minska transportkostnader."
    
    elif 'kläder' in insight_lower or 'shopping' in insight_lower:
        return "💡 Rekommendation: Sätt en månatlig budget för kläder och vänta 24 timmar innan större köp."
    
    elif 'hälsa' in insight_lower:
        return "💡 Rekommendation: Kontrollera om du har rätt försäkringsskydd och använd förebyggande vård."
    
    else:
        return "💡 Rekommendation: Sätt upp en månadsbudget för denna kategori och följ upp regelbundet."
