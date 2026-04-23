"""Integration tests for file format support."""

import pytest
from pathlib import Path
from app.parser import ResumeParser


@pytest.fixture
def parser():
    """Create a ResumeParser instance."""
    return ResumeParser()


@pytest.fixture
def test_files_dir():
    """Get the test files directory."""
    return Path(__file__).parent


class TestFileFormats:
    """Test parsing files in different formats."""
    
    def test_txt_file_parsing(self, parser, test_files_dir):
        """Test complete parsing workflow for TXT file."""
        txt_file = test_files_dir / "sample_resume.txt"
        
        if not txt_file.exists():
            pytest.skip(f"Sample TXT file not found: {txt_file}")
        
        # Parse the file
        result = parser.parse_file(str(txt_file))
        
        # Verify the result structure
        assert result.text is not None
        assert len(result.text) > 0
        assert result.contact_info is not None
        assert result.sections is not None
        assert len(result.skills) > 0
        assert len(result.experience) > 0
        assert len(result.education) > 0
        
        # Verify specific content extraction
        assert "john" in result.text.lower()
        assert "john.doe@example.com" in result.contact_info.get("email", "")
    
    def test_docx_file_parsing(self, parser, test_files_dir):
        """Test complete parsing workflow for DOCX file."""
        docx_file = test_files_dir / "sample_resume.docx"
        
        if not docx_file.exists():
            pytest.skip(f"Sample DOCX file not found: {docx_file}")
        
        try:
            # Parse the file
            result = parser.parse_file(str(docx_file))
            
            # Verify the result structure
            assert result.text is not None
            assert len(result.text) > 0
            assert result.contact_info is not None
            assert result.sections is not None
            
            # At least one extraction should work
            assert len(result.skills) > 0 or len(result.experience) > 0 or len(result.education) > 0
            
        except ImportError:
            pytest.skip("python-docx is not installed")
    
    def test_multiple_file_reading(self, parser, test_files_dir):
        """Test reading multiple files sequentially."""
        txt_file = test_files_dir / "sample_resume.txt"
        docx_file = test_files_dir / "sample_resume.docx"
        
        files_to_test = []
        if txt_file.exists():
            files_to_test.append(("txt", txt_file))
        if docx_file.exists():
            files_to_test.append(("docx", docx_file))
        
        if not files_to_test:
            pytest.skip("No sample files found")
        
        results = {}
        for file_type, file_path in files_to_test:
            try:
                result = parser.parse_file(str(file_path))
                results[file_type] = result
                assert result.text is not None
                assert len(result.text) > 0
            except ImportError:
                # Skip if required library is missing
                pass
        
        # Should have at least parsed TXT
        assert len(results) > 0
    
    def test_file_content_extraction(self, parser, test_files_dir):
        """Test that file reading preserves content for parsing."""
        txt_file = test_files_dir / "sample_resume.txt"
        
        if not txt_file.exists():
            pytest.skip(f"Sample TXT file not found: {txt_file}")
        
        # Read file directly
        with open(txt_file, 'r', encoding='utf-8') as f:
            direct_text = f.read()
        
        # Read through parser
        parsed_result = parser.parse_file(str(txt_file))
        parsed_text = parsed_result.text
        
        # Verify content is preserved
        assert len(parsed_text) > 0
        # Check for key information presence
        assert any(word in direct_text.lower() and word in parsed_text.lower() 
                  for word in ['experience', 'skills', 'education', 'john', 'contact'])


class TestFileReadingMethods:
    """Test individual file reading methods."""
    
    def test_txt_read_preserves_encoding(self, parser, test_files_dir):
        """Test that TXT reading preserves text encoding properly."""
        txt_file = test_files_dir / "sample_resume.txt"
        
        if not txt_file.exists():
            pytest.skip("Sample TXT file not found")
        
        text = parser._read_txt_file(str(txt_file))
        
        # Check that text is properly decoded
        assert isinstance(text, str)
        assert len(text) > 0
        assert '\n' in text  # Should have newlines
    
    def test_docx_read_extracts_paragraphs(self, parser, test_files_dir):
        """Test that DOCX reading properly extracts paragraphs."""
        docx_file = test_files_dir / "sample_resume.docx"
        
        if not docx_file.exists():
            pytest.skip("Sample DOCX file not found")
        
        try:
            text = parser._read_docx_file(str(docx_file))
            
            # Check that text is properly extracted
            assert isinstance(text, str)
            assert len(text) > 0
            assert '\n' in text  # Should have newlines from multiple paragraphs
            
        except ImportError:
            pytest.skip("python-docx is not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
