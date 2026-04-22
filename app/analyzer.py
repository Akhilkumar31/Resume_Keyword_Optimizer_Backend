"""Keyword analysis module for resume optimization."""

import re
from typing import List, Dict, Tuple
from collections import Counter
from app.schemas import KeywordMatch, ResumeAnalysis


class KeywordAnalyzer:
    """Analyzes keywords in resumes and job descriptions."""
    
    def __init__(self):
        """Initialize the keyword analyzer."""
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'is', 'has', 'have', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
    
    def analyze_resume(
        self,
        resume_text: str,
        job_description: str = None
    ) -> ResumeAnalysis:
        """
        Analyze resume and optionally match against job description.
        
        Args:
            resume_text: The resume text to analyze
            job_description: Optional job description for matching
            
        Returns:
            ResumeAnalysis: Analysis results with matched and missing keywords
        """
        # Extract keywords from resume
        resume_keywords = self._extract_keywords(resume_text)
        
        matched_keywords = []
        missing_keywords = []
        match_score = 0.0
        recommendations = []
        
        if job_description:
            job_keywords = self._extract_keywords(job_description)
            
            # Find matches
            matched_keywords = self._find_matching_keywords(resume_keywords, job_keywords)
            
            # Find missing keywords
            missing_keywords = self._find_missing_keywords(resume_keywords, job_keywords)
            
            # Calculate match score
            match_score = self._calculate_match_score(
                len(matched_keywords),
                len(job_keywords)
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                matched_keywords,
                missing_keywords,
                match_score
            )
        else:
            # If no job description, analyze resume keywords
            matched_keywords = [
                KeywordMatch(
                    keyword=keyword,
                    frequency=count,
                    relevance_score=min(count / 10, 1.0)
                )
                for keyword, count in resume_keywords.most_common(20)
            ]
            match_score = 1.0
        
        return ResumeAnalysis(
            total_keywords=len(resume_keywords),
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            match_score=match_score,
            recommendations=recommendations
        )
    
    def _extract_keywords(self, text: str) -> Counter:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Counter: Count of extracted keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and split into words
        words = re.findall(r'\b[a-z]+(?:[+-][a-z]+)*\b', text)
        
        # Filter out stop words and short words
        keywords = [
            word for word in words
            if word not in self.stop_words and len(word) > 2
        ]
        
        return Counter(keywords)
    
    def _find_matching_keywords(
        self,
        resume_keywords: Counter,
        job_keywords: Counter
    ) -> List[KeywordMatch]:
        """Find keywords that match between resume and job description."""
        matched = []
        
        for keyword in job_keywords:
            if keyword in resume_keywords:
                relevance_score = min(resume_keywords[keyword] / 5, 1.0)
                matched.append(KeywordMatch(
                    keyword=keyword,
                    frequency=resume_keywords[keyword],
                    relevance_score=relevance_score
                ))
        
        # Sort by relevance score descending
        matched.sort(key=lambda x: x.relevance_score, reverse=True)
        return matched
    
    def _find_missing_keywords(
        self,
        resume_keywords: Counter,
        job_keywords: Counter
    ) -> List[str]:
        """Find keywords in job description that are missing from resume."""
        missing = []
        
        for keyword in job_keywords:
            if keyword not in resume_keywords:
                missing.append(keyword)
        
        return missing[:10]  # Return top 10 missing keywords
    
    def _calculate_match_score(
        self,
        matched_count: int,
        total_job_keywords: int
    ) -> float:
        """Calculate the match score between resume and job description."""
        if total_job_keywords == 0:
            return 0.0
        
        score = min(matched_count / total_job_keywords, 1.0)
        return round(score, 2)
    
    def _generate_recommendations(
        self,
        matched_keywords: List[KeywordMatch],
        missing_keywords: List[str],
        match_score: float
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if match_score < 0.3:
            recommendations.append(
                "Low match score. Consider adding more relevant keywords from the job description."
            )
        elif match_score < 0.6:
            recommendations.append(
                "Moderate match. Try to incorporate more job-specific keywords."
            )
        else:
            recommendations.append(
                "Good match! Your resume covers most required keywords."
            )
        
        if missing_keywords:
            top_missing = ', '.join(missing_keywords[:5])
            recommendations.append(
                f"Consider adding these keywords: {top_missing}"
            )
        
        return recommendations
