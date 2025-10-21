"""
Hybrid classifier service för transaktionskategorisering.

Detta modul implementerar en hybrid-klassificerare som kombinerar:
1. Regelbaserad matchning (snabb, hög precision)
2. TF-IDF maskinlärning (fallback för okända transaktioner)

Klassificeraren håller koll på antalet träningsexempel per kategori
och kan tränas asynkront när tillräckligt med data finns tillgängligt.
"""

import yaml
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import threading
import pickle


class HybridClassifier:
    """
    Hybrid-klassificerare som kombinerar regelbaserad och ML-baserad kategorisering.
    
    Attribut:
        rules: Dict med kategoriregler från YAML
        model: Tränad TF-IDF + Naive Bayes modell (eller None)
        training_in_progress: Flag som indikerar pågående träning
        category_counts: Dict med antal exempel per kategori
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialisera klassificeraren.
        
        Args:
            schema_path: Sökväg till category_schema.yaml (None = default)
        """
        if schema_path is None:
            # Default till projektets category_schema.yaml
            schema_path = Path(__file__).parent.parent.parent / "category_schema.yaml"
        else:
            schema_path = Path(schema_path)
            
        self.schema_path = schema_path
        self.rules = {}
        self.model = None
        self.vectorizer = None
        self.training_in_progress = False
        self.category_counts = {}
        self.min_examples_per_category = 2
        
        # Ladda schema och regler
        self._load_schema()
        
    def _load_schema(self) -> None:
        """Laddar kategori-schema från YAML-fil."""
        if not self.schema_path.exists():
            # Skapa tom schema om den inte finns
            self._create_default_schema()
            
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            
        # Ladda kategorier och keywords
        self.rules = schema.get('categories', {})
        
        # Ladda inställningar
        settings = schema.get('persisted_settings', {})
        training_settings = settings.get('training', {})
        self.min_examples_per_category = training_settings.get('min_examples_per_category', 2)
        
        # Räkna träningsexempel per kategori
        training_examples = schema.get('training_examples', [])
        self._update_category_counts(training_examples)
        
    def _create_default_schema(self) -> None:
        """Skapar en default category_schema.yaml om den inte finns."""
        default_schema = {
            'categories': {},
            'model_metadata': {
                'model_type': 'hybrid',
                'last_trained': None,
                'training_count': 0
            },
            'training_examples': [],
            'persisted_settings': {
                'training': {
                    'min_examples_per_category': 2
                }
            }
        }
        
        self.schema_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schema_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_schema, f, allow_unicode=True, default_flow_style=False)
            
    def _update_category_counts(self, training_examples: List[Dict]) -> None:
        """
        Uppdaterar räknare för antal exempel per kategori.
        
        Args:
            training_examples: Lista med träningsexempel
        """
        self.category_counts = {}
        
        # Handle None case
        if training_examples is None:
            return
            
        for example in training_examples:
            category = example.get('category', '')
            self.category_counts[category] = self.category_counts.get(category, 0) + 1
            
    def rule_match(self, description: str) -> Optional[Tuple[str, float]]:
        """
        Matchar transaktion mot regelbaserade keywords.
        
        Args:
            description: Transaktionsbeskrivning
            
        Returns:
            Tuple (kategori, confidence) eller None om ingen match
        """
        description_lower = description.lower()
        
        for category, config in self.rules.items():
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    # Hög confidence vid regelbaserad match
                    return (category, 0.95)
                    
        return None
        
    def predict(self, description: str, use_rules: bool = True, 
                use_model: bool = True) -> Tuple[str, float]:
        """
        Förutsäger kategori för en transaktionsbeskrivning.
        
        Args:
            description: Transaktionsbeskrivning
            use_rules: Använd regelbaserad matchning först
            use_model: Använd ML-modell som fallback
            
        Returns:
            Tuple (kategori, confidence)
        """
        # Försök regelbaserad matchning först
        if use_rules:
            rule_result = self.rule_match(description)
            if rule_result:
                return rule_result
                
        # Fallback till ML-modell om tillgänglig
        if use_model and self.model is not None:
            try:
                # Förutsäg med TF-IDF modell
                probabilities = self.model.predict_proba([description])[0]
                max_prob_idx = np.argmax(probabilities)
                confidence = probabilities[max_prob_idx]
                
                # Hämta kategori från modellens classes
                category = self.model.classes_[max_prob_idx]
                
                return (category, float(confidence))
            except Exception as e:
                print(f"Fel vid ML-prediktion: {e}")
                
        # Ingen match - returnera "övrigt" med låg confidence
        return ("övrigt", 0.1)
        
    def get_category_stats(self) -> Dict[str, int]:
        """
        Returnerar statistik över träningsexempel per kategori.
        
        Returns:
            Dict med kategori -> antal exempel
        """
        return self.category_counts.copy()
        
    def can_train(self) -> bool:
        """
        Kontrollerar om modellen kan tränas (tillräckligt med data).
        
        Returns:
            True om tillräckligt med träningsdata finns
        """
        # Kräv minst 2 kategorier och minst min_examples_per_category per kategori
        if len(self.category_counts) < 2:
            return False
            
        # Kontrollera att varje kategori har tillräckligt med exempel
        for count in self.category_counts.values():
            if count < self.min_examples_per_category:
                return False
                
        return True
        
    def train(self, training_examples: List[Dict], async_mode: bool = False) -> bool:
        """
        Tränar ML-modellen på träningsexempel.
        
        Args:
            training_examples: Lista med träningsexempel (dict med 'description' och 'category')
            async_mode: Kör träning asynkront i separat tråd
            
        Returns:
            True om träning startades/slutfördes, False annars
        """
        if async_mode:
            # Starta träning i bakgrundstråd
            thread = threading.Thread(target=self._train_model, args=(training_examples,))
            thread.daemon = True
            thread.start()
            return True
        else:
            # Synkron träning
            return self._train_model(training_examples)
            
    def _train_model(self, training_examples: List[Dict]) -> bool:
        """
        Intern metod för att träna modellen.
        
        Args:
            training_examples: Lista med träningsexempel
            
        Returns:
            True om träning lyckades
        """
        if self.training_in_progress:
            print("Träning pågår redan")
            return False
            
        try:
            self.training_in_progress = True
            
            # Uppdatera category counts
            self._update_category_counts(training_examples)
            
            # Kontrollera om vi har tillräckligt med data
            if not self.can_train():
                print(f"Otillräckligt med träningsdata. Behöver minst {self.min_examples_per_category} exempel per kategori och minst 2 kategorier.")
                return False
                
            # Extrahera features och labels
            descriptions = [ex['description'] for ex in training_examples]
            categories = [ex['category'] for ex in training_examples]
            
            # Skapa och träna pipeline (TF-IDF + Naive Bayes)
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
                ('clf', MultinomialNB())
            ])
            
            self.model.fit(descriptions, categories)
            
            # Uppdatera metadata i schema
            self._update_model_metadata(len(training_examples))
            
            print(f"Modell tränad med {len(training_examples)} exempel över {len(set(categories))} kategorier")
            return True
            
        except Exception as e:
            print(f"Fel vid träning: {e}")
            return False
            
        finally:
            self.training_in_progress = False
            
    def _update_model_metadata(self, training_count: int) -> None:
        """
        Uppdaterar modellmetadata i schema-filen.
        
        Args:
            training_count: Antal träningsexempel
        """
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
                
            if 'model_metadata' not in schema:
                schema['model_metadata'] = {}
                
            schema['model_metadata']['last_trained'] = datetime.now().isoformat()
            schema['model_metadata']['training_count'] = training_count
            schema['model_metadata']['categories_count'] = len(self.category_counts)
            
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, allow_unicode=True, default_flow_style=False)
                
        except Exception as e:
            print(f"Kunde inte uppdatera model_metadata: {e}")
            
    def get_training_status(self) -> Dict:
        """
        Returnerar status för träning och modell.
        
        Returns:
            Dict med träningsstatus och metadata
        """
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            
        model_metadata = schema.get('model_metadata', {})
        
        return {
            'model_trained': self.model is not None,
            'training_in_progress': self.training_in_progress,
            'can_train': self.can_train(),
            'category_counts': self.category_counts,
            'total_examples': sum(self.category_counts.values()),
            'min_examples_required': self.min_examples_per_category,
            'last_trained': model_metadata.get('last_trained'),
            'model_version': model_metadata.get('model_version', '1.0.0')
        }
