"""Pydantic schemas for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ResumeAnalysisRequest(BaseModel):
    """Request schema for resume analysis."""
    resume_text: str = Field(..., description="The resume text to analyze")
    job_description: Optional[str] = Field(None, description="Optional job description for matching")


class KeywordMatch(BaseModel):
    """Schema for a single keyword match."""
    model_config = ConfigDict(json_schema_extra={"example": {"keyword": "Python", "frequency": 5, "relevance_score": 0.85}})

    keyword: str
    frequency: int
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class KeywordSuggestion(BaseModel):
    """Schema for keyword synonym suggestions."""
    keyword: str
    suggestions: List[str] = Field(default_factory=list, description="List of synonym suggestions")


class ResumeAnalysis(BaseModel):
    """Response schema for resume analysis."""
    total_keywords: int
    matched_keywords: List[KeywordMatch]
    missing_keywords: List[str] = Field(default_factory=list)
    suggestions: dict = Field(default_factory=dict, description="Synonym suggestions for missing keywords (keyword -> list of synonyms)")
    match_score: float = Field(..., ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    """Schema for parsed resume data."""
    text: str
    sections: dict = Field(default_factory=dict)
    contact_info: Optional[dict] = None
    experience: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)


class JobDescriptionAnalysis(BaseModel):
    """Schema for job description analysis."""
    key_skills: List[str]
    key_responsibilities: List[str]
    required_keywords: List[str]
    nice_to_have_keywords: List[str]


class KeywordExtractResponse(BaseModel):
    """Response schema for keyword extraction endpoint."""
    top_keywords: List[Dict[str, Any]] = Field(
        ...,
        description="List of extracted keywords with their frequencies"
    )
    total_unique_keywords: int = Field(
        ...,
        description="Total count of unique keywords found"
    )


class JobDescriptionAnalysisResponse(BaseModel):
    """Response schema for job description analysis endpoint."""
    top_keywords: List[Dict[str, Any]] = Field(
        ...,
        description="List of top keywords from job description"
    )
    total_unique_keywords: int = Field(
        ...,
        description="Total unique keywords in job description"
    )
    keyword_frequency: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequency map of all extracted keywords"
    )


class ComparisonMetrics(BaseModel):
    """Schema for resume-to-JD comparison metrics."""
    match_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score")
    matched_count: int = Field(..., description="Number of matched keywords")
    total_jd_keywords: int = Field(..., description="Total unique keywords in job description")
    missing_count: int = Field(..., description="Number of missing keywords from resume")
    keyword_coverage_percentage: float = Field(
        ...,
        description="Percentage of job description keywords covered by resume"
    )
    jaccard_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Jaccard similarity score between resume and JD keywords"
    )
    top_resume_keywords: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top keywords from resume"
    )
    top_jd_keywords: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top keywords from job description"
    )
    matched_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords present in both resume and job description"
    )
    missing_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords from job description not found in resume"
    )
