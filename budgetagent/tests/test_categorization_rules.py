"""
Test categorization rules.

Testsuite för categorize_expenses-modulen som hanterar automatisk och manuell
kategorisering av transaktioner baserat på nyckelord och regler.
"""

import pytest
import pandas as pd
import yaml
from pathlib import Path

# Funktioner att testa (importeras när de är implementerade)
# from budgetagent.modules.categorize_expenses import (
#     auto_categorize,
#     manual_override,
#     update_category_map,
# )


class TestAutoCategorize:
    """Tester för auto_categorize-funktionen."""

    def test_categorize_food_expenses(self):
        """Test att automatiskt kategorisera mat-utgifter."""
        # Exempel: transaktioner från ICA, Coop ska kategoriseras som "Mat"
        # TODO: Implementera test när auto_categorize är implementerad
        pass

    def test_categorize_transport_expenses(self):
        """Test att automatiskt kategorisera transport-utgifter."""
        # Exempel: SL, Uber ska kategoriseras som "Transport"
        # TODO: Implementera test när auto_categorize är implementerad
        pass

    def test_categorize_housing_expenses(self):
        """Test att automatiskt kategorisera boende-utgifter."""
        # TODO: Implementera test när auto_categorize är implementerad
        pass

    def test_categorize_with_empty_rules(self):
        """Edge case: Kategorisera utan regler."""
        # TODO: Implementera test för tom regeluppsättning
        pass

    def test_categorize_with_empty_data(self):
        """Edge case: Tom DataFrame."""
        empty_df = pd.DataFrame()
        # TODO: Implementera test för tom DataFrame
        pass

    def test_categorize_unknown_transaction(self):
        """Edge case: Transaktion som inte matchar någon regel."""
        # TODO: Implementera test för okänd transaktion
        pass


class TestManualOverride:
    """Tester för manual_override-funktionen."""

    def test_override_single_category(self):
        """Test att manuellt ändra en kategori."""
        # TODO: Implementera test när manual_override är implementerad
        pass

    def test_override_multiple_categories(self):
        """Test att manuellt ändra flera kategorier."""
        # TODO: Implementera test när manual_override är implementerad
        pass

    def test_override_with_empty_overrides(self):
        """Edge case: Tom override-dictionary."""
        # TODO: Implementera test för tom override
        pass

    def test_override_nonexistent_transaction(self):
        """Edge case: Försök överstyrning av transaktion som inte finns."""
        # TODO: Implementera test för felaktig överstyrning
        pass


class TestUpdateCategoryMap:
    """Tester för update_category_map-funktionen."""

    def test_add_new_category_rule(self):
        """Test att lägga till ny kategoriseringsregel."""
        # TODO: Implementera test när update_category_map är implementerad
        pass

    def test_update_existing_rule(self):
        """Test att uppdatera befintlig regel."""
        # TODO: Implementera test när update_category_map är implementerad
        pass

    def test_update_with_empty_rules(self):
        """Edge case: Tom regeluppsättning."""
        # TODO: Implementera test för tom regeluppsättning
        pass

    def test_update_with_invalid_format(self):
        """Edge case: Ogiltigt format på regler."""
        # TODO: Implementera test för ogiltigt format
        pass


class TestYAMLValidation:
    """Tester för YAML-konfigurationsvalidering."""

    def test_categorization_rules_yaml_structure(self):
        """Validera struktur på kategoriseringsregler."""
        # Exempel YAML-struktur som förväntas:
        # categories:
        #   mat:
        #     keywords: ["ica", "coop"]
        # TODO: Skapa och validera kategoriseringsregler-YAML om det inte finns
        pass

    def test_category_keywords_are_lists(self):
        """Validera att nyckelord är listor."""
        # TODO: Implementera validering av YAML-struktur
        pass

    def test_yaml_contains_common_categories(self):
        """Validera att vanliga kategorier finns (Mat, Transport, Boende)."""
        # TODO: Implementera validering av kategori-komplettering
        pass


class TestCategorization:
    """Integrationstester för kategoriseringslogik."""

    def test_full_categorization_workflow(self):
        """Test av hela kategoriseringsflödet: auto -> manual override."""
        # TODO: Implementera end-to-end test
        pass

    def test_case_insensitive_matching(self):
        """Test att matchning är case-insensitive."""
        # TODO: Implementera test för case-insensitivity
        pass

    def test_partial_keyword_matching(self):
        """Test att partiell matchning fungerar (t.ex. "ICA MAXI" matchar "ica")."""
        # TODO: Implementera test för partiell matchning
        pass

    def test_categorization_with_special_characters(self):
        """Edge case: Beskrivningar med specialtecken."""
        # TODO: Implementera test för specialtecken
        pass

    def test_categorization_with_empty_description(self):
        """Edge case: Tom beskrivning."""
        # TODO: Implementera test för tom beskrivning
        pass


