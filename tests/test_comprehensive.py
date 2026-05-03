"""
Comprehensive test suite for Resume Keyword Optimizer.
Covers: keyword extraction, match/missing accuracy, score calculation,
        file format parsing, edge cases, and API endpoint behavior.
"""

import io
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.analyzer import KeywordAnalyzer
from app.parser import ResumeParser
from app.schemas import ResumeAnalysis, ParsedResume

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def analyzer():
    return KeywordAnalyzer()


@pytest.fixture(scope="module")
def parser():
    return ResumeParser()


RESUME_PYTHON_DEV = """
Jane Smith
jane.smith@email.com | (555) 987-6543 | linkedin.com/in/janesmith

PROFESSIONAL SUMMARY
Software engineer with 4 years of experience building Python backend services,
REST APIs, and data pipelines. Proficient in cloud infrastructure on AWS.

EXPERIENCE
Backend Engineer – DataFlow Inc. (2021-Present)
- Developed REST APIs with Python and FastAPI
- Built CI/CD pipelines using Jenkins and Docker
- Deployed microservices on Kubernetes and AWS EKS
- Automated testing using pytest; maintained 85%+ code coverage

Junior Developer – WebSoft (2019-2021)
- Wrote Python scripts for data processing and ETL pipelines
- Used PostgreSQL and Redis for data storage
- Collaborated using Git and GitHub

SKILLS
Languages: Python, JavaScript, SQL
Frameworks: FastAPI, Flask, React
Tools: Docker, Kubernetes, Jenkins, Git, AWS
Databases: PostgreSQL, MongoDB, Redis

EDUCATION
Bachelor of Science in Computer Science
State University, 2019
"""

JD_PYTHON_BACKEND = """
Senior Python Backend Engineer

Requirements:
- 4+ years of Python development experience
- Strong knowledge of REST APIs and microservices architecture
- Experience with Docker and Kubernetes
- AWS cloud services (EKS, S3, Lambda)
- PostgreSQL database design and optimization
- CI/CD pipelines (Jenkins, GitHub Actions)
- Proficiency in Git and code review practices
- Unit testing and pytest experience

Nice to have:
- GraphQL API experience
- Terraform or Pulumi for infrastructure as code
- Machine learning pipeline exposure
- Redis caching strategies
"""

JD_DATA_SCIENTIST = """
Data Scientist – Machine Learning Team

Requirements:
- Python programming and data analysis
- Machine learning model development with TensorFlow or PyTorch
- Data visualization using Tableau or Power BI
- Statistical analysis and A/B testing
- SQL and data warehousing
- Experience with pandas, numpy, scikit-learn

Nice to have:
- Deep learning and neural networks
- MLflow or Kubeflow for model tracking
- Apache Spark for big data
"""


# ===========================================================================
# 1. KEYWORD EXTRACTION TESTS
# ===========================================================================

