"""FastAPI application entry point for Resume Keyword Optimizer."""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from app.schemas import (
    ResumeAnalysisRequest, 
    ResumeAnalysis,
    KeywordExtractResponse,
    JobDescriptionAnalysisResponse,
    ComparisonMetrics,
    FetchJobDescriptionRequest,
    FetchJobDescriptionResponse
)
from app.parser import ResumeParser
from app.analyzer import KeywordAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
SUPPORTED_FILE_FORMATS = ('.txt', '.pdf', '.docx')
DEFAULT_TOP_N_KEYWORDS = 20
DEFAULT_JD_TOP_N = 30

# Initialize FastAPI app
app = FastAPI(
    title="Resume Keyword Optimizer API",
    description="API for optimizing resumes with keyword analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
resume_parser = ResumeParser()
keyword_analyzer = KeywordAnalyzer()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API is running."""
    return {
        "message": "Resume Keyword Optimizer API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze", response_model=ResumeAnalysis, tags=["Analysis"])
async def analyze_resume(request: ResumeAnalysisRequest) -> ResumeAnalysis:
    """
    Analyze a resume and optionally match against a job description.
    
    Args:
        request: ResumeAnalysisRequest containing resume text and optional job description
        
    Returns:
        ResumeAnalysis: Analysis results with keyword matching and recommendations
        
    Raises:
        HTTPException: If resume text is empty
    """
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        
        logger.info("Analyzing resume")
        
        # Analyze the resume
        analysis = keyword_analyzer.analyze_resume(
            request.resume_text,
            request.job_description
        )
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse", tags=["Parsing"])
async def parse_resume(request: ResumeAnalysisRequest):
    """
    Parse a resume and extract structured information.
    
    Args:
        request: ResumeAnalysisRequest containing resume text
        
    Returns:
        ParsedResume: Structured resume data
        
    Raises:
        HTTPException: If resume text is empty
    """
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        
        logger.info("Parsing resume")
        
        # Parse the resume
        parsed = resume_parser.parse(request.resume_text)
        
        return parsed
    
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", tags=["File Upload"])
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and process a resume file.
    
    Supported formats: .txt, .pdf, .docx
    Maximum file size: 5MB
    
    Args:
        file: Resume file to upload
        
    Returns:
        Parsed resume data with sections, contact info, skills, experience, and education
        
    Raises:
        HTTPException: If file type is not supported or file is too large
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        if not file.filename.endswith(SUPPORTED_FILE_FORMATS):
            raise HTTPException(
                status_code=400,
                detail=f"Only {', '.join(SUPPORTED_FILE_FORMATS)} files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of 5MB"
            )
        
        # Handle text file decoding
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            # Try alternative encoding if UTF-8 fails
            try:
                text_content = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="File must be valid UTF-8 or Latin-1 encoded text"
                )
        
        # Parse the resume
        parsed = resume_parser.parse(text_content)
        
        return parsed
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keywords/extract", response_model=KeywordExtractResponse, tags=["Keywords"])
async def extract_keywords(request: ResumeAnalysisRequest) -> KeywordExtractResponse:
    """
    Extract top keywords from text (resume or job description).
    
    Args:
        request: ResumeAnalysisRequest with resume_text containing the text to analyze
        
    Returns:
        KeywordExtractResponse with top keywords and their frequencies
        
    Raises:
        HTTPException: If text is empty
    """
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        logger.info("Extracting keywords from text")
        
        top_keywords = keyword_analyzer.extract_top_keywords(request.resume_text, top_n=DEFAULT_TOP_N_KEYWORDS)
        
        return KeywordExtractResponse(
            top_keywords=[{"keyword": kw, "frequency": freq} for kw, freq in top_keywords],
            total_unique_keywords=len(top_keywords)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keywords/analyze-jd", response_model=JobDescriptionAnalysisResponse, tags=["Keywords"])
async def analyze_job_description(request: ResumeAnalysisRequest) -> JobDescriptionAnalysisResponse:
    """
    Analyze a job description to extract key requirements.
    
    Args:
        request: ResumeAnalysisRequest with resume_text containing the job description
        
    Returns:
        JobDescriptionAnalysisResponse with top keywords and analysis
        
    Raises:
        HTTPException: If job description is empty
    """
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        logger.info("Analyzing job description")
        
        analysis = keyword_analyzer.analyze_job_description(request.resume_text, top_n=DEFAULT_JD_TOP_N)
        
        return JobDescriptionAnalysisResponse(
            top_keywords=[{"keyword": kw, "frequency": freq} for kw, freq in analysis["top_keywords"]],
            total_unique_keywords=analysis["total_keywords"],
            keyword_frequency=analysis["keyword_frequency"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare", response_model=ComparisonMetrics, tags=["Comparison"])
async def compare_resume_to_jd(request: ResumeAnalysisRequest) -> ComparisonMetrics:
    """
    Perform detailed comparison between resume and job description.
    
    Analyzes keyword matching, coverage, and provides similarity metrics.
    
    Args:
        request: ResumeAnalysisRequest with both resume_text and job_description
        
    Returns:
        ComparisonMetrics with detailed comparison including:
        - Match score (0-1 scale)
        - Matched keywords
        - Missing keywords
        - Keyword coverage percentage
        - Jaccard similarity score
        
    Raises:
        HTTPException: If either resume or job description is empty
    """
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        if not request.job_description or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        logger.info("Comparing resume to job description")
        
        comparison = keyword_analyzer.compare_resume_to_jd(
            request.resume_text,
            request.job_description
        )
        
        return ComparisonMetrics(
            match_score=comparison["match_score"],
            matched_count=comparison["matched_count"],
            total_jd_keywords=comparison["total_jd_keywords"],
            missing_count=comparison["missing_count"],
            keyword_coverage_percentage=comparison["keyword_coverage"],
            jaccard_similarity=comparison["jaccard_similarity"],
            top_resume_keywords=[{"keyword": kw, "frequency": freq} for kw, freq in comparison["top_resume_keywords"]],
            top_jd_keywords=[{"keyword": kw, "frequency": freq} for kw, freq in comparison["top_jd_keywords"]],
            matched_keywords=comparison["intersection_keywords"],
            missing_keywords=comparison["missing_keywords"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing resume to job description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-job-description", response_model=FetchJobDescriptionResponse, tags=["Job Description"])
async def fetch_job_description(request: FetchJobDescriptionRequest) -> FetchJobDescriptionResponse:
    """
    Fetch and extract job description text from a given URL.
    
    Uses BeautifulSoup to parse the webpage and extract visible text.
    Filters out script, style, and navigation elements for clean content.
    
    Args:
        request: FetchJobDescriptionRequest containing the URL to fetch
        
    Returns:
        FetchJobDescriptionResponse with extracted job description text and page title
        
    Raises:
        HTTPException: If URL is invalid or request fails
    """
    try:
        url = request.url.strip()
        
        # Validate URL format
        if not url:
            raise HTTPException(status_code=400, detail="URL cannot be empty")
        
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = "https://" + url
        if not parsed_url.netloc and not urlparse(url).netloc:
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        logger.info(f"Fetching job description from URL: {url}")
        
        # Fetch the webpage
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="Request timeout: The URL took too long to respond")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Connection error: Unable to reach the URL")
        except requests.exceptions.HTTPError as e:
            raise HTTPException(status_code=response.status_code, detail=f"HTTP error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Request error: {str(e)}")
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract page title
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.find("h1"):
            title = soup.find("h1").get_text()
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text: remove extra whitespace and newlines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        job_description = "\n".join(chunk for chunk in chunks if chunk)
        
        if not job_description or len(job_description.strip()) == 0:
            raise HTTPException(status_code=400, detail="No text content found on the webpage")
        
        return FetchJobDescriptionResponse(
            url=request.url,
            job_description=job_description,
            title=title,
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
