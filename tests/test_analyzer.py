"""Tests for keyword analyzer and resume-JD comparison."""

import pytest
from app.analyzer import KeywordAnalyzer
from app.schemas import KeywordMatch


@pytest.fixture
def analyzer():
    """Create a KeywordAnalyzer instance."""
    return KeywordAnalyzer()


@pytest.fixture
def sample_resume():
    """Sample resume text."""
    return """
    John Doe
    john@example.com | (555) 123-4567
    
    PROFESSIONAL SUMMARY
    Experienced software developer with 5 years of experience in Python and JavaScript.
    Expertise in full-stack development, cloud architecture, and DevOps.
    
    EXPERIENCE
    Senior Developer at Tech Corp (2021-2024)
    - Led development of microservices architecture using Python
    - Implemented CI/CD pipelines with Docker and Kubernetes
    - Mentored junior developers
    - Technologies: Python, JavaScript, Docker, Kubernetes, AWS
    
    Developer at StartUp Inc (2019-2021)
    - Built REST APIs using Python and Flask
    - Developed React frontends for web applications
    - Implemented automated testing with pytest
    - Technologies: Python, JavaScript, React, PostgreSQL, Git
    
    SKILLS
    Programming Languages: Python, JavaScript, Java, SQL
    Frameworks: Django, Flask, React, Vue
    Tools & Technologies: Docker, Kubernetes, AWS, Git, Jenkins
    Databases: PostgreSQL, MongoDB
    Other: REST APIs, Microservices, CI/CD, DevOps
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2019
    """


@pytest.fixture
def sample_job_description():
    """Sample job description."""
    return """
    Senior Python Developer
    
    We are looking for an experienced Senior Python Developer to join our team.
    
    REQUIREMENTS
    - 5+ years of experience with Python development
    - Strong knowledge of software architecture and design patterns
    - Experience with microservices and distributed systems
    - Expertise in Docker and Kubernetes containerization
    - AWS cloud platform experience
    - Strong understanding of REST APIs and API design
    - Experience with relational databases (PostgreSQL, MySQL)
    - Proficiency with Git and version control
    - CI/CD pipeline experience
    - Knowledge of DevOps practices
    
    NICE TO HAVE
    - Machine Learning or data science experience
    - GraphQL knowledge
    - Kubernetes advanced patterns
    - Terraform or Infrastructure as Code
    - Agile/Scrum certification
    
    RESPONSIBILITIES
    - Design and develop scalable Python backend systems
    - Lead architecture decisions for new features
    - Mentor junior developers
    - Implement automated testing and code quality standards
    - Collaborate with frontend and DevOps teams
    - Participate in code reviews
    """


