"""
Unit tests for core scraping functionality
"""

import pytest
import hashlib
from scraper import core
from unittest.mock import Mock, patch, MagicMock


class TestHashCalculation:
    """Test content hashing"""
    
    def test_calculate_hash_consistent(self):
        """Hash should be consistent for same input"""
        text = "Hello, World!"
        hash1 = core.compute_hash(text)
        hash2 = core.compute_hash(text)
        assert hash1 == hash2
    
    def test_calculate_hash_different(self):
        """Different text should produce different hashes"""
        hash1 = core.compute_hash("Text 1")
        hash2 = core.compute_hash("Text 2")
        assert hash1 != hash2
    
    def test_calculate_hash_sha256(self):
        """Hash should be SHA256"""
        text = "Test"
        expected = hashlib.sha256(text.encode('utf-8')).hexdigest()
        result = core.compute_hash(text)
        assert result == expected


class TestSimilarityCalculation:
    """Test similarity scoring"""
    
    def test_identical_texts(self):
        """Identical texts should have 100% similarity"""
        text = "This is a test"
        similarity = core.calculate_similarity(text, text)
        assert similarity == 1.0
    
    def test_completely_different(self):
        """Completely different texts should have low similarity"""
        text1 = "Hello World"
        text2 = "Goodbye Universe"
        similarity = core.calculate_similarity(text1, text2)
        assert similarity < 0.5
    
    def test_minor_change(self):
        """Minor changes should have high similarity"""
        text1 = "The quick brown fox"
        text2 = "The quick brown dog"
        similarity = core.calculate_similarity(text1, text2)
        assert similarity > 0.7


class TestDiffGeneration:
    """Test diff generation"""
    
    def test_generate_diff_no_change(self):
        """No diff for identical texts"""
        text = "Same text"
        diff = core.short_unified_diff(text, text)
        assert diff == ""
    
    def test_generate_diff_with_change(self):
        """Diff should show changes"""
        old = "Line 1\nLine 2\nLine 3"
        new = "Line 1\nModified Line 2\nLine 3"
        diff = core.short_unified_diff(old, new)
        assert "Modified" in diff or "-Line 2" in diff


class TestURLNormalization:
    """Test URL normalization"""
    
    def test_remove_trailing_slash(self):
        """Should remove trailing slash for non-root paths"""
        url = "https://example.com/page/"
        normalized = core.normalize_url(url)
        assert normalized == "https://example.com/page"

    def test_keep_root_slash(self):
        """Should keep trailing slash for root"""
        url = "https://example.com/"
        normalized = core.normalize_url(url)
        assert normalized == "https://example.com/"
    
    def test_remove_fragment(self):
        """Should remove URL fragments"""
        url = "https://example.com/page#section"
        normalized = core.normalize_url(url)
        assert "#section" not in normalized
    
    def test_lowercase_domain(self):
        """Should lowercase domain"""
        url = "https://EXAMPLE.COM/Page"
        normalized = core.normalize_url(url)
        assert "EXAMPLE" not in normalized


class TestRobotsTxt:
    """Test robots.txt compliance"""
    
    @patch('urllib.robotparser.RobotFileParser')
    def test_robots_txt_allowed(self, mock_parser):
        """Should allow when robots.txt permits"""
        mock_instance = Mock()
        mock_instance.can_fetch.return_value = True
        mock_parser.return_value = mock_instance
        
        result = core.allowed_by_robots("https://example.com/page")
        assert result is True
    
    @patch('urllib.robotparser.RobotFileParser')
    def test_robots_txt_disallowed(self, mock_parser):
        """Should block when robots.txt forbids"""
        mock_instance = Mock()
        mock_instance.can_fetch.return_value = False
        mock_parser.return_value = mock_instance
        
        with patch('scraper.core.get_robot_parser_for_domain', return_value=mock_instance):
             # Mocking the helper because allowed_by_robots calls it
             # Alternatively patch 'scraper.core.RobotFileParser' directly if used inside
             # core.py uses 'get_robot_parser_for_domain'
             result = core.allowed_by_robots("https://example.com/admin")
             assert result is False


class TestHTMLParsing:
    """Test HTML parsing"""
    
    def test_extract_title(self):
        """Should extract page title"""
        html = "<html><head><title>Test Page</title></head><body></body></html>"
        title, _, _ = core.parse_html(html)
        assert title == "Test Page"
    
    def test_extract_title_missing(self):
        """Should handle missing title"""
        html = "<html><body>No title</body></html>"
        title, _, _ = core.parse_html(html)
        assert title == "No Title"
    
    def test_extract_text(self):
        """Should extract text content"""
        html = "<html><body><p>Hello</p><p>World</p></body></html>"
        _, text, _ = core.parse_html(html)
        assert "Hello" in text
        assert "World" in text


class TestFileDetection:
    """Test file URL detection"""
    
    def test_pdf_detection(self):
        """Should detect PDF files"""
        url = "https://example.com/document.pdf"
        assert core.is_file_url(url) is True
    
    def test_image_detection(self):
        """Should detect image files"""
        urls = [
            "https://example.com/image.jpg",
            "https://example.com/photo.png",
            "https://example.com/pic.gif"
        ]
        for url in urls:
            assert core.is_file_url(url) is True
    
    def test_html_not_file(self):
        """HTML pages should not be detected as files"""
        url = "https://example.com/page.html"
        assert core.is_file_url(url) is False


class TestDomainComparison:
    """Test domain comparison"""
    
    def test_same_domain(self):
        """Should recognize same domain"""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert core.is_same_domain(url1, url2) is True
    
    def test_different_domain(self):
        """Should recognize different domains"""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"
        assert core.is_same_domain(url1, url2) is False
    
    def test_subdomain_handling(self):
        """Should handle subdomains correctly"""
        url1 = "https://www.example.com/page"
        url2 = "https://example.com/page"
        # Implementation normalizes www but compares exact netloc. 
        # is_same_domain replaces www. 
        # So it should be True
        assert core.is_same_domain(url1, url2) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
