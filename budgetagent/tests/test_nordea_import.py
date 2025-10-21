"""
Test för Nordea CSV-import funktionalitet.

Testsuite för att verifiera att Nordea CSV-filer kan importeras
och parsas korrekt via import_bank_data-modulen.
"""

import pytest
import pandas as pd
from pathlib import Path
from decimal import Decimal
from datetime import date

from budgetagent.modules import import_bank_data


class TestNordeaImport:
    """Tester för Nordea CSV-import."""

    @pytest.fixture
    def nordea_csv_path(self, tmp_path):
        """Skapar en testfil med Nordea CSV-format."""
        csv_content = """Bokföringsdatum,Valutadatum,Belopp,Avsändare,Mottagare,Rubrik,Valuta
2025-01-15,2025-01-15,-350.50,Robin Eklund,ICA Maxi,Matinköp,SEK
2025-01-16,2025-01-16,-120.00,Robin Eklund,Circle K,Bensin,SEK
2025-01-25,2025-01-25,28000.00,Arbetsgivare AB,Robin Eklund,Lön,SEK"""
        
        file_path = tmp_path / "test_nordea.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        return str(file_path)

    def test_detect_nordea_format(self, nordea_csv_path):
        """Test att Nordea-format detekteras korrekt."""
        df = import_bank_data.load_file(nordea_csv_path)
        detected_format = import_bank_data.detect_format(df)
        assert detected_format == "Nordea", f"Förväntade Nordea men fick {detected_format}"

    def test_normalize_nordea_columns(self, nordea_csv_path):
        """Test att Nordea-kolumner normaliseras korrekt."""
        df = import_bank_data.load_file(nordea_csv_path)
        normalized = import_bank_data.normalize_columns(df, "Nordea")
        
        # Kontrollera att standardkolumnerna finns
        assert 'date' in normalized.columns
        assert 'amount' in normalized.columns
        assert 'description' in normalized.columns
        assert 'currency' in normalized.columns

    def test_import_nordea_transactions(self, nordea_csv_path):
        """Test att Nordea-transaktioner importeras korrekt."""
        transactions = import_bank_data.import_and_parse(nordea_csv_path)
        
        # Kontrollera att transaktioner importerades
        assert len(transactions) == 3, f"Förväntade 3 transaktioner men fick {len(transactions)}"
        
        # Kontrollera första transaktionen
        first = transactions[0]
        assert first.date == date(2025, 1, 15)
        assert first.amount == Decimal('-350.50')
        assert first.description == "Matinköp"
        assert first.currency == "SEK"
        
        # Kontrollera lön-transaktion
        income_transaction = transactions[2]
        assert income_transaction.amount == Decimal('28000.00')
        assert income_transaction.amount > 0, "Lön borde vara positiv"

    def test_import_empty_nordea_file(self, tmp_path):
        """Edge case: Tom Nordea CSV-fil."""
        empty_file = tmp_path / "empty_nordea.csv"
        empty_file.write_text("Bokföringsdatum,Valutadatum,Belopp,Rubrik,Valuta\n", encoding='utf-8')
        
        transactions = import_bank_data.import_and_parse(str(empty_file))
        assert len(transactions) == 0, "Tom fil borde ge inga transaktioner"

    def test_nordea_with_missing_description(self, tmp_path):
        """Test Nordea CSV med saknad Rubrik-kolumn."""
        csv_content = """Bokföringsdatum,Belopp,Avsändare,Mottagare,Valuta
2025-01-15,-350.50,Robin Eklund,ICA Maxi,SEK"""
        
        file_path = tmp_path / "nordea_no_rubrik.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        
        # Borde fortfarande kunna importera med Avsändare/Mottagare som beskrivning
        transactions = import_bank_data.import_and_parse(str(file_path))
        assert len(transactions) == 1
        # Beskrivningen borde komma från antingen Avsändare eller Mottagare
        assert transactions[0].description is not None

    def test_nordea_tab_separated_with_saldo(self, tmp_path):
        """Test Nordea CSV med tab-separator och Saldo-kolumn som valuta."""
        # Detta är det verkliga Nordea-formatet som användaren har
        csv_content = """Bokföringsdag\tBelopp\tAvsändare\tMottagare\tNamn\tRubrik\tSaldo\tValuta
2025-10-21\t-500\t1709 20 72840\t\tSwish betalning MICKES DÄCK\t4995,52\tSEK\t
2025-10-21\t-3737,5\t1709 20 72840\t\tAutogiro K*jb-bildemo\t5495,52\tSEK\t"""
        
        file_path = tmp_path / "nordea_tab.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        
        transactions = import_bank_data.import_and_parse(str(file_path))
        assert len(transactions) == 2, f"Förväntade 2 transaktioner men fick {len(transactions)}"
        
        # Kontrollera första transaktionen
        first = transactions[0]
        assert first.date == date(2025, 10, 21)
        assert first.amount == Decimal('-500')
        assert 'Swish' in first.description or 'MICKES DÄCK' in first.description
        assert first.currency == "SEK"
        
        # Kontrollera andra transaktionen med komma-decimal
        second = transactions[1]
        assert second.amount == Decimal('-3737.5')
        assert 'Autogiro' in second.description
