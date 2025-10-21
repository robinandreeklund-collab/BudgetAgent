"""
Modul för extrahering av fakturainformation från PDF-filer och konvertering till YAML-format.

Denna modul hanterar automatisk extraktion av fakturadata från PDF-filer.
Den stödjer både textbaserade PDF:er och bildbaserade fakturor via OCR.
Extraherad information sparas direkt i upcoming_bills.yaml för vidare användning.

Beroenden:
- pdfplumber för PDF-textextraktion
- pytesseract (valfritt) för OCR
- pdf2image (valfri) för bildbaserade fakturor

Exempel på YAML-konfiguration (parse_pdf_bills.yaml):
    parse_pdf_bills:
      ocr_enabled: false
      default_category: "Boende"
      date_format: "YYYY-MM-DD"
      
Output skrivs till upcoming_bills.yaml:
    upcoming_bills:
      bills:
        - name: "Elräkning"
          amount: 900
          due_date: "2025-11-30"
          category: "Boende"
"""

from typing import List, Dict, Optional
from pathlib import Path
import re
from datetime import datetime
from decimal import Decimal
import yaml
import pdfplumber
from .models import Bill


def extract_text_from_pdf(file_path: str) -> str:
    """
    Läser text från PDF-sidor och returnerar som sträng.
    
    Använder pdfplumber för att extrahera all text från en PDF-fil.
    
    Args:
        file_path: Sökväg till PDF-filen
        
    Returns:
        Extraherad text som en sammanhängande sträng
        
    Raises:
        FileNotFoundError: Om PDF-filen inte finns
        Exception: Om PDF-filen inte kan läsas
    """
    pdf_file = Path(file_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF-fil hittades inte: {file_path}")
    
    try:
        text_parts = []
        with pdfplumber.open(str(pdf_file)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n'.join(text_parts)
    except Exception as e:
        raise Exception(f"Kunde inte läsa PDF-fil: {e}")


def extract_bills_from_text(raw_text: str, default_category: str = "Boende") -> List[Bill]:
    """
    Identifierar fakturor i texten via regex eller heuristik.
    
    Analyserar extraherad text och letar efter mönster som indikerar
    fakturainformation (belopp, datum, betalningsmottagare).
    
    Args:
        raw_text: Rå text från PDF
        default_category: Standardkategori om ingen kan identifieras
        
    Returns:
        Lista med Bill-objekt
    """
    bills = []
    
    # Mönster för att identifiera belopp (SEK, kr, kronor)
    # Matchar: 1 234,56, 1234.56, 1234,56 kr, etc.
    amount_patterns = [
        r'(?:SEK|kr|kronor)?\s*(\d{2,}[\d\s]*[,\.]?\d{0,2})\s*(?:SEK|kr|kronor)?',
        r'Belopp:?\s*(\d{2,}[\d\s]*[,\.]?\d{0,2})',
        r'Att betala:?\s*(\d{2,}[\d\s]*[,\.]?\d{0,2})',
        r'Totalt:?\s*(\d{2,}[\d\s]*[,\.]?\d{0,2})',
        r'Summa:?\s*(\d{2,}[\d\s]*[,\.]?\d{0,2})'
    ]
    
    # Mönster för datum (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, etc.)
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}[-/]\d{2}[-/]\d{4})',
        r'(\d{2}\.\d{2}\.\d{4})',
        r'Förfallodatum:?\s*(\d{4}-\d{2}-\d{2})',
        r'Förfallodatum:?\s*(\d{2}[-/]\d{2}[-/]\d{4})',
        r'Sista betalningsdag:?\s*(\d{4}-\d{2}-\d{2})',
        r'Sista betalningsdag:?\s*(\d{2}[-/]\d{2}[-/]\d{4})',
        r'Betalas senast:?\s*(\d{4}-\d{2}-\d{2})',
        r'Betalas senast:?\s*(\d{2}[-/]\d{2}[-/]\d{4})'
    ]
    
    # Mönster för fakturans namn/typ
    name_patterns = [
        r'Faktura(?:\s+för)?:?\s*([^\n]+)',
        r'Leverantör:?\s*([^\n]+)',
        r'Från:?\s*([^\n]+)',
        r'([A-ZÅÄÖ][a-zåäö]+\s+(?:AB|HB|KB))',  # Företagsnamn
    ]
    
    # Försök extrahera belopp
    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(' ', '').replace(',', '.')
            try:
                amount = Decimal(amount_str)
                if amount > 0:
                    break
            except:
                continue
    
    # Försök extrahera datum
    due_date = None
    for pattern in date_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Försök olika datumformat
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y']:
                try:
                    due_date = datetime.strptime(date_str, fmt).date()
                    break
                except:
                    continue
            if due_date:
                break
    
    # Försök extrahera namn
    bill_name = None
    for pattern in name_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            bill_name = match.group(1).strip()
            if bill_name and len(bill_name) > 2:
                break
    
    # Om vi har minst belopp och datum, skapa en faktura
    if amount and due_date:
        if not bill_name:
            bill_name = "Faktura från PDF"
        
        # Gissa kategori baserat på nyckelord (prioritetsordning)
        category = default_category
        text_lower = raw_text.lower()
        
        # Försäkring har högst prioritet
        if any(word in text_lower for word in ['försäkring', 'insurance', 'hemförsäkring', 'bilförsäkring']):
            category = "Försäkring"
        # Sedan boenderelaterade kostnader
        elif any(word in text_lower for word in ['el', 'elräkning', 'elavgift', 'energi']):
            category = "Boende"
        elif any(word in text_lower for word in ['vatten', 'va-avgift']):
            category = "Boende"
        elif any(word in text_lower for word in ['hyra', 'hyreskostnad']):
            category = "Boende"
        elif any(word in text_lower for word in ['telefon', 'tele2', 'telia', 'telenor', 'mobilabonnemang']):
            category = "Boende"
        elif any(word in text_lower for word in ['internet', 'bredband', 'wifi']):
            category = "Boende"
        
        try:
            bill = Bill(
                name=bill_name,
                amount=amount,
                due_date=due_date,
                category=category
            )
            bills.append(bill)
        except Exception as e:
            print(f"Kunde inte skapa faktura: {e}")
    
    return bills


