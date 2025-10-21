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
        # Disable duplicate checking for this test
        transactions = import_bank_data.import_and_parse(nordea_csv_path, check_duplicates=False)
        
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
        
        transactions = import_bank_data.import_and_parse(str(empty_file), check_duplicates=False)
        assert len(transactions) == 0, "Tom fil borde ge inga transaktioner"

    def test_nordea_with_missing_description(self, tmp_path):
        """Test Nordea CSV med saknad Rubrik-kolumn."""
        csv_content = """Bokföringsdatum,Belopp,Avsändare,Mottagare,Valuta
2025-01-15,-350.50,Robin Eklund,ICA Maxi,SEK"""
        
        file_path = tmp_path / "nordea_no_rubrik.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        
        # Borde fortfarande kunna importera med Avsändare/Mottagare som beskrivning
        transactions = import_bank_data.import_and_parse(str(file_path), check_duplicates=False)
        assert len(transactions) == 1
        # Beskrivningen borde komma från antingen Avsändare eller Mottagare
        assert transactions[0].description is not None

    def test_nordea_semicolon_separated(self, tmp_path):
        """Test Nordea CSV med semikolon-separator (verkligt Nordea-format)."""
        csv_content = """Bokföringsdag;Belopp;Avsändare;Mottagare;Namn;Rubrik;Saldo;Valuta
2025/10/21;-500,00;1709 20 72840;;;Swish betalning MICKES DÄCK;4995,52;SEK
2025/10/21;-3737,50;1709 20 72840;;;Autogiro K*jb-bildemo;5495,52;SEK"""
        
        file_path = tmp_path / "nordea_semicolon.csv"
        file_path.write_text(csv_content, encoding='utf-8-sig')  # Med BOM
        
        transactions = import_bank_data.import_and_parse(str(file_path), check_duplicates=False)
        assert len(transactions) == 2, f"Förväntade 2 transaktioner men fick {len(transactions)}"
        
        # Kontrollera första transaktionen
        first = transactions[0]
        assert first.date == date(2025, 10, 21)
        assert first.amount == Decimal('-500.00')
        assert 'Swish' in first.description or 'MICKES DÄCK' in first.description
        assert first.currency == "SEK"
        
        # Kontrollera andra transaktionen med komma-decimal
        second = transactions[1]
        assert second.amount == Decimal('-3737.50')
        assert 'Autogiro' in second.description

    def test_duplicate_file_detection(self, tmp_path, monkeypatch):
        """Test att samma fil inte importeras två gånger."""
        # Setup en temporär accounts-databas
        temp_accounts_path = tmp_path / "accounts.yaml"
        from budgetagent.modules import account_manager
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        
        # Skapa en testfil
        csv_content = """Bokföringsdatum,Valutadatum,Belopp,Avsändare,Mottagare,Rubrik,Valuta
2025-01-15,2025-01-15,-350.50,Robin Eklund,ICA Maxi,Matinköp,SEK
2025-01-16,2025-01-16,-120.00,Robin Eklund,Circle K,Bensin,SEK"""
        
        file_path = tmp_path / "test_nordea_dup.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        
        # Importera första gången
        transactions1 = import_bank_data.import_and_parse(str(file_path))
        assert len(transactions1) == 2, "Första importen borde ge 2 transaktioner"
        
        # Importera andra gången - borde ge 0 transaktioner
        transactions2 = import_bank_data.import_and_parse(str(file_path))
        assert len(transactions2) == 0, "Andra importen borde ge 0 transaktioner (redan importerad)"

    def test_duplicate_transaction_detection(self, tmp_path, monkeypatch):
        """Test att samma transaktioner inte importeras två gånger."""
        # Setup en temporär accounts-databas
        temp_accounts_path = tmp_path / "accounts.yaml"
        from budgetagent.modules import account_manager
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        
        # Skapa första filen med samma kontonamn i filnamnet
        csv_content1 = """Bokföringsdatum,Valutadatum,Belopp,Avsändare,Mottagare,Rubrik,Valuta
2025-01-15,2025-01-15,-350.50,Robin Eklund,ICA Maxi,Matinköp,SEK
2025-01-16,2025-01-16,-120.00,Robin Eklund,Circle K,Bensin,SEK"""
        
        file_path1 = tmp_path / "PERSONKONTO 1234 - 2025-01-15.csv"
        file_path1.write_text(csv_content1, encoding='utf-8')
        
        # Importera första filen
        transactions1 = import_bank_data.import_and_parse(str(file_path1))
        assert len(transactions1) == 2
        
        # Skapa andra filen med samma kontonamn och en ny och en dubblett-transaktion
        csv_content2 = """Bokföringsdatum,Valutadatum,Belopp,Avsändare,Mottagare,Rubrik,Valuta
2025-01-16,2025-01-16,-120.00,Robin Eklund,Circle K,Bensin,SEK
2025-01-17,2025-01-17,-75.00,Robin Eklund,Apotek,Medicin,SEK"""
        
        file_path2 = tmp_path / "PERSONKONTO 1234 - 2025-01-17.csv"
        file_path2.write_text(csv_content2, encoding='utf-8')
        
        # Importera andra filen - borde bara få en transaktion (den nya)
        transactions2 = import_bank_data.import_and_parse(str(file_path2))
        assert len(transactions2) == 1, "Andra importen borde ge 1 ny transaktion (en är dubblett)"
        assert transactions2[0].amount == Decimal('-75.00'), "Den nya transaktionen borde vara från Apotek"