class TestKeywordExtraction:
    """Test keyword extraction functionality."""
    
    def test_extract_keywords_basic(self, analyzer, sample_resume):
        """Test basic keyword extraction."""
        keywords = analyzer.extract_top_keywords(sample_resume, top_n=10)
        
        assert len(keywords) > 0
        assert isinstance(keywords, list)
        assert isinstance(keywords[0], tuple)
        assert isinstance(keywords[0][0], str)  # keyword
        assert isinstance(keywords[0][1], int)  # frequency
    
    def test_extract_top_keywords(self, analyzer, sample_resume):
        """Test extracting top N keywords."""
        top_5 = analyzer.extract_top_keywords(sample_resume, top_n=5)
        top_20 = analyzer.extract_top_keywords(sample_resume, top_n=20)
        
        assert len(top_5) == 5
        assert len(top_20) == 20
        assert top_5[0] in top_20
    
    def test_stopwords_removed(self, analyzer):
        """Test that stopwords are properly removed."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = analyzer.extract_top_keywords(text)
        
        # Check that common stopwords are not in the keywords
        keyword_set = {kw for kw, _ in keywords}
        assert 'the' not in keyword_set
        assert 'a' not in keyword_set
        assert 'is' not in keyword_set
    
    def test_stopwords_comprehensive(self, analyzer):
        """Test comprehensive stopword filtering."""
        text = """
        The development team is working on the project. 
        They are using Python and Docker for the application.
        We have been implementing microservices and we will deploy to AWS.
        """
        keywords = analyzer.extract_top_keywords(text)
        keyword_set = {kw for kw, _ in keywords}
        
        # Verify stopwords are filtered
        for stopword in ['the', 'and', 'is', 'are', 'for', 'we', 'have', 'been', 'will']:
            assert stopword not in keyword_set
    
    def test_technical_terms_preserved(self, analyzer):
        """Test that technical terms are preserved."""
        text = "Python, JavaScript, React, Docker, Kubernetes, PostgreSQL, AWS"
        keywords = analyzer.extract_top_keywords(text)
        keyword_set = {kw for kw, _ in keywords}
        
        # Technical terms should be present
        assert 'python' in keyword_set
        assert 'javascript' in keyword_set
        assert 'docker' in keyword_set
    
    def test_numbers_filtered(self, analyzer):
        """Test that numeric values are filtered out."""
        text = "5 years experience, 2024, version 3.8"
        keywords = analyzer.extract_top_keywords(text)
        keyword_set = {kw for kw, _ in keywords}
        
        # Numbers should not be in keywords
        assert not any(kw.isdigit() for kw in keyword_set)


class TestJobDescriptionAnalysis:
    """Test job description analysis."""
    
    def test_analyze_job_description(self, analyzer, sample_job_description):
        """Test job description analysis."""
        analysis = analyzer.analyze_job_description(sample_job_description)
        
        assert 'top_keywords' in analysis
        assert 'total_keywords' in analysis
        assert 'keyword_frequency' in analysis
        assert len(analysis['top_keywords']) > 0
    
    def test_jd_keywords_extracted(self, analyzer, sample_job_description):
        """Test that key job requirements are extracted."""
        analysis = analyzer.analyze_job_description(sample_job_description)
        top_keywords = [kw for kw, _ in analysis['top_keywords']]
        
        # Check that job-specific keywords are present
        assert any(kw in top_keywords for kw in ['python', 'docker', 'kubernetes', 'aws'])
    
    def test_jd_top_n_limit(self, analyzer, sample_job_description):
        """Test top_n parameter for job description analysis."""
        analysis_10 = analyzer.analyze_job_description(sample_job_description, top_n=10)
        analysis_30 = analyzer.analyze_job_description(sample_job_description, top_n=30)
        
        assert len(analysis_10['top_keywords']) == 10
        assert len(analysis_30['top_keywords']) == 30


class TestResumeJDComparison:
    """Test resume vs job description comparison."""
    
    def test_compare_resume_to_jd(self, analyzer, sample_resume, sample_job_description):
        """Test basic resume vs JD comparison."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        assert 'match_score' in comparison
        assert 'matched_count' in comparison
        assert 'missing_count' in comparison
        assert 'keyword_coverage' in comparison
        assert 'jaccard_similarity' in comparison
        assert 'intersection_keywords' in comparison
        assert 'missing_keywords' in comparison
        assert 'top_resume_keywords' in comparison
        assert 'top_jd_keywords' in comparison
    
    def test_match_score_calculation(self, analyzer, sample_resume, sample_job_description):
        """Test match score is calculated correctly."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        assert 0.0 <= comparison['match_score'] <= 1.0
    
    def test_keyword_coverage_percentage(self, analyzer, sample_resume, sample_job_description):
        """Test keyword coverage percentage calculation."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        assert 0 <= comparison['keyword_coverage'] <= 100
        assert isinstance(comparison['keyword_coverage'], float)
    
    def test_jaccard_similarity(self, analyzer, sample_resume, sample_job_description):
        """Test Jaccard similarity calculation."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        assert 0.0 <= comparison['jaccard_similarity'] <= 1.0
        assert isinstance(comparison['jaccard_similarity'], float)
    
    def test_matched_keywords_contain_relevant_terms(self, analyzer, sample_resume, sample_job_description):
        """Test that matched keywords include expected technical skills."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        matched_keywords = comparison['intersection_keywords']
        
        # Expected matches between resume and JD
        assert len(matched_keywords) > 0
        assert any(kw in matched_keywords for kw in ['python', 'docker', 'kubernetes'])
    
    def test_missing_keywords_identified(self, analyzer, sample_resume, sample_job_description):
        """Test that missing keywords are identified."""
        comparison = analyzer.compare_resume_to_jd(sample_resume, sample_job_description)
        
        missing_keywords = comparison['missing_keywords']
        
        # Should have some missing keywords
        assert len(missing_keywords) > 0
        assert isinstance(missing_keywords, list)
    
    def test_comparison_same_text(self, analyzer):
        """Test comparison when resume and JD are identical."""
        text = "Python Django Docker Kubernetes AWS PostgreSQL"
        
        comparison = analyzer.compare_resume_to_jd(text, text)
        
        # Perfect match should have high scores
        assert comparison['match_score'] == 1.0
        assert comparison['jaccard_similarity'] == 1.0


