"""
Tester för klassificerings-API:t.

Dessa tester verifierar att Flask API:t fungerar korrekt för:
- Label (spara träningsexempel)
- Preview (förhandsgranska klassificering)
- Assign (persistera tilldelningar)
- Training trigger (starta träning)
"""

import pytest
import json
import sys
from pathlib import Path

# Lägg till projektets rotkatalog till path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.classification import app, store, classifier


@pytest.fixture
def client():
    """Skapar en Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def setup_test_data():
    """Sätter upp testdata innan varje test."""
    # Spara original metoder
    original_save = store.save_to_yaml
    original_update = classifier._update_model_metadata
    original_load = store.load_from_yaml
    
    # Mock save_to_yaml och _update_model_metadata för att förhindra skrivning till disk
    store.save_to_yaml = lambda: None
    classifier._update_model_metadata = lambda training_count: None
    
    # Mock load_from_yaml men behåll state
    def mock_load():
        # Ladda inte från disk, använd befintlig state
        pass
    store.load_from_yaml = mock_load
    
    # Rensa store
    store.training_examples = []
    store.assigned_categories = {}
    store.preview_sessions = {}
    
    # Rensa classifier state
    classifier.category_counts = {}
    classifier.model = None
    
    yield
    
    # Återställ original metoder
    store.save_to_yaml = original_save
    classifier._update_model_metadata = original_update
    store.load_from_yaml = original_load
    
    # Cleanup efter test
    store.training_examples = []
    store.assigned_categories = {}


class TestGetAccounts:
    """Tester för GET /api/accounts endpoint."""
    
    def test_get_accounts_success(self, client):
        """Testar att hämta alla konton fungerar."""
        response = client.get('/api/accounts')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'accounts' in data
        assert 'count' in data
        assert isinstance(data['accounts'], list)


class TestGetAccountTransactions:
    """Tester för GET /api/accounts/{accountId}/transactions endpoint."""
    
    def test_get_transactions_with_invalid_account(self, client):
        """Testar hämtning av transaktioner för icke-existerande konto."""
        response = client.get('/api/accounts/nonexistent_account/transactions')
        
        # Förväntar antingen 200 med tom lista eller 500
        assert response.status_code in [200, 500]
        
    def test_get_transactions_with_pagination(self, client):
        """Testar paginering av transaktioner."""
        response = client.get('/api/accounts/test_account/transactions?limit=10&offset=0')
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'limit' in data
            assert 'offset' in data
            assert data['limit'] == 10
            assert data['offset'] == 0


class TestLabelTransaction:
    """Tester för POST /api/transactions/{transactionId}/label endpoint."""
    
    def test_label_transaction_success(self, client, setup_test_data):
        """Testar att spara ett träningsexempel fungerar."""
        payload = {
            'description': 'ICA Maxi Linköping',
            'category': 'mat'
        }
        
        response = client.post(
            '/api/transactions/test_transaction_123/label',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'training_example' in data
        assert data['training_example']['description'] == 'ICA Maxi Linköping'
        assert data['training_example']['category'] == 'mat'
        assert 'total_examples' in data
        assert 'can_train' in data
        
    def test_label_transaction_missing_fields(self, client, setup_test_data):
        """Testar att request utan required fields returnerar 400."""
        payload = {
            'description': 'ICA Maxi Linköping'
            # Saknar 'category'
        }
        
        response = client.post(
            '/api/transactions/test_transaction_123/label',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        
    def test_label_transaction_multiple_examples(self, client, setup_test_data):
        """Testar att lägga till flera träningsexempel."""
        examples = [
            {'description': 'ICA Maxi', 'category': 'mat'},
            {'description': 'Coop Supermarket', 'category': 'mat'},
            {'description': 'Circle K', 'category': 'transport'}
        ]
        
        for idx, example in enumerate(examples):
            response = client.post(
                f'/api/transactions/test_trans_{idx}/label',
                data=json.dumps(example),
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['total_examples'] == idx + 1


class TestAssignCategory:
    """Tester för POST /api/transactions/{transactionId}/assign endpoint."""
    
    def test_assign_category_success(self, client, setup_test_data):
        """Testar att tilldela kategori fungerar."""
        payload = {
            'category': 'mat'
        }
        
        response = client.post(
            '/api/transactions/test_transaction_456/assign',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['category'] == 'mat'
        assert data['transaction_id'] == 'test_transaction_456'
        
    def test_assign_category_missing_category(self, client, setup_test_data):
        """Testar att request utan kategori returnerar 400."""
        payload = {}
        
        response = client.post(
            '/api/transactions/test_transaction_456/assign',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestPreviewClassification:
    """Tester för POST /api/preview endpoint."""
    
    def test_preview_classification_success(self, client, setup_test_data):
        """Testar förhandsgranskning av klassificering."""
        payload = {
            'transactions': [
                {'description': 'ICA Maxi Linköping'},
                {'description': 'Circle K bensinstation'}
            ]
        }
        
        response = client.post(
            '/api/preview',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'results' in data
        assert 'session_id' in data
        assert len(data['results']) == 2
        
        # Verifiera att varje resultat har rätt struktur
        for result in data['results']:
            assert 'description' in result
            assert 'predicted_category' in result
            assert 'confidence' in result
            assert 'needs_review' in result
            
    def test_preview_classification_missing_transactions(self, client, setup_test_data):
        """Testar preview utan transaktioner returnerar 400."""
        payload = {}
        
        response = client.post(
            '/api/preview',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        
    def test_preview_classification_empty_list(self, client, setup_test_data):
        """Testar preview med tom lista."""
        payload = {
            'transactions': []
        }
        
        response = client.post(
            '/api/preview',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['results']) == 0


class TestTriggerTraining:
    """Tester för POST /api/train endpoint."""
    
    def test_trigger_training_insufficient_data(self, client, setup_test_data):
        """Testar träning utan tillräckligt med data returnerar 400."""
        response = client.post('/api/train?async=false')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Otillräckligt med träningsdata' in data['error']
        
    def test_trigger_training_with_sufficient_data(self, client, setup_test_data):
        """Testar träning med tillräckligt med data."""
        # Lägg till träningsexempel först
        examples = [
            {'description': 'ICA Maxi Linköping', 'category': 'mat'},
            {'description': 'Coop Supermarket', 'category': 'mat'},
            {'description': 'Circle K bensin', 'category': 'transport'},
            {'description': 'Shell diesel', 'category': 'transport'}
        ]
        
        for idx, example in enumerate(examples):
            client.post(
                f'/api/transactions/test_trans_{idx}/label',
                data=json.dumps(example),
                content_type='application/json'
            )
            
        # Trigga träning
        response = client.post('/api/train?async=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data


class TestModelStatus:
    """Tester för GET /api/model/status endpoint."""
    
    def test_get_model_status_success(self, client):
        """Testar att hämta modellstatus fungerar."""
        response = client.get('/api/model/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'status' in data
        
        # Verifiera status-struktur
        status = data['status']
        assert 'model_trained' in status
        assert 'training_in_progress' in status
        assert 'can_train' in status
        assert 'category_counts' in status
        assert 'total_examples' in status
        assert 'min_examples_required' in status


class TestErrorHandling:
    """Tester för felhantering."""
    
    def test_404_error(self, client):
        """Testar att icke-existerande endpoint returnerar 404."""
        response = client.get('/api/nonexistent_endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


class TestIntegrationFlow:
    """Integration-tester som testar hela flödet."""
    
    def test_full_classification_workflow(self, client, setup_test_data):
        """
        Testar hela arbetsflödet:
        1. Lägg till träningsexempel (label)
        2. Förhandsgranska klassificering (preview)
        3. Tilldela kategori (assign)
        4. Kontrollera status
        """
        # 1. Lägg till träningsexempel
        examples = [
            {'description': 'ICA Maxi', 'category': 'mat'},
            {'description': 'Coop Extra', 'category': 'mat'},
            {'description': 'Circle K', 'category': 'transport'},
            {'description': 'Shell', 'category': 'transport'}
        ]
        
        for idx, example in enumerate(examples):
            response = client.post(
                f'/api/transactions/train_{idx}/label',
                data=json.dumps(example),
                content_type='application/json'
            )
            assert response.status_code == 201
            
        # 2. Förhandsgranska klassificering
        preview_payload = {
            'transactions': [
                {'description': 'ICA Supermarket Stockholm'},
                {'description': 'Circle K bensinstation Uppsala'}
            ]
        }
        
        response = client.post(
            '/api/preview',
            data=json.dumps(preview_payload),
            content_type='application/json'
        )
        assert response.status_code == 200
        preview_data = json.loads(response.data)
        assert len(preview_data['results']) == 2
        
        # 3. Tilldela kategori baserat på preview
        for result in preview_data['results']:
            assign_payload = {
                'category': result['predicted_category']
            }
            response = client.post(
                '/api/transactions/assign_test_123/assign',
                data=json.dumps(assign_payload),
                content_type='application/json'
            )
            assert response.status_code == 200
            
        # 4. Kontrollera modellstatus
        response = client.get('/api/model/status')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert status_data['status']['total_examples'] >= 4