class TestHybridCategorization:
    """Tester för hybrid-kategorisering med AI-fallback."""

    def test_rule_based_categorization_with_confidence(self):
        """Test att regelbaserad kategorisering ger högt säkerhetsvärde."""
        from budgetagent.modules.categorize_expenses import auto_categorize
        
        # Skapa testdata
        data = pd.DataFrame({
            'description': ['ICA Maxi Stockholm', 'Circle K Bensinmack'],
            'amount': [-350.50, -600.00]
        })
        
        # Ladda regler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        # Kategorisera
        result = auto_categorize(data, rules)
        
        # Verifiera kategorier och säkerhetsvärden
        assert result.loc[0, 'category'] == 'Mat'
        assert result.loc[0, 'confidence'] >= 0.9
        
        assert result.loc[1, 'category'] == 'Transport'
        assert result.loc[1, 'confidence'] >= 0.9

    def test_unknown_transaction_flagged_for_review(self):
        """Test att okända transaktioner flaggas för manuell granskning."""
        from budgetagent.modules.categorize_expenses import auto_categorize
        
        # Skapa testdata med okänd transaktion
        data = pd.DataFrame({
            'description': ['Okänd butik AB', 'ICA Stockholm'],
            'amount': [-100.00, -350.50]
        })
        
        # Ladda regler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        # Kategorisera
        result = auto_categorize(data, rules)
        
        # Verifiera att okänd transaktion flaggas
        assert result.loc[0, 'needs_review'] == True
        assert result.loc[0, 'confidence'] < 0.7
        
        # ICA ska inte flaggas (hög säkerhet)
        assert result.loc[1, 'needs_review'] == False

    def test_ai_fallback_for_unknown_transactions(self):
        """Test att AI-fallback används för okända transaktioner."""
        from budgetagent.modules.categorize_expenses import auto_categorize
        
        # Skapa testdata
        data = pd.DataFrame({
            'description': ['Helt okänd beskrivning'],
            'amount': [-100.00]
        })
        
        # Regler med AI-fallback aktiverad
        rules = {
            'config': {
                'use_rules': True,
                'use_ai_fallback': True,
                'confidence_threshold': 0.7,
                'ai_min_confidence': 0.5
            },
            'mat': {'keywords': ['ica', 'coop'], 'confidence': 0.95}
        }
        
        # Kategorisera
        result = auto_categorize(data, rules)
        
        # Verifiera att något värde finns (även om det är okategoriserad)
        assert pd.notna(result.loc[0, 'category'])
        assert 'confidence' in result.columns

    def test_get_transactions_needing_review(self):
        """Test att hämta transaktioner som behöver granskning."""
        from budgetagent.modules.categorize_expenses import (
            auto_categorize, get_transactions_needing_review
        )
        
        # Skapa testdata
        data = pd.DataFrame({
            'description': ['ICA Stockholm', 'Okänd transaktion', 'Circle K'],
            'amount': [-350.50, -100.00, -600.00]
        })
        
        # Ladda regler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        # Kategorisera
        categorized = auto_categorize(data, rules)
        
        # Hämta transaktioner som behöver granskning
        needs_review = get_transactions_needing_review(categorized)
        
        # Verifiera att minst okända transaktionen finns
        assert len(needs_review) >= 1
        assert any('Okänd' in desc for desc in needs_review['description'].values)

    def test_get_uncategorized_transactions(self):
        """Test att hämta okategoriserade transaktioner."""
        from budgetagent.modules.categorize_expenses import (
            auto_categorize, get_uncategorized_transactions
        )
        
        # Skapa testdata
        data = pd.DataFrame({
            'description': ['ICA Stockholm', 'Helt okänd butik XYZ'],
            'amount': [-350.50, -100.00]
        })
        
        # Regler utan AI-fallback
        rules = {
            'config': {
                'use_rules': True,
                'use_ai_fallback': False
            },
            'mat': {'keywords': ['ica'], 'confidence': 0.95}
        }
        
        # Kategorisera
        categorized = auto_categorize(data, rules)
        
        # Hämta okategoriserade
        uncategorized = get_uncategorized_transactions(categorized)
        
        # Verifiera att okänd transaktion är okategoriserad
        assert len(uncategorized) >= 1
        assert 'okänd' in uncategorized.iloc[0]['description'].lower()

    def test_confidence_threshold_configuration(self):
        """Test att säkerhetströskelvärde kan konfigureras."""
        from budgetagent.modules.categorize_expenses import auto_categorize
        
        # Skapa testdata
        data = pd.DataFrame({
            'description': ['Okänd butik'],
            'amount': [-100.00]
        })
        
        # Regler med lägre tröskelvärde
        rules = {
            'config': {
                'use_rules': True,
                'use_ai_fallback': True,
                'confidence_threshold': 0.3,  # Lägre tröskelvärde
                'ai_min_confidence': 0.2
            },
            'mat': {'keywords': ['ica'], 'confidence': 0.95}
        }
        
        # Kategorisera
        result = auto_categorize(data, rules)
        
        # Med lägre tröskelvärde kan AI-fallback ge resultat utan flaggning
        assert pd.notna(result.loc[0, 'category'])

    def test_categorize_transactions_with_confidence(self):
        """Test att categorize_transactions returnerar säkerhetsvärden."""
        from budgetagent.modules.categorize_expenses import categorize_transactions
        from budgetagent.modules.models import Transaction
        from datetime import date
        from decimal import Decimal
        
        # Skapa testdata
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                amount=Decimal('-350.50'),
                description='ICA Maxi Stockholm',
                currency='SEK'
            ),
            Transaction(
                date=date(2025, 1, 16),
                amount=Decimal('-100.00'),
                description='Okänd butik',
                currency='SEK'
            )
        ]
        
        # Ladda regler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        # Kategorisera
        result = categorize_transactions(transactions, rules)
        
        # Verifiera att metadata innehåller säkerhetsvärden
        assert 'confidence' in result[0].metadata
        assert float(result[0].metadata['confidence']) >= 0.9
        
        # Okänd transaktion ska ha needs_review
        assert 'needs_review' in result[1].metadata or result[1].category == 'Okategoriserad'
