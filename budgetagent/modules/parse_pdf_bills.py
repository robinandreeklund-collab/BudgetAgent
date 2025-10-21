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


def extract_text_from_pdf(file_path: str) -> str:
    """
    Läser text från PDF-sidor och returnerar som sträng.
    
    Använder pdfplumber för att extrahera all text från en PDF-fil.
    
    Args:
        file_path: Sökväg till PDF-filen
        
    Returns:
        Extraherad text som en sammanhängande sträng
    """
    pass


def extract_bills_from_text(raw_text: str) -> List[Dict]:
    """
    Identifierar fakturor i texten via regex eller heuristik.
    
    Analyserar extraherad text och letar efter mönster som indikerar
    fakturainformation (belopp, datum, betalningsmottagare).
    
    Args:
        raw_text: Rå text från PDF
        
    Returns:
        Lista med dictionary-objekt innehållande:
        - name (str): Fakturans namn/beskrivning
        - amount (float): Belopp i kronor
        - due_date (str): Förfallodatum i format YYYY-MM-DD
        - category (str, optional): Kategori för fakturen
    """
    pass


def validate_bill_structure(bill: Dict) -> bool:
    """
    Säkerställer att varje faktura har korrekt format och fält.
    
    Validerar att en faktura innehåller alla nödvändiga fält och
    att de har korrekta datatyper och värden.
    
    Args:
        bill: Dictionary med fakturadata
        
    Returns:
        True om strukturen är korrekt, annars False
    """
    pass


def write_bills_to_yaml(bills: List[Dict], yaml_path: str) -> None:
    """
    Lägger till extraherade fakturor i upcoming_bills.yaml.
    
    Läser befintlig YAML-fil, lägger till nya fakturor och sparar.
    Undviker dubbletter genom att jämföra namn och förfallodatum.
    
    Args:
        bills: Lista med validerade fakturor
        yaml_path: Sökväg till upcoming_bills.yaml
    """
    pass


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
    """
    pass
