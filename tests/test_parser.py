"""Tests for resume parser supporting multiple file formats."""

import os
import pytest
from pathlib import Path
from app.parser import ResumeParser
from app.schemas import ParsedResume


@pytest.fixture
def parser():
    """Create a ResumeParser instance."""
    return ResumeParser()


@pytest.fixture
def sample_resume_txt():
    """Get path to sample TXT resume."""
    return Path(__file__).parent / "sample_resume.txt"


class TestResumeParserBasic:
    """Test basic resume parsing functionality."""
    
    def test_parse_text_directly(self, parser):
        """Test parsing resume text directly."""
        resume_text = """
        John Doe
        john@example.com
        
        EXPERIENCE
        Senior Developer at Company
        
        SKILLS
        Python, JavaScript
        """
        
        result = parser.parse(resume_text)
        
        assert isinstance(result, ParsedResume)
        assert result.text is not None
        assert result.contact_info is not None
        assert "john@example.com" in result.contact_info.get("email", "")
    
    def test_extract_email(self, parser):
        """Test email extraction."""
        resume_text = "Contact: jane@company.com"
        result = parser.parse(resume_text)
        
        assert result.contact_info is not None
        assert "jane@company.com" in result.contact_info.get("email", "")
    
    def test_extract_phone(self, parser):
        """Test phone number extraction."""
        resume_text = "Phone: (555) 123-4567"
        result = parser.parse(resume_text)
        
        assert result.contact_info is not None
        assert "555" in result.contact_info.get("phone", "")
    
    def test_extract_linkedin(self, parser):
        """Test LinkedIn URL extraction."""
        resume_text = "LinkedIn: linkedin.com/in/johndoe"
        result = parser.parse(resume_text)
        
        assert result.contact_info is not None
        assert "linkedin.com/in/johndoe" in result.contact_info.get("linkedin", "")
    
    def test_extract_skills(self, parser):
        """Test skills extraction from resume sections."""
        resume_text = """
        SKILLS
        Python, JavaScript, Java
        Docker, Kubernetes
        """
        result = parser.parse(resume_text)
        
        assert len(result.skills) > 0
        assert any("Python" in skill for skill in result.skills)
    
    def test_extract_experience(self, parser):
        """Test experience extraction."""
        resume_text = """
        EXPERIENCE
        Senior Developer at Tech Corp
        Led development team
        
        Junior Developer at StartUp
        Built web applications
        """
        result = parser.parse(resume_text)
        
        assert len(result.experience) > 0
    
    def test_extract_education(self, parser):
        """Test education extraction."""
        resume_text = """
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology
        """
        result = parser.parse(resume_text)
        
        assert len(result.education) > 0
    
    def test_extract_sections(self, parser):
        """Test section extraction from resume."""
        resume_text = """
        CONTACT
        john@example.com
        
        SUMMARY
        Experienced professional
        
        SKILLS
        Python, Java
        
        EXPERIENCE
        Developer role
        """
        result = parser.parse(resume_text)
        
        assert result.sections is not None
        assert len(result.sections) > 0


class TestFileReading:
    """Test file reading capabilities."""
    
    def test_txt_file_reading(self, parser, sample_resume_txt):
        """Test reading .txt resume file."""
        if not sample_resume_txt.exists():
            pytest.skip("Sample resume not found")
        
        result = parser.parse_file(str(sample_resume_txt))
        
        assert isinstance(result, ParsedResume)
        assert len(result.text) > 0
        assert result.contact_info is not None
        assert "john.doe@example.com" in result.contact_info.get("email", "")
    
    def test_file_not_found(self, parser):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/path/resume.txt")
    
    def test_unsupported_file_format(self, parser, tmp_path):
        """Test error handling for unsupported file formats."""
        unsupported_file = tmp_path / "resume.xyz"
        unsupported_file.write_text("resume content")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_file(str(unsupported_file))
    
    def test_txt_read_method(self, parser, sample_resume_txt):
        """Test _read_txt_file method."""
        if not sample_resume_txt.exists():
            pytest.skip("Sample resume not found")
        
        text = parser._read_txt_file(str(sample_resume_txt))
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert "john" in text.lower() or "experience" in text.lower()


