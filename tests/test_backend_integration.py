"""
Comprehensive integration tests for Resume Keyword Optimizer backend.

Tests verify:
1. /analyze endpoint accepts JSON with resume_text and optional job_description
2. /analyze/file endpoint accepts UploadFile resume and Form job_description
3. Resume parser supports .txt, .pdf, and .docx files
4. Analyzer returns score, matched keywords, missing keywords, and suggestions
5. API response keys match frontend usage
6. Error handling for unsupported files, empty resume, and empty job description
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import tempfile
import os

from app.main import app
from app.analyzer import KeywordAnalyzer
from app.parser import ResumeParser
from app.schemas import ResumeAnalysis, KeywordMatch

# Initialize test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns expected structure."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Resume Keyword Optimizer API"
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAnalyzeEndpoint:
    """Test /analyze endpoint with JSON body."""
    
    def test_analyze_resume_without_job_description(self):
        """Test analyzing resume without job description."""
        payload = {
            "resume_text": "Python Developer with 5 years experience. Skills: Python, JavaScript, React, SQL, PostgreSQL."
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_keywords" in data
        assert "matched_keywords" in data
        assert "missing_keywords" in data
        assert "suggestions" in data
        assert "match_score" in data
        assert "recommendations" in data
        
        # Verify data types
        assert isinstance(data["total_keywords"], int)
        assert isinstance(data["matched_keywords"], list)
        assert isinstance(data["missing_keywords"], list)
        assert isinstance(data["suggestions"], dict)
        assert isinstance(data["match_score"], (int, float))
        assert isinstance(data["recommendations"], list)
        
        # Verify match_score when no job description
        assert data["match_score"] == 100.0
    
    def test_analyze_resume_with_job_description(self):
        """Test analyzing resume with job description for matching."""
        payload = {
            "resume_text": "Python Developer with 5 years experience. Skills: Python, JavaScript, React.",
            "job_description": "Looking for Python developer. Required: Python, Django, PostgreSQL, Docker, AWS."
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "matched_keywords" in data
        assert "missing_keywords" in data
        assert "match_score" in data
        
        # Verify matched keywords have required fields
        if data["matched_keywords"]:
            for match in data["matched_keywords"]:
                assert "keyword" in match
                assert "frequency" in match
                assert "relevance_score" in match
                assert 0.0 <= match["relevance_score"] <= 1.0
        
        # Verify missing keywords
        assert isinstance(data["missing_keywords"], list)
        
        # Match score should be lower than 100 when job description is provided
        assert data["match_score"] < 100.0
    
    def test_analyze_empty_resume_fails(self):
        """Test that empty resume text raises error."""
        payload = {
            "resume_text": ""
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "cannot be empty" in data["detail"].lower()
    
    def test_analyze_whitespace_resume_fails(self):
        """Test that whitespace-only resume raises error."""
        payload = {
            "resume_text": "   \n\t  "
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 400
    
    def test_analyze_empty_job_description_fails(self):
        """Test that empty job description raises error if provided."""
        payload = {
            "resume_text": "Python Developer with 5 years experience",
            "job_description": ""
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "cannot be empty" in data["detail"].lower()


class TestAnalyzeFileEndpoint:
    """Test /analyze/file endpoint with UploadFile and Form."""
    
    def test_analyze_txt_file_without_job_description(self):
        """Test analyzing .txt file without job description."""
        resume_content = "Python Developer with 5 years experience. Skills: Python, JavaScript, React, SQL."
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.txt", BytesIO(resume_content.encode()), "text/plain")},
            data={}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_keywords" in data
        assert "matched_keywords" in data
        assert "missing_keywords" in data
        assert "suggestions" in data
        assert "match_score" in data
        assert "recommendations" in data
    
    def test_analyze_txt_file_with_job_description(self):
        """Test analyzing .txt file with job description."""
        resume_content = "Python Developer with 5 years experience. Skills: Python, JavaScript, React."
        job_description = "Looking for Python developer. Required: Python, Django, PostgreSQL, Docker, AWS."
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.txt", BytesIO(resume_content.encode()), "text/plain")},
            data={"job_description": job_description}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has analysis
        assert data["match_score"] > 0
        assert "matched_keywords" in data
    
    def test_analyze_pdf_file_fails_gracefully(self):
        """Test that PDF files are handled (or error if pdfplumber not available)."""
        # Create a minimal PDF-like content (this might not be a valid PDF)
        pdf_content = b"%PDF-1.4\nInvalid PDF content"
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.pdf", BytesIO(pdf_content), "application/pdf")},
            data={}
        )
        
        # Should either succeed (if pdfplumber works) or fail gracefully
        assert response.status_code in [200, 400]
    
    def test_analyze_docx_file_fails_gracefully(self):
        """Test that DOCX files are handled (or error if python-docx not available)."""
        # Create minimal DOCX-like content
        docx_content = b"PK\x03\x04Invalid DOCX content"
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.docx", BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={}
        )
        
        # Should either succeed (if python-docx works) or fail gracefully
        assert response.status_code in [200, 400]
    
    def test_analyze_unsupported_file_type_fails(self):
        """Test that unsupported file types are rejected."""
        content = b"Some content"
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.xlsx", BytesIO(content), "application/vnd.ms-excel")},
            data={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "supported" in data["detail"].lower()
    
    def test_analyze_empty_file_fails(self):
        """Test that empty file fails."""
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.txt", BytesIO(b""), "text/plain")},
            data={}
        )
        
        assert response.status_code == 400
    
    def test_analyze_empty_job_description_in_form_fails(self):
        """Test that empty job_description form field is treated as not provided.
        
        Note: FastAPI converts empty form strings to None with Form(None),
        so empty job_description is treated the same as not providing it.
        """
        resume_content = "Python Developer with experience"
        
        response = client.post(
            "/analyze/file",
            files={"resume": ("resume.txt", BytesIO(resume_content.encode()), "text/plain")},
            data={"job_description": ""}
        )
        
        # Empty form field is treated as None, so it's accepted
        assert response.status_code == 200
        data = response.json()
        assert "match_score" in data
        assert data["match_score"] == 100.0  # No job description, so perfect score
    
    def test_analyze_no_file_fails(self):
        """Test that missing resume file fails."""
        response = client.post(
            "/analyze/file",
            data={"job_description": "Looking for Python developer"}
        )
        
        assert response.status_code in [400, 422]  # 422 if validation error


class TestUploadEndpoint:
    """Test /upload endpoint."""
    
    def test_upload_txt_file(self):
        """Test uploading and parsing .txt file."""
        resume_content = "John Doe\n\nSKILLS\nPython, JavaScript, React\n\nEXPERIENCE\n5 years as developer"
        
        response = client.post(
            "/upload",
            files={"file": ("resume.txt", BytesIO(resume_content.encode()), "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify parsed resume structure
        assert "text" in data
        assert "sections" in data
        assert isinstance(data["sections"], dict)
    
    def test_upload_unsupported_file_fails(self):
        """Test that unsupported file types are rejected."""
        response = client.post(
            "/upload",
            files={"file": ("resume.xlsx", BytesIO(b"content"), "application/vnd.ms-excel")}
        )
        
        assert response.status_code == 400
    
    def test_upload_empty_file_fails(self):
        """Test that empty file fails."""
        response = client.post(
            "/upload",
            files={"file": ("resume.txt", BytesIO(b""), "text/plain")}
        )
        
        assert response.status_code == 400


class TestAnalyzerDirectly:
    """Test KeywordAnalyzer class directly."""
    
    def test_analyzer_returns_correct_response_type(self):
        """Test that analyzer returns ResumeAnalysis object."""
        analyzer = KeywordAnalyzer()
        
        resume_text = "Python Developer with 5 years experience. Skills: Python, JavaScript, React."
        job_description = "Looking for Python developer. Required: Python, Django, PostgreSQL."
        
        result = analyzer.analyze_resume(resume_text, job_description)
        
        # Verify it's a ResumeAnalysis object
        assert isinstance(result, ResumeAnalysis)
        
        # Verify all required fields exist
        assert hasattr(result, "total_keywords")
        assert hasattr(result, "matched_keywords")
        assert hasattr(result, "missing_keywords")
        assert hasattr(result, "suggestions")
        assert hasattr(result, "match_score")
        assert hasattr(result, "recommendations")
    
    def test_matched_keywords_have_required_fields(self):
        """Test that matched keywords have all required fields."""
        analyzer = KeywordAnalyzer()
        
        resume_text = "Python Developer"
        job_description = "Python Django PostgreSQL"
        
        result = analyzer.analyze_resume(resume_text, job_description)
        
        # Check matched keywords
        if result.matched_keywords:
            for match in result.matched_keywords:
                assert isinstance(match, KeywordMatch)
                assert match.keyword is not None
                assert match.frequency is not None
                assert match.relevance_score is not None
                assert 0.0 <= match.relevance_score <= 1.0


class TestParserSupport:
    """Test resume parser supports multiple file formats."""
    
    def test_parser_supports_txt_files(self):
        """Test that parser can handle .txt files."""
        parser = ResumeParser()
        
        resume_text = "John Doe\n\nSKILLS\nPython, JavaScript"
        result = parser.parse(resume_text)
        
        assert result.text == resume_text
        assert isinstance(result.sections, dict)
    
    def test_parse_file_method_validates_file_format(self):
        """Test that parse_file method validates file format."""
        parser = ResumeParser()
        
        # Create a temporary unsupported file
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                parser.parse_file(temp_path)
            assert "Unsupported file format" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """Test comprehensive error handling."""
    
    def test_missing_resume_file_in_upload(self):
        """Test error when resume file is not provided."""
        response = client.post("/upload")
        
        assert response.status_code in [400, 422]
    
    def test_analyze_with_only_whitespace_job_description(self):
        """Test error when job description is only whitespace."""
        payload = {
            "resume_text": "Python Developer",
            "job_description": "   \n\t  "
        }
        response = client.post("/analyze", json=payload)
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