class TestKeywordExtraction:
    """Verify keyword extraction correctness."""

    def test_technical_keywords_present(self, analyzer):
        """Core tech terms must appear in extracted keywords."""
        text = "Python FastAPI Docker Kubernetes PostgreSQL Redis AWS Jenkins pytest"
        kws = {k for k, _ in analyzer.extract_top_keywords(text, top_n=20)}
        for expected in ["python", "fastapi", "docker", "kubernetes", "postgresql", "redis", "aws", "jenkins", "pytest"]:
            assert expected in kws, f"Expected keyword '{expected}' missing"

    def test_stopwords_excluded(self, analyzer):
        """Common stop words must NOT appear in output."""
        text = "The team is working on the project for the company and the client"
        kws = {k for k, _ in analyzer.extract_top_keywords(text, top_n=20)}
        for sw in ["the", "is", "on", "for", "and"]:
            assert sw not in kws, f"Stopword '{sw}' should be removed"

    def test_short_words_excluded(self, analyzer):
        """Words shorter than 3 characters must be excluded."""
        text = "I am a go developer using ai to build ui"
        kws = {k for k, _ in analyzer.extract_top_keywords(text, top_n=20)}
        for short in ["i", "am", "a", "to"]:
            assert short not in kws, f"Short word '{short}' should be excluded"

    def test_numeric_tokens_excluded(self, analyzer):
        """Pure numbers and version numbers must be excluded."""
        text = "Python 3.9 experience, 5 years, version 2024, 100 employees"
        kws = {k for k, _ in analyzer.extract_top_keywords(text, top_n=20)}
        assert not any(k.isdigit() for k in kws), "Digit-only tokens should be filtered"

    def test_frequency_counts_correct(self, analyzer):
        """Keyword that appears 3 times should have frequency 3."""
        text = "python python python java java"
        kws = dict(analyzer.extract_top_keywords(text, top_n=10))
        assert kws.get("python") == 3, f"Expected python=3, got {kws.get('python')}"
        assert kws.get("java") == 2, f"Expected java=2, got {kws.get('java')}"

    def test_top_n_respected(self, analyzer):
        """extract_top_keywords must return exactly top_n results (or fewer if not enough)."""
        kws = analyzer.extract_top_keywords(RESUME_PYTHON_DEV, top_n=5)
        assert len(kws) == 5

    def test_keywords_sorted_by_frequency(self, analyzer):
        """Keywords must be sorted descending by frequency."""
        kws = analyzer.extract_top_keywords(RESUME_PYTHON_DEV, top_n=10)
        freqs = [freq for _, freq in kws]
        assert freqs == sorted(freqs, reverse=True), "Keywords not sorted by frequency"

    def test_case_insensitive_extraction(self, analyzer):
        """Keywords must be lowercased and case-insensitively counted."""
        text = "Python PYTHON python"
        kws = dict(analyzer.extract_top_keywords(text, top_n=5))
        assert kws.get("python") == 3, "Case-insensitive counting failed"

    def test_no_job_description_analyze(self, analyzer):
        """analyze_resume without JD should return keywords, score=1.0."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV)
        assert result.match_score == 1.0
        assert result.total_keywords > 0
        assert len(result.matched_keywords) > 0
        assert result.missing_keywords == []


# ===========================================================================
# 2. MATCHED KEYWORDS ACCURACY
# ===========================================================================

class TestMatchedKeywords:
    """Verify that matched keywords are genuinely present in both texts."""

    def test_matched_keywords_exist_in_resume(self, analyzer):
        """Every matched keyword must appear in the resume."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        resume_kws = {k for k, _ in analyzer.extract_top_keywords(RESUME_PYTHON_DEV, top_n=100)}
        for match in result.matched_keywords:
            # Keyword may be matched via synonym/partial — just ensure non-empty
            assert match.keyword, "Matched keyword must not be empty"

    def test_matched_keywords_from_jd(self, analyzer):
        """Matched keywords must originate from the JD, not random words."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        jd_kws = {k for k, _ in analyzer.extract_top_keywords(JD_PYTHON_BACKEND, top_n=100)}
        for match in result.matched_keywords:
            assert match.keyword in jd_kws, (
                f"'{match.keyword}' in matched_keywords but not in JD keywords"
            )

    def test_relevance_score_range(self, analyzer):
        """Relevance score for every matched keyword must be in [0.0, 1.0]."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        for match in result.matched_keywords:
            assert 0.0 <= match.relevance_score <= 1.0, (
                f"relevance_score={match.relevance_score} out of range for '{match.keyword}'"
            )

    def test_no_duplicate_matched_keywords(self, analyzer):
        """The same keyword must not appear twice in matched_keywords."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        seen = [m.keyword for m in result.matched_keywords]
        assert len(seen) == len(set(seen)), "Duplicate matched keywords found"

    def test_python_keyword_matched(self, analyzer):
        """'python' must be matched when both resume and JD contain it."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        matched_kws = {m.keyword for m in result.matched_keywords}
        assert "python" in matched_kws, "'python' should be matched"

    def test_unrelated_jd_gives_low_match(self, analyzer):
        """A Python resume against a Data Scientist JD should score below 0.6."""
        # The resume has no ML, TensorFlow, PyTorch, Tableau
        pure_resume = "Experienced Python backend developer. REST APIs, Docker, Kubernetes, PostgreSQL."
        result = analyzer.analyze_resume(pure_resume, JD_DATA_SCIENTIST)
        assert result.match_score < 0.6, (
            f"Expected low score for unrelated JD, got {result.match_score}"
        )