class TestPDFSupport:
    """Test PDF file support."""
    
    def test_pdf_read_without_import(self, parser):
        """Test handling when pdfplumber is not available."""
        # This test verifies graceful error handling
        # If pdfplumber is installed, it will pass the import check
        try:
            import pdfplumber  # noqa: F401
            pytest.skip("pdfplumber is installed, skipping import error test")
        except ImportError:
            with pytest.raises(ImportError):
                parser._read_pdf_file("dummy.pdf")
    
    def test_pdf_file_not_found(self, parser):
        """Test error handling for missing PDF file."""
        try:
            import pdfplumber  # noqa: F401
            with pytest.raises(ValueError):
                parser._read_pdf_file("/nonexistent/resume.pdf")
        except ImportError:
            pytest.skip("pdfplumber not installed")


class TestDOCXSupport:
    """Test DOCX file support."""
    
    def test_docx_read_without_import(self, parser):
        """Test handling when python-docx is not available."""
        try:
            from docx import Document  # noqa: F401
            pytest.skip("python-docx is installed, skipping import error test")
        except ImportError:
            with pytest.raises(ImportError):
                parser._read_docx_file("dummy.docx")
    
    def test_docx_file_not_found(self, parser):
        """Test error handling for missing DOCX file."""
        try:
            from docx import Document  # noqa: F401
            with pytest.raises(ValueError):
                parser._read_docx_file("/nonexistent/resume.docx")
        except ImportError:
            pytest.skip("python-docx not installed")


class TestParsingOutputStructure:
    """Test the structure of parsed resume output."""
    
    def test_parsed_resume_schema(self, parser):
        """Test that ParsedResume schema is correctly populated."""
        resume_text = """
        John Doe
        john@example.com | (555) 123-4567
        
        PROFESSIONAL SUMMARY
        Experienced developer
        
        SKILLS
        Python, Docker, Kubernetes
        
        EXPERIENCE
        Senior Developer at Tech Corp
        
        EDUCATION
        BS in Computer Science
        """
        
        result = parser.parse(resume_text)
        
        assert result.text is not None
        assert result.sections is not None
        assert result.contact_info is not None
        assert isinstance(result.skills, list)
        assert isinstance(result.experience, list)
        assert isinstance(result.education, list)
    
    def test_complex_resume_parsing(self, parser):
        """Test parsing a complex resume with multiple sections."""
        complex_resume = """
        Jane Smith
        jane.smith@tech.com | +1(555)987-6543 | linkedin.com/in/janesmith
        
        PROFESSIONAL SUMMARY
        Full-stack engineer with 8 years of experience
        
        WORK EXPERIENCE
        Principal Engineer at Cloud Systems
        June 2022 - Present
        • Architected microservices platform
        • Led team of 10 engineers
        
        Senior Developer at Web Solutions
        January 2020 - May 2022
        • Developed customer portal
        
        TECHNICAL SKILLS
        Languages: Python, Go, Rust, JavaScript, TypeScript
        Cloud: AWS, GCP, Azure
        Databases: PostgreSQL, MongoDB, Elasticsearch
        
        EDUCATION
        Master of Science in Computer Science
        Tech University, 2018
        
        Bachelor of Science in Engineering
        State University, 2016
        """
        
        result = parser.parse(complex_resume)
        
        # Verify all sections are extracted
        assert len(result.skills) > 0
        assert len(result.experience) > 0
        assert len(result.education) > 0
        assert result.contact_info is not None
        
        # Verify contact info extraction
        assert "jane.smith@tech.com" in result.contact_info.get("email", "")
        assert "555" in result.contact_info.get("phone", "")
        assert "linkedin.com/in/janesmith" in result.contact_info.get("linkedin", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
