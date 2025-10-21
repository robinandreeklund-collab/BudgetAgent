"""
Flask-baserat API för transaktionskategorisering och träning.

Detta API-skelett tillhandahåller endpoints för:
- Hämta konton och transaktioner
- Spara träningsexempel (label)
- Persistera tilldelningar (assign)
- Förhandsgranska klassificering (preview)
- Triggera asynkron träning
- Hämta modellstatus

Använder en enkel in-memory store som placeholder för demonstration.
I produktion skulle detta kunna ersättas med databas eller YAML-persistence.
"""

from flask import Flask, request, jsonify
from typing import Dict, List, Optional
import yaml
from pathlib import Path
from datetime import datetime
import uuid
import sys

# Lägg till projektets rotkatalog till path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.service.classifier import HybridClassifier
from budgetagent.modules.account_manager import (
    load_accounts
)


# Helper function to get transactions from account
def get_account_transactions(account_id: str) -> List[Dict]:
    """
    Hämtar transaktioner för ett konto.
    
    Args:
        account_id: Konto-ID
        
    Returns:
        Lista med transaktioner
    """
    # Placeholder - i produktion skulle detta hämta från databas eller YAML
    # För nu returnerar vi tom lista eller mock data
    accounts = load_accounts()
    
    # Hitta konto
    account = None
    for acc in accounts:
        if acc.get('account_id') == account_id or acc.get('account_name') == account_id:
            account = acc
            break
            
    if not account:
        return []
        
    # I framtiden skulle vi ladda transaktioner från en persistent lagring
    # För nu returnerar vi tom lista
    return []


# Skapa Flask app
app = Flask(__name__)


# In-memory store för demonstration (ersätts med databas i produktion)
class InMemoryStore:
    """Enkel in-memory lagring för demonstration."""
    
    def __init__(self):
        self.accounts = {}
        self.transactions = {}
        self.assigned_categories = {}  # transaction_id -> category
        self.training_examples = []
        self.preview_sessions = {}
        
    def load_from_yaml(self):
        """Laddar data från YAML-filer."""
        # Ladda konton från account_manager
        try:
            accounts_dict = load_accounts()
            # Konvertera dict till lista för enklare hantering
            self.accounts = {}
            for account_name, account_data in accounts_dict.items():
                if isinstance(account_data, dict):
                    self.accounts[account_data.get('account_id', account_name)] = account_data
        except Exception as e:
            print(f"Kunde inte ladda konton: {e}")
            
        # Ladda träningsexempel från category_schema.yaml
        try:
            schema_path = Path(__file__).parent.parent.parent / "category_schema.yaml"
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                    self.training_examples = schema.get('training_examples', [])
        except Exception as e:
            print(f"Kunde inte ladda träningsexempel: {e}")
            
    def save_to_yaml(self):
        """Sparar data till YAML-filer."""
        try:
            schema_path = Path(__file__).parent.parent.parent / "category_schema.yaml"
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
                
            schema['training_examples'] = self.training_examples
            
            with open(schema_path, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"Kunde inte spara till YAML: {e}")


# Initialisera store och classifier
store = InMemoryStore()
store.load_from_yaml()