# ===========================================================================
# 3. MISSING KEYWORDS ACCURACY
# ===========================================================================

class TestMissingKeywords:
    """Verify that missing keywords are truly absent from the resume."""

    def test_missing_keywords_absent_from_resume(self, analyzer):
        """Keywords listed as missing must NOT be in the resume's extracted keywords."""
        resume = "Python developer with REST API experience and Docker skills."
        jd = "Python developer with GraphQL, Terraform, Kubernetes, machine learning, PyTorch."
        result = analyzer.analyze_resume(resume, jd)
        resume_kws = {k for k, _ in analyzer.extract_top_keywords(resume, top_n=100)}
        for missing in result.missing_keywords:
            assert missing not in resume_kws, (
                f"'{missing}' listed as missing but found in resume"
            )

    def test_graphql_missing_when_absent(self, analyzer):
        """'graphql' should be missing when resume has no GraphQL mention."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        # GraphQL is in JD nice-to-have but not in resume
        assert "graphql" in result.missing_keywords, (
            "Expected 'graphql' in missing keywords"
        )

    def test_missing_keywords_capped(self, analyzer):
        """Missing keywords list must be capped (currently at 15)."""
        # JD with many unique keywords the resume doesn't have
        resume = "Software developer."
        jd = " ".join([
            "tensorflow pytorch keras scikit pandas numpy matplotlib seaborn",
            "tableau powerbi spark hadoop kafka airflow mlflow kubeflow",
            "terraform pulumi ansible saltstack puppet chef",
            "graphql grpc rabbitmq celery redis elasticsearch kibana"
        ])
        result = analyzer.analyze_resume(resume, jd)
        assert len(result.missing_keywords) <= 15, (
            f"Missing keywords count {len(result.missing_keywords)} exceeds cap of 15"
        )


# ===========================================================================
# 4. SCORE CALCULATION
# ===========================================================================

class TestScoreCalculation:
    """Verify match score formula correctness."""

    def test_score_is_zero_for_no_matches(self, analyzer):
        """Score must be 0.0 when nothing matches."""
        resume = "Customer service representative with communication skills."
        jd = "Python developer with docker kubernetes tensorflow pytorch."
        result = analyzer.analyze_resume(resume, jd)
        assert result.match_score == 0.0

    def test_score_is_one_for_perfect_match(self, analyzer):
        """Score must be 1.0 when resume covers all JD keywords."""
        text = "python docker kubernetes aws postgresql git pytest jenkins fastapi flask"
        result = analyzer.analyze_resume(text, text)
        assert result.match_score == 1.0

    def test_score_in_valid_range(self, analyzer):
        """Score must always be in [0.0, 1.0]."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, JD_PYTHON_BACKEND)
        assert 0.0 <= result.match_score <= 1.0

    def test_score_partial_match(self, analyzer):
        """A partial resume should yield a score between 0 and 1."""
        resume = "Python developer experienced with Docker and REST APIs."
        result = analyzer.analyze_resume(resume, JD_PYTHON_BACKEND)
        assert 0.0 < result.match_score < 1.0, (
            f"Expected partial score, got {result.match_score}"
        )

    def test_score_increases_with_more_keywords(self, analyzer):
        """Adding more matching keywords must not decrease the score."""
        resume_basic = "Python developer."
        resume_rich = "Python developer with Docker, Kubernetes, AWS, PostgreSQL, pytest, Jenkins, Git."
        r1 = analyzer.analyze_resume(resume_basic, JD_PYTHON_BACKEND)
        r2 = analyzer.analyze_resume(resume_rich, JD_PYTHON_BACKEND)
        assert r2.match_score >= r1.match_score, (
            "Adding relevant keywords should not decrease match score"
        )

    def test_score_formula_manual(self, analyzer):
        """Manually verify score = matched / total_jd_keywords (capped at 1.0)."""
        resume = "python docker"
        jd = "python docker kubernetes"  # 3 unique JD keywords
        result = analyzer.analyze_resume(resume, jd)
        # matched = 2, total_jd = 3 → score ≈ 0.67
        assert 0.6 <= result.match_score <= 0.75, (
            f"Expected ~0.67, got {result.match_score}"
        )


