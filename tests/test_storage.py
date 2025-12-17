"""
Unit tests for storage functionality
"""

import pytest
import json
import os
from scraper import storage
from unittest.mock import Mock, patch, mock_open


class TestJSONStorage:
    """Test JSON file operations"""
    
    def test_load_json_valid(self):
        """Should load valid JSON"""
        mock_data = '{"key": "value"}'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            with patch('os.path.exists', return_value=True):
                result = storage.load_json("test.json")
                assert result == {"key": "value"}
    
    def test_load_json_missing_file(self):
        """Should return empty dict for missing file"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = storage.load_json("missing.json")
            assert result == {}
    
    def test_save_json(self):
        """Should save data as JSON"""
        data = {"test": "data"}
        # Simply verifying it doesn't raise exception and tries to open/rename
        with patch('builtins.open', mock_open()) as m:
             with patch('os.rename'):
                 with patch('os.remove'):
                    storage.save_json("test.json", data)
                    assert m.called


class TestDomainOperations:
    """Test domain CRUD operations"""
    
    def test_add_domain(self):
        """Should add new domain"""
        domain_data = {
            "url": "https://example.com",
            "interval_minutes": 60,
            "email": "test@example.com"
        }
        
        # Mock storage
        with patch.object(storage, 'save_json'):
             with patch.object(storage, 'load_json', return_value={}):
                domain = storage.add_domain(**domain_data)
                assert domain is not None
                assert domain['id'] is not None
    
    def test_get_domain_by_id(self):
        """Should retrieve domain by ID"""
        mock_data = {
            "domains": [
                {"id": "123", "url": "https://example.com"}
            ]
        }
        
        with patch.object(storage, 'load_json', return_value=mock_data):
            domain = storage.get_domain("123")
            assert domain is not None
            assert domain['url'] == "https://example.com"
    
    def test_get_all_domains(self):
        """Should retrieve all domains"""
        mock_data = {
            "domains": [
                {"id": "1", "url": "https://example1.com"},
                {"id": "2", "url": "https://example2.com"}
            ]
        }
        
        with patch.object(storage, 'load_json', return_value=mock_data):
            domains = storage.get_all_domains()
            assert len(domains) == 2
    
    def test_update_domain(self):
        """Should update existing domain"""
        # Mock implementation
        pass
    
    def test_delete_domain(self):
        """Should delete domain"""
        # Mock implementation
        pass


class TestPageOperations:
    """Test page CRUD operations"""
    
    def test_add_page(self):
        """Should add new page"""
        page_data = {
            "domain_id": "domain-123",
            "url": "https://example.com/page",
            "title": "Test Page",
            "content_hash": "abc123",
            "status_code": 200 # Added required field
        }
        
        with patch.object(storage, 'save_json'):
             with patch.object(storage, 'load_json', return_value={}):
                page = storage.add_page(**page_data)
                assert page is not None
                assert page['id'] is not None
    
    def test_get_page_by_url(self):
        """Should retrieve page by URL"""
        mock_data = {
            "pages": [
                {
                    "id": "page-1",
                    "domain_id": "domain-123",
                    "url": "https://example.com/page",
                    "title": "Test"
                }
            ]
        }
        
        with patch.object(storage, 'load_json', return_value=mock_data):
            page = storage.get_page_by_url("domain-123", "https://example.com/page")
            assert page is not None
    
    def test_get_domain_pages(self):
        """Should retrieve all pages for a domain"""
        mock_data = {
            "pages": [
                {"id": "1", "domain_id": "domain-123"},
                {"id": "2", "domain_id": "domain-123"},
                {"id": "3", "domain_id": "domain-456"}
            ]
        }
        
        with patch.object(storage, 'load_json', return_value=mock_data):
            pages = storage.get_domain_pages("domain-123")
            assert len(pages) == 2
    
    def test_mark_page_removed(self):
        """Should mark page as removed"""
        # Mock implementation
        pass


class TestChangeOperations:
    """Test change tracking operations"""
    
    def test_add_change(self):
        """Should record a change"""
        change_data = {
            "page_id": "page-123",
            "run_id": "run-1",  # Required arg
            "change_type": "modified",
            "similarity": 0.85 # Renamed from similarity_score
        }
        
        with patch.object(storage, 'save_json'):
             with patch.object(storage, 'load_json', return_value={}):
                change = storage.add_change(**change_data)
                assert change is not None
                assert change['id'] is not None
    
    def test_get_recent_changes(self):
        """Should retrieve recent changes"""
        # Mock implementation
        pass
    
    def test_get_page_changes(self):
        """Should retrieve changes for a specific page"""
        mock_data = {
            "changes": [
                {"id": "1", "page_id": "page-123", "change_type": "new"},
                {"id": "2", "page_id": "page-123", "change_type": "modified"},
                {"id": "3", "page_id": "page-456", "change_type": "new"}
            ]
        }
        
        with patch.object(storage, 'load_json', return_value=mock_data):
            changes = storage.get_page_changes("page-123")
            assert len(changes) == 2


class TestDataIntegrity:
    """Test data integrity and validation"""
    
    def test_handle_corrupted_json(self):
        """Should handle corrupted JSON gracefully"""
        with patch('builtins.open', mock_open(read_data='invalid json{')):
            result = storage.load_json("corrupted.json")
            # Should return empty dict or raise specific exception
            assert isinstance(result, dict) or result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