class TestKeywordSimilarity:
    """Test keyword similarity detection."""
    
    def test_exact_match(self, analyzer):
        """Test exact keyword matching."""
        resume_text = "Python JavaScript Docker"
        jd_text = "Python JavaScript Docker"
        
        comparison = analyzer.compare_resume_to_jd(resume_text, jd_text)
        
        # All keywords should match
        assert comparison['matched_count'] > 0
    
    def test_partial_match_variations(self, analyzer):
        """Test detection of keyword variations."""
        resume_text = "Using Python, JavaScript, and React framework"
        jd_text = "Python developer proficient in JavaScript and ReactJS"
        
        comparison = analyzer.compare_resume_to_jd(resume_text, jd_text)
        
        # Should detect similar keywords despite variations
        assert len(comparison['intersection_keywords']) > 0
    
    def test_keyword_case_insensitive(self, analyzer):
        """Test that keyword matching is case-insensitive."""
        resume_text = "Python PYTHON python"
        jd_text = "python"
        
        keywords_resume = analyzer._extract_keywords(resume_text)
        keywords_jd = analyzer._extract_keywords(jd_text)
        
        # Should be treated as same keyword
        assert 'python' in keywords_resume
        assert 'python' in keywords_jd


class TestAnalyzeResume:
    """Test analyze_resume method."""
    
    def test_analyze_without_jd(self, analyzer, sample_resume):
        """Test analyzing resume without job description."""
        analysis = analyzer.analyze_resume(sample_resume)
        
        assert analysis.total_keywords > 0
        assert len(analysis.matched_keywords) > 0
        assert analysis.match_score == 1.0  # Single resume analysis gives perfect score
    
    def test_analyze_with_jd(self, analyzer, sample_resume, sample_job_description):
        """Test analyzing resume with job description."""
        analysis = analyzer.analyze_resume(sample_resume, sample_job_description)
        
        assert analysis.total_keywords > 0
        assert len(analysis.matched_keywords) >= 0
        assert 0 <= analysis.match_score <= 1.0
        assert len(analysis.recommendations) > 0
    
    def test_recommendations_generated(self, analyzer, sample_resume, sample_job_description):
        """Test that recommendations are generated."""
        analysis = analyzer.analyze_resume(sample_resume, sample_job_description)
        
        assert len(analysis.recommendations) > 0
        assert isinstance(analysis.recommendations, list)
        assert all(isinstance(r, str) for r in analysis.recommendations)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text_extraction(self, analyzer):
        """Test keyword extraction from empty text."""
        keywords = analyzer.extract_top_keywords("")
        
        assert len(keywords) == 0
    
    def test_single_word_extraction(self, analyzer):
        """Test extraction from single word."""
        keywords = analyzer.extract_top_keywords("Python")
        
        assert len(keywords) > 0
        assert keywords[0][0] == 'python'
    
    def test_special_characters(self, analyzer):
        """Test handling of special characters."""
        text = "C++ C# Node.js Ruby@Rails"
        keywords = analyzer.extract_top_keywords(text)
        keyword_set = {kw for kw, _ in keywords}
        
        # Technical terms with special chars should be handled
        assert any(kw in keyword_set for kw in ['c++', 'c#', 'node.js', 'rails'])
    
    def test_unicode_text(self, analyzer):
        """Test handling of unicode text."""
        text = "Developer with Python and JavaScript skills 开发者"
        keywords = analyzer.extract_top_keywords(text)
        
        assert len(keywords) > 0
        assert any(kw in {kw for kw, _ in keywords} for kw in ['developer', 'python', 'javascript'])