classifier = HybridClassifier()


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """
    GET /api/accounts
    
    Hämtar alla registrerade bankkonton.
    
    Returns:
        JSON lista med konton
    """
    try:
        accounts_dict = load_accounts()
        
        # Konvertera dict till lista för API-svar
        accounts_list = []
        for account_name, account_data in accounts_dict.items():
            # Konvertera Account-objekt eller dict till serialiserbart format
            if isinstance(account_data, dict):
                account_info = {
                    'account_name': account_name,
                    'account_id': account_data.get('account_id', account_name),
                    **account_data
                }
            else:
                # Om det är ett Account-objekt
                account_info = {
                    'account_name': account_name,
                    'account_id': getattr(account_data, 'account_id', account_name)
                }
                
            # Ta bort set och datetime objekt för JSON-serialisering
            if 'transaction_hashes' in account_info:
                account_info.pop('transaction_hashes')
            if 'last_import_date' in account_info and account_info['last_import_date']:
                account_info['last_import_date'] = str(account_info['last_import_date'])
            if 'balance_date' in account_info and account_info['balance_date']:
                account_info['balance_date'] = str(account_info['balance_date'])
            if 'current_balance' in account_info and account_info['current_balance']:
                account_info['current_balance'] = str(account_info['current_balance'])
                
            accounts_list.append(account_info)
        
        return jsonify({
            'success': True,
            'accounts': accounts_list,
            'count': len(accounts_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/accounts/<account_id>/transactions', methods=['GET'])
def get_account_transactions_endpoint(account_id):
    """
    GET /api/accounts/{accountId}/transactions
    
    Hämtar alla transaktioner för ett specifikt konto.
    
    Args:
        account_id: Konto-ID
        
    Query parameters:
        limit: Max antal transaktioner (default: 100)
        offset: Offset för paginering (default: 0)
        
    Returns:
        JSON med transaktioner
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Hämta transaktioner från account_manager
        transactions = get_account_transactions(account_id)
        
        # Lägg till assigned categories från store
        for trans in transactions:
            trans_id = trans.get('transaction_hash', '')
            if trans_id in store.assigned_categories:
                trans['assigned_category'] = store.assigned_categories[trans_id]
                
        # Paginering
        paginated = transactions[offset:offset+limit]
        
        return jsonify({
            'success': True,
            'account_id': account_id,
            'transactions': paginated,
            'total': len(transactions),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transactions/<transaction_id>/label', methods=['POST'])
def label_transaction(transaction_id):
    """
    POST /api/transactions/{transactionId}/label
    
    Sparar ett träningsexempel för AI-modellen.
    Detta markerar en transaktion med rätt kategori för framtida träning.
    
    Request body:
        {
            "description": "ICA Maxi Linköping",
            "category": "mat"
        }
        
    Args:
        transaction_id: Transaktions-ID (hash)
        
    Returns:
        JSON med status
    """
    try:
        data = request.get_json()
        
        if not data or 'description' not in data or 'category' not in data:
            return jsonify({
                'success': False,
                'error': 'Saknar required fields: description, category'
            }), 400
            
        # Skapa träningsexempel
        training_example = {
            'description': data['description'],
            'category': data['category'],
            'date_added': datetime.now().isoformat(),
            'confidence': 1.0,
            'source': 'manual',
            'transaction_id': transaction_id
        }
        
        # Lägg till i store
        store.training_examples.append(training_example)
        store.save_to_yaml()
        
        # Kontrollera om vi kan träna automatiskt
        classifier._update_category_counts(store.training_examples)
        can_auto_train = classifier.can_train()
        
        return jsonify({
            'success': True,
            'message': 'Träningsexempel sparat',
            'training_example': training_example,
            'total_examples': len(store.training_examples),
            'can_train': can_auto_train
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transactions/<transaction_id>/assign', methods=['POST'])
def assign_category(transaction_id):
    """
    POST /api/transactions/{transactionId}/assign
    
    Persisterar en kategorilldelning för en transaktion.
    Detta sparar den tilldelade kategorin permanent (inte bara för träning).
    
    Request body:
        {
            "category": "mat"
        }
        
    Args:
        transaction_id: Transaktions-ID (hash)
        
    Returns:
        JSON med status
    """
    try:
        data = request.get_json()
        
        if not data or 'category' not in data:
            return jsonify({
                'success': False,
                'error': 'Saknar required field: category'
            }), 400
            
        # Spara persistent tilldelning
        store.assigned_categories[transaction_id] = {
            'category': data['category'],
            'assigned_at': datetime.now().isoformat(),
            'source': data.get('source', 'manual')
        }
        
        return jsonify({
            'success': True,
            'message': 'Kategori tilldelad',
            'transaction_id': transaction_id,
            'category': data['category']
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/preview', methods=['POST'])
def preview_classification():
    """
    POST /api/preview
    
    Förhandsgranskar klassificering för en eller flera transaktioner.
    Använder hybrid-klassificering (rules -> model fallback).
    
    Request body:
        {
            "transactions": [
                {"description": "ICA Maxi Linköping"},
                {"description": "Circle K bensinstation"}
            ]
        }
        
    Returns:
        JSON med förhandsgranskade kategorier och confidence scores
    """
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({
                'success': False,
                'error': 'Saknar required field: transactions'
            }), 400
            
        transactions = data['transactions']
        results = []
        
        for trans in transactions:
            description = trans.get('description', '')
            if not description:
                continue
                
            # Klassificera med hybrid-modell
            category, confidence = classifier.predict(description)
            
            results.append({
                'description': description,
                'predicted_category': category,
                'confidence': confidence,
                'needs_review': confidence < 0.7
            })
            
        # Skapa preview-session
        session_id = f"preview_{uuid.uuid4().hex[:8]}"
        store.preview_sessions[session_id] = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'results': results
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/train', methods=['POST'])
def trigger_training():
    """
    POST /api/train
    
    Triggar asynkron träning av AI-modellen.
    Tränar modellen på alla sparade träningsexempel.
    
    Query parameters:
        async: true/false (default: true)
        
    Returns:
        JSON med träningsstatus
    """
    try:
        async_mode = request.args.get('async', 'true').lower() == 'true'
        
        # Ladda om training examples från YAML
        store.load_from_yaml()
        
        # Kontrollera om vi har tillräckligt med data
        classifier._update_category_counts(store.training_examples)
        if not classifier.can_train():
            return jsonify({
                'success': False,
                'error': 'Otillräckligt med träningsdata',
                'details': {
                    'total_examples': len(store.training_examples),
                    'category_counts': classifier.category_counts,
                    'min_required': classifier.min_examples_per_category
                }
            }), 400
            
        # Starta träning
        training_started = classifier.train(store.training_examples, async_mode=async_mode)
        
        if training_started:
            return jsonify({
                'success': True,
                'message': 'Träning startad' if async_mode else 'Träning slutförd',
                'async': async_mode,
                'training_examples': len(store.training_examples)
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Kunde inte starta träning'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/model/status', methods=['GET'])
def get_model_status():
    """
    GET /api/model/status
    
    Hämtar status för AI-modellen och träning.
    
    Returns:
        JSON med modellstatus och metadata
    """
    try:
        status = classifier.get_training_status()
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Felhanterare
@app.errorhandler(404)
def not_found(error):
    """Hantera 404-fel."""
    return jsonify({
        'success': False,
        'error': 'Endpoint hittades inte'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Hantera 500-fel."""
    return jsonify({
        'success': False,
        'error': 'Internt serverfel'
    }), 500


# Main entry point för att köra API:t standalone
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
