"""Pydantic schemas for request/response validation."""

from typing import List, Optional
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
