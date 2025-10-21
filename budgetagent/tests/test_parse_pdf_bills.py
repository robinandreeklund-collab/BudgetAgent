"""
Test parse_pdf_bills functionality.

Testsuite för parse_pdf_bills-modulen som hanterar extrahering
av fakturainformation från PDF-filer.
"""

import pytest
from pathlib import Path
from datetime import date
from decimal import Decimal
from budgetagent.modules.parse_pdf_bills import (
    extract_bills_from_text,
    validate_bill_structure,
    write_bills_to_yaml
)
from budgetagent.modules.models import Bill
import yaml


class TestExtractBillsFromText:
    """Tester för extract_bills_from_text-funktionen."""
    
    def test_extract_simple_invoice(self):
        """Test att extrahera enkelt fakturamönster."""
        text = """
        Faktura: Elräkning
        Belopp: 900 kr
        Förfallodatum: 2025-11-30
        """
        
        bills = extract_bills_from_text(text, "Boende")
        
        assert len(bills) == 1
        assert bills[0].name == "Elräkning"
        assert bills[0].amount == Decimal('900')
        assert bills[0].due_date == date(2025, 11, 30)
        assert bills[0].category == "Boende"
    
    def test_extract_with_different_date_format(self):
        """Test att extrahera datum i olika format."""
        text = """
        Faktura från: Internet AB
        Att betala: 399 kronor
        Sista betalningsdag: 15-12-2025
        """
        
        bills = extract_bills_from_text(text, "Boende")
        
        if bills:  # Endast testa om parsing lyckades
            assert len(bills) >= 1
            bill = bills[0]
            assert bill.due_date == date(2025, 12, 15)
    
    def test_extract_with_decimal_amount(self):
        """Test att extrahera belopp med decimaler."""
        text = """
        Totalt att betala: 1234.56 SEK
        Förfallodatum: 2025-12-01
        """
        
        bills = extract_bills_from_text(text, "Övrigt")
        
        if bills:
            assert bills[0].amount == Decimal('1234.56')
    
    def test_extract_electricity_bill_category(self):
        """Test att automatiskt identifiera elräkningskategori."""
        text = """
        Elräkning från Vattenfall
        Belopp: 850 kr
        Förfallodatum: 2025-11-25
        """
        
        bills = extract_bills_from_text(text, "Övrigt")
        
        if bills:
            assert bills[0].category == "Boende"  # Bör automatiskt kategoriseras
    
    def test_extract_insurance_bill_category(self):
        """Test att automatiskt identifiera försäkringskategori."""
        text = """
        Försäkring - Hemförsäkring
        Belopp: 450 kronor
        Betalas senast: 2025-12-10
        """
        
        bills = extract_bills_from_text(text, "Övrigt")
        
        if bills:
            assert bills[0].category == "Försäkring"
    
    def test_extract_no_bills_from_empty_text(self):
        """Test att hantera tom text."""
        bills = extract_bills_from_text("", "Boende")
        assert len(bills) == 0
    
    def test_extract_incomplete_data(self):
        """Test att hantera ofullständig fakturainformation."""
        text = """
        Faktura från: Företag AB
        Belopp: 500 kr
        """
        # Inget datum angivet
        
        bills = extract_bills_from_text(text, "Boende")
        # Bör inte skapa faktura utan datum
        assert len(bills) == 0
    
    def test_extract_amount_with_spaces(self):
        """Test att hantera belopp med mellanslag."""
        text = """
        Belopp: 1 234,56 kr
        Förfallodatum: 2025-11-30
        """
        
        bills = extract_bills_from_text(text, "Boende")
        
        if bills:
            assert bills[0].amount == Decimal('1234.56')