def validate_bill_structure(bill: Bill) -> bool:
    """
    Säkerställer att varje faktura har korrekt format och fält.
    
    Validerar att en faktura innehåller alla nödvändiga fält och
    att de har korrekta datatyper och värden. Pydantic validerar
    automatiskt, men denna funktion kan lägga till extra affärslogik.
    
    Args:
        bill: Bill-objekt att validera
        
    Returns:
        True om strukturen är korrekt, annars False
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


def write_bills_to_yaml(bills: List[Bill], yaml_path: str) -> None:
    """
    Lägger till extraherade fakturor i upcoming_bills.yaml.
    
    Läser befintlig YAML-fil, lägger till nya fakturor och sparar.
    Undviker dubbletter genom att jämföra namn och förfallodatum.
    
    Args:
        bills: Lista med validerade Bill-objekt
        yaml_path: Sökväg till upcoming_bills.yaml
        
    Raises:
        Exception: Om YAML-filen inte kan läsas eller skrivas
    """
    yaml_file = Path(yaml_path)
    
    try:
        # Ladda befintliga fakturor
        if yaml_file.exists():
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        
        if 'upcoming_bills' not in data:
            data['upcoming_bills'] = {'bills': []}
        elif 'bills' not in data['upcoming_bills']:
            data['upcoming_bills']['bills'] = []
        
        # Lägg till nya fakturor
        added_count = 0
        for bill in bills:
            if not validate_bill_structure(bill):
                print(f"Faktura {bill.name} validerades inte korrekt, hoppar över")
                continue
            
            # Konvertera Bill till dictionary
            bill_dict = {
                'name': bill.name,
                'amount': float(bill.amount),
                'due_date': bill.due_date.isoformat(),
                'category': bill.category,
                'account': bill.account,
                'recurring': bill.recurring,
                'frequency': bill.frequency,
                'paid': bill.paid
            }
            
            if bill.payment_date:
                bill_dict['payment_date'] = bill.payment_date.isoformat()
            
            # Kontrollera för dubbletter
            duplicate = any(
                b.get('name') == bill_dict['name'] and
                float(b.get('amount', 0)) == bill_dict['amount'] and
                b.get('due_date') == bill_dict['due_date']
                for b in data['upcoming_bills']['bills']
            )
            
            if not duplicate:
                data['upcoming_bills']['bills'].append(bill_dict)
                added_count += 1
        
        # Spara tillbaka
        yaml_file.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✅ Lade till {added_count} nya fakturor i {yaml_path}")
        
    except Exception as e:
        raise Exception(f"Kunde inte skriva fakturor till YAML: {e}")


def extract_text_with_ocr(file_path: str) -> str:
    """
    Använder OCR för att tolka bildbaserade fakturor (valfri funktion).
    
    Konverterar PDF till bilder och använder Tesseract OCR för att
    extrahera text från bildbaserade fakturor.
    
    Kräver:
    - pytesseract
    - pdf2image
    
    Args:
        file_path: Sökväg till PDF-filen
        
    Returns:
        OCR-tolkad text som sträng
        
    Raises:
        ImportError: Om pytesseract eller pdf2image inte är installerade
        Exception: Om OCR misslyckas
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "OCR-funktionalitet kräver pytesseract och pdf2image. "
            "Installera med: pip install pytesseract pdf2image"
        )
    
    pdf_file = Path(file_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF-fil hittades inte: {file_path}")
    
    try:
        # Konvertera PDF till bilder
        images = convert_from_path(str(pdf_file))
        
        # Använd OCR på varje sida
        text_parts = []
        for i, image in enumerate(images):
            try:
                text = pytesseract.image_to_string(image, lang='swe')
                if text:
                    text_parts.append(text)
            except Exception as e:
                print(f"Kunde inte läsa sida {i + 1} med OCR: {e}")
                continue
        
        return '\n'.join(text_parts)
        
    except Exception as e:
        raise Exception(f"OCR misslyckades: {e}")


def parse_pdf_to_bills(
    file_path: str, 
    default_category: str = "Boende", 
    ocr_enabled: bool = False
) -> List[Bill]:
    """
    Huvudfunktion för att parsa PDF och extrahera fakturor.
    
    Försöker först med textextraktion, och om OCR är aktiverat
    och textextraktion misslyckas, använder OCR istället.
    
    Args:
        file_path: Sökväg till PDF-filen
        default_category: Standardkategori för fakturor
        ocr_enabled: Om OCR ska användas för bildbaserade PDFs
        
    Returns:
        Lista med extraherade Bill-objekt
    """
    # Försök med textextraktion först
    try:
        text = extract_text_from_pdf(file_path)
        
        # Om ingen text extraherades och OCR är aktiverat, försök med OCR
        if (not text or len(text.strip()) < 10) and ocr_enabled:
            print("Lite eller ingen text hittades, försöker med OCR...")
            text = extract_text_with_ocr(file_path)
        
        # Extrahera fakturor från texten
        bills = extract_bills_from_text(text, default_category)
        
        return bills
        
    except Exception as e:
        print(f"Fel vid parsning av PDF: {e}")
        return []