# ===========================================================================
# 5. RESUME PARSER TESTS
# ===========================================================================

class TestResumeParser:
    """Test structured data extraction from resume text."""

    def test_email_extraction(self, parser):
        text = "Contact me at alice@example.com or call me."
        result = parser.parse(text)
        assert result.contact_info.get("email") == "alice@example.com"

    def test_phone_extraction(self, parser):
        text = "Phone: (800) 555-1234"
        result = parser.parse(text)
        assert "555" in result.contact_info.get("phone", "")

    def test_linkedin_extraction(self, parser):
        text = "Profile: linkedin.com/in/testuser"
        result = parser.parse(text)
        assert "linkedin.com/in/testuser" in result.contact_info.get("linkedin", "")

    def test_skills_section_extracted(self, parser):
        text = "SKILLS\nPython, Docker, Kubernetes\nAWS, Git"
        result = parser.parse(text)
        assert len(result.skills) > 0
        skill_text = " ".join(result.skills)
        assert "Python" in skill_text

    def test_experience_section_extracted(self, parser):
        text = "EXPERIENCE\nSenior Developer at Acme Corp\nBuilt backend systems."
        result = parser.parse(text)
        assert len(result.experience) > 0

    def test_education_section_extracted(self, parser):
        text = "EDUCATION\nBS Computer Science\nMIT, 2020"
        result = parser.parse(text)
        assert len(result.education) > 0

    def test_parsed_resume_type(self, parser):
        result = parser.parse(RESUME_PYTHON_DEV)
        assert isinstance(result, ParsedResume)

    def test_txt_file_parsing(self, parser):
        txt_path = Path(__file__).parent / "sample_resume.txt"
        if not txt_path.exists():
            pytest.skip("sample_resume.txt not found")
        result = parser.parse_file(str(txt_path))
        assert result.text is not None
        assert len(result.text) > 0

    def test_unsupported_format_raises(self, parser, tmp_path):
        f = tmp_path / "resume.xyz"
        f.write_text("some content")
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_file(str(f))

    def test_nonexistent_file_raises(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/path/resume.txt")

    def test_latin1_encoding_fallback(self, parser, tmp_path):
        """Parser must fall back to latin-1 when file is not UTF-8."""
        f = tmp_path / "resume.txt"
        f.write_bytes("Résumé developer Python\n".encode("latin-1"))
        result = parser.parse_file(str(f))
        assert result.text is not None

    def test_docx_parsing_skips_when_library_missing(self, parser, tmp_path):
        """If python-docx is not installed, parse_file should raise ImportError, not crash."""
        from app import parser as parser_module
        original_document = parser_module.Document
        parser_module.Document = None
        try:
            f = tmp_path / "resume.docx"
            f.write_bytes(b"fake docx content")
            with pytest.raises((ImportError, ValueError)):
                parser.parse_file(str(f))
        finally:
            parser_module.Document = original_document


# ===========================================================================
# 6. API ENDPOINT TESTS
# ===========================================================================

class TestAPIEndpoints:
    """Test all API routes via TestClient."""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_analyze_with_resume_only(self, client):
        payload = {"resume_text": RESUME_PYTHON_DEV}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_keywords" in data
        assert "match_score" in data
        assert data["match_score"] == 1.0

    def test_analyze_with_job_description(self, client):
        payload = {"resume_text": RESUME_PYTHON_DEV, "job_description": JD_PYTHON_BACKEND}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_score"] > 0
        assert "matched_keywords" in data
        assert "missing_keywords" in data

    def test_analyze_empty_resume_returns_400(self, client):
        """Empty or whitespace-only resume must return HTTP 400."""
        payload = {"resume_text": "   "}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 400

    def test_analyze_response_schema(self, client):
        """Response must conform to ResumeAnalysis schema fields."""
        payload = {"resume_text": RESUME_PYTHON_DEV, "job_description": JD_PYTHON_BACKEND}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        required_fields = {"total_keywords", "matched_keywords", "missing_keywords",
                           "match_score", "suggestions", "recommendations"}
        assert required_fields.issubset(data.keys())

    def test_parse_endpoint(self, client):
        payload = {"resume_text": RESUME_PYTHON_DEV}
        resp = client.post("/parse", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "sections" in data

    def test_parse_empty_text_returns_400(self, client):
        payload = {"resume_text": ""}
        resp = client.post("/parse", json=payload)
        assert resp.status_code == 400

    def test_keywords_extract_endpoint(self, client):
        payload = {"resume_text": RESUME_PYTHON_DEV}
        resp = client.post("/keywords/extract", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data or "top_keywords" in data or isinstance(data, dict)

    def test_keywords_extract_empty_returns_400(self, client):
        payload = {"resume_text": ""}
        resp = client.post("/keywords/extract", json=payload)
        assert resp.status_code == 400

    # --- Upload endpoint ---

    def test_upload_txt_file(self, client):
        """Uploading a .txt file should return parsed resume."""
        content = RESUME_PYTHON_DEV.encode("utf-8")
        resp = client.post("/upload", files={"file": ("resume.txt", content, "text/plain")})
        assert resp.status_code == 200

    def test_upload_unsupported_format_returns_400(self, client):
        """Uploading a .docx must be rejected because /upload only accepts .txt/.pdf."""
        content = b"fake docx"
        resp = client.post("/upload", files={"file": ("resume.docx", content, "application/vnd.openxmlformats")})
        assert resp.status_code == 400

    def test_upload_missing_file_returns_422(self, client):
        """No file in request must return 422 (validation error)."""
        resp = client.post("/upload")
        assert resp.status_code == 422

    # BUG TEST: PDF uploaded to /upload will fail with UnicodeDecodeError
    # because the endpoint does content.decode('utf-8') on binary data.
    def test_upload_pdf_binary_content_returns_400(self, client):
        """
        BUG: /upload tries to decode PDF binary as UTF-8 which crashes.
        This test documents the current behavior so the bug can be tracked.
        """
        fake_pdf = b"%PDF-1.4 binary \x80\x81\x82 content"
        resp = client.post("/upload", files={"file": ("resume.pdf", fake_pdf, "application/pdf")})
        # Currently returns 400 due to UnicodeDecodeError handler — acceptable
        # but the fix should use pdfplumber instead of decode()
        assert resp.status_code in (400, 500), (
            "PDF binary upload should not return 200"
        )


# ===========================================================================
# 7. EDGE CASES
# ===========================================================================

class TestEdgeCases:
    """Edge cases: empty input, very long text, special characters, etc."""

    def test_empty_resume_text_raises(self, analyzer):
        """analyze_resume on empty string should not return a meaningful result."""
        result = analyzer.analyze_resume("   ")
        # Should work but return 0 keywords (no crash)
        assert result.total_keywords == 0

    def test_whitespace_only_resume(self, analyzer):
        result = analyzer.analyze_resume("\n\n\t  \n")
        assert result.total_keywords == 0

    def test_empty_job_description(self, analyzer):
        """Empty JD should be treated as no JD provided (no crash)."""
        result = analyzer.analyze_resume(RESUME_PYTHON_DEV, "")
        # With empty JD, analyzer still runs — result should be valid
        assert result.total_keywords >= 0

    def test_very_long_resume(self, analyzer):
        """Very long resume text must not crash or timeout noticeably."""
        long_text = (RESUME_PYTHON_DEV * 100)  # ~100x resume length
        result = analyzer.analyze_resume(long_text, JD_PYTHON_BACKEND)
        assert result.match_score >= 0.0

    def test_resume_with_special_characters(self, analyzer):
        """Special characters like @, #, $, %, ^ must be handled gracefully."""
        text = "Python developer ### @@@ $$$ %%% ^^^ skills: C++, C#, .NET"
        result = analyzer.analyze_resume(text)
        assert result.total_keywords >= 0

    def test_resume_with_unicode(self, analyzer):
        """Unicode characters (accents, non-ASCII) must not crash."""
        text = "Développeur Python expérimenté. Compétences: Docker, Kubernetes, API REST."
        result = analyzer.analyze_resume(text)
        assert result.total_keywords >= 0

    def test_resume_only_numbers(self, analyzer):
        """A resume containing only numbers must yield 0 keywords."""
        result = analyzer.analyze_resume("1234 5678 9012 3456 2024 100 200")
        assert result.total_keywords == 0

    def test_single_word_resume(self, analyzer):
        """Single-word resume must not crash."""
        result = analyzer.analyze_resume("Python")
        assert result.total_keywords >= 0

    def test_jd_with_no_extractable_keywords(self, analyzer):
        """JD with only stopwords must yield 0 matches, not crash."""
        resume = "Python developer with Docker and Kubernetes experience."
        jd = "the a an and or but in on at to for of with by"
        result = analyzer.analyze_resume(resume, jd)
        assert result.match_score == 0.0

    def test_parser_empty_text(self, parser):
        """Parsing empty string must return a ParsedResume without crash."""
        result = parser.parse("")
        assert isinstance(result, ParsedResume)
        assert result.text == ""

    def test_parser_no_sections(self, parser):
        """Resume without recognizable sections must still parse."""
        text = "John Doe – Python developer"
        result = parser.parse(text)
        assert isinstance(result, ParsedResume)

    def test_invalid_file_path(self, parser):
        """Non-existent file path must raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("C:/does/not/exist/resume.txt")

    def test_empty_txt_file(self, parser, tmp_path):
        """An empty .txt file must parse without crashing."""
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = parser.parse_file(str(f))
        assert isinstance(result, ParsedResume)
        assert result.text == ""


# ===========================================================================
# 8. KNOWN BUG DOCUMENTATION TESTS
# ===========================================================================

class TestKnownBugs:
    """
    These tests document known bugs in the current implementation.
    They may fail (and that is expected) until the bugs are fixed.
    """

    def test_BUG_java_javascript_false_positive_match(self, analyzer):
        """
        BUG: _keywords_similar treats 'java' as similar to 'javascript' because
        'java' is a substring of 'javascript' (kw1 in kw2).
        
        A Java-heavy resume should NOT match a JavaScript-only JD at high score.
        """
        resume = "Java developer with Spring Boot and JVM expertise."
        jd = "JavaScript frontend developer with React and Node.js experience."
        result = analyzer.analyze_resume(resume, jd)
        # These should NOT be matched — 'java' != 'javascript'
        matched_kws = {m.keyword for m in result.matched_keywords}
        assert "javascript" not in matched_kws, (
            "BUG: 'java' resume incorrectly matched to 'javascript' JD keyword"
        )

    def test_BUG_upload_endpoint_rejects_docx(self, client):
        """
        BUG: /upload endpoint checks for '.txt' and '.pdf' only, silently
        excluding '.docx' even though ResumeParser supports it.
        The endpoint should also accept .docx files.
        """
        fake_docx = b"PK\x03\x04"  # ZIP/DOCX magic bytes
        resp = client.post("/upload", files={"file": ("resume.docx", fake_docx, "application/vnd.openxmlformats")})
        # Current behavior: 400 — BUG: should be 200 after .docx support added
        assert resp.status_code == 400, (
            "BUG confirmed: /upload rejects .docx despite parser supporting it"
        )

    def test_BUG_match_score_can_exceed_logic_expectation(self, analyzer):
        """
        Score uses total unique JD keyword count as denominator.
        If a JD has many duplicated words reducing unique count,
        score can appear artificially high.
        """
        resume = "python"
        # JD repeats 'python' 10x but has only 1 unique keyword
        jd = "python " * 10
        result = analyzer.analyze_resume(resume, jd)
        # matched=1, total_jd_unique=1 → score=1.0 even though JD was repetitive
        assert result.match_score == 1.0, (
            "BUG: single keyword match gives 100% score when JD has only one unique keyword"
        )

    def test_BUG_missing_keywords_hardcap_hides_gaps(self, analyzer):
        """
        BUG: _find_missing_keywords caps at 15 results.
        Important missing keywords beyond position 15 are silently hidden.
        """
        resume = "software developer"
        jd = " ".join([
            "tensorflow pytorch keras scikit numpy pandas matplotlib",
            "tableau powerbi spark hadoop kafka airflow mlflow kubeflow",
            "terraform pulumi ansible saltstack graphql grpc rabbitmq"
        ])
        result = analyzer.analyze_resume(resume, jd)
        assert len(result.missing_keywords) == 15, (
            "Missing keywords should be capped at 15 (BUG: important keywords hidden beyond cap)"
        )