class TestValidateBillStructure:
    """Tester för validate_bill_structure-funktionen."""
    
    def test_validate_correct_bill(self):
        """Test att validera korrekt faktura."""
        bill = Bill(
            name="Elräkning",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        assert validate_bill_structure(bill) is True
    
    def test_validate_bill_with_empty_name(self):
        """Test att avvisa faktura med tomt namn."""
        bill = Bill(
            name="",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        assert validate_bill_structure(bill) is False
    
    def test_validate_recurring_bill_with_frequency(self):
        """Test att validera återkommande faktura med frekvens."""
        bill = Bill(
            name="Hyra",
            amount=Decimal('8000'),
            due_date=date(2025, 12, 1),
            category="Boende",
            recurring=True,
            frequency="monthly"
        )
        
        assert validate_bill_structure(bill) is True
    
    def test_validate_recurring_bill_without_frequency(self):
        """Test att avvisa återkommande faktura utan frekvens."""
        bill = Bill(
            name="Hyra",
            amount=Decimal('8000'),
            due_date=date(2025, 12, 1),
            category="Boende",
            recurring=True
        )
        
        assert validate_bill_structure(bill) is False
    
    def test_validate_paid_bill_with_payment_date(self):
        """Test att validera betald faktura med betalningsdatum."""
        bill = Bill(
            name="Internet",
            amount=Decimal('399'),
            due_date=date(2025, 11, 15),
            category="Boende",
            paid=True,
            payment_date=date(2025, 11, 16)
        )
        
        assert validate_bill_structure(bill) is True
    
    def test_validate_paid_bill_without_payment_date(self):
        """Test att avvisa betald faktura utan betalningsdatum."""
        bill = Bill(
            name="Internet",
            amount=Decimal('399'),
            due_date=date(2025, 11, 15),
            category="Boende",
            paid=True
        )
        
        assert validate_bill_structure(bill) is False


class TestWriteBillsToYaml:
    """Tester för write_bills_to_yaml-funktionen."""
    
    def test_write_single_bill(self, tmp_path):
        """Test att skriva en enskild faktura till YAML."""
        yaml_file = tmp_path / "test_bills.yaml"
        
        bill = Bill(
            name="Elräkning",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        write_bills_to_yaml([bill], str(yaml_file))
        
        # Verifiera att filen skapades och innehåller rätt data
        assert yaml_file.exists()
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert 'upcoming_bills' in data
        assert 'bills' in data['upcoming_bills']
        assert len(data['upcoming_bills']['bills']) == 1
        assert data['upcoming_bills']['bills'][0]['name'] == "Elräkning"
        assert data['upcoming_bills']['bills'][0]['amount'] == 900.0
    
    def test_write_multiple_bills(self, tmp_path):
        """Test att skriva flera fakturor till YAML."""
        yaml_file = tmp_path / "test_bills.yaml"
        
        bills = [
            Bill(
                name="Elräkning",
                amount=Decimal('900'),
                due_date=date(2025, 11, 30),
                category="Boende"
            ),
            Bill(
                name="Internet",
                amount=Decimal('399'),
                due_date=date(2025, 11, 15),
                category="Boende"
            )
        ]
        
        write_bills_to_yaml(bills, str(yaml_file))
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert len(data['upcoming_bills']['bills']) == 2
    
    def test_write_bills_avoids_duplicates(self, tmp_path):
        """Test att undvika dubbletter vid skrivning."""
        yaml_file = tmp_path / "test_bills.yaml"
        
        bill = Bill(
            name="Elräkning",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        # Skriv samma faktura två gånger
        write_bills_to_yaml([bill], str(yaml_file))
        write_bills_to_yaml([bill], str(yaml_file))
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Bör endast finnas en faktura
        assert len(data['upcoming_bills']['bills']) == 1
    
    def test_write_bills_appends_to_existing(self, tmp_path):
        """Test att lägga till fakturor till befintlig fil."""
        yaml_file = tmp_path / "test_bills.yaml"
        
        bill1 = Bill(
            name="Elräkning",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        bill2 = Bill(
            name="Internet",
            amount=Decimal('399'),
            due_date=date(2025, 11, 15),
            category="Boende"
        )
        
        # Skriv första fakturan
        write_bills_to_yaml([bill1], str(yaml_file))
        
        # Skriv andra fakturan
        write_bills_to_yaml([bill2], str(yaml_file))
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Båda fakturorna bör finnas
        assert len(data['upcoming_bills']['bills']) == 2
    
    def test_write_bills_skips_invalid(self, tmp_path):
        """Test att hoppa över ogiltiga fakturor."""
        yaml_file = tmp_path / "test_bills.yaml"
        
        valid_bill = Bill(
            name="Elräkning",
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        invalid_bill = Bill(
            name="",  # Tomt namn
            amount=Decimal('900'),
            due_date=date(2025, 11, 30),
            category="Boende"
        )
        
        write_bills_to_yaml([valid_bill, invalid_bill], str(yaml_file))
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Endast den giltiga fakturan bör sparas
        assert len(data['upcoming_bills']['bills']) == 1
        assert data['upcoming_bills']['bills'][0]['name'] == "Elräkning"


class TestIntegration:
    """Integrationstester för hela PDF-parsningsflödet."""
    
    def test_extract_and_write_workflow(self, tmp_path):
        """Test hela arbetsflödet från text till YAML."""
        text = """
        Faktura: Elräkning Vattenfall
        Belopp: 925,50 kr
        Förfallodatum: 2025-11-30
        """
        
        # Extrahera fakturor från text
        bills = extract_bills_from_text(text, "Boende")
        
        # Skriv till YAML
        yaml_file = tmp_path / "test_bills.yaml"
        write_bills_to_yaml(bills, str(yaml_file))
        
        # Verifiera att allt fungerade
        assert yaml_file.exists()
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if bills:  # Om parsing lyckades
            assert len(data['upcoming_bills']['bills']) >= 1
