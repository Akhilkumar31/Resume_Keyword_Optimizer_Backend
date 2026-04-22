"""FastAPI application entry point for Resume Keyword Optimizer."""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.schemas import ResumeAnalysisRequest, ResumeAnalysis
from app.parser import ResumeParser
from app.analyzer import KeywordAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    Args:
        file: Resume file to upload (txt or pdf support planned)
        
    Returns:
        Parsed resume data
        
    Raises:
        HTTPException: If file type is not supported
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type (currently only text files)
        if not file.filename.endswith(('.txt', '.pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt and .pdf files are supported"
            )
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Parse the resume
        parsed = resume_parser.parse(text_content)
        
        return parsed
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid text/UTF-8 encoded")
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
