"""Keyword analysis module for resume optimization."""

import re
from typing import List, Dict, Tuple, Set
from collections import Counter
from app.schemas import KeywordMatch, ResumeAnalysis


class KeywordAnalyzer:
    """Analyzes keywords in resumes and job descriptions."""
    
    def __init__(self):
        """Initialize the keyword analyzer with comprehensive stopwords."""
        # Comprehensive set of stop words to filter out
        self.stop_words = {
            # Articles and prepositions
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'while', 'so', 'because', 'now',
            # Verbs
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'has', 'have', 'had', 'having',
            'do', 'does', 'did', 'doing',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
            'shall', 'seem', 'seemed', 'seems',
            # Pronouns
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'him', 'her',
            'me', 'us', 'myself', 'yourself', 'himself', 'herself', 'itself',
            'ourselves', 'yourselves', 'themselves',
            'this', 'that', 'these', 'those',
            'what', 'which', 'who', 'whom', 'whose',
            # Common words
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'same', 'so', 'than', 'too', 'very',
            'just', 'also', 'too', 'first', 'last', 'many', 'much', 'any', 'another',
            # Additional common words in job descriptions
            'job', 'position', 'role', 'work', 'team', 'company', 'organization',
            'including', 'ability', 'experience', 'required', 'preferred', 'must',
            'should', 'will', 'can', 'we', 'our', 'you', 'your', 'about', 'would',
            'help', 'make', 'provide', 'ensure', 'support', 'manage', 'perform',
            'day', 'time', 'use', 'part', 'area', 'level'
        }
    
    def extract_top_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Extract top keywords from text.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of tuples (keyword, frequency)
        """
        keywords = self._extract_keywords(text)
        return keywords.most_common(top_n)
    
    def analyze_job_description(self, job_description: str, top_n: int = 30) -> Dict:
        """
        Analyze job description to extract key information.
        
        Args:
            job_description: The job description text
            top_n: Number of top keywords to extract
            
        Returns:
            Dictionary with analysis results
        """
        top_keywords = self.extract_top_keywords(job_description, top_n)
        
        return {
            'top_keywords': top_keywords,
            'total_keywords': len(set(self._extract_keywords(job_description))),
            'keyword_frequency': dict(top_keywords)
        }
    
    def compare_resume_to_jd(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict:
        """
        Perform detailed comparison between resume and job description.
        
        Args:
            resume_text: The resume text
            job_description: The job description text
            
        Returns:
            Dictionary with detailed comparison metrics
        """
        resume_keywords = self._extract_keywords(resume_text)
        job_keywords = self._extract_keywords(job_description)
        
        # Find matches and missing keywords
        matched_keywords = self._find_matching_keywords(resume_keywords, job_keywords)
        missing_keywords = self._find_missing_keywords(resume_keywords, job_keywords)
        
        # Calculate metrics
        match_score = self._calculate_match_score(len(matched_keywords), len(job_keywords))
        
        # Get top keywords from both
        top_resume_keywords = resume_keywords.most_common(15)
        top_jd_keywords = job_keywords.most_common(15)
        
        # Calculate keyword intersection and union
        resume_keyword_set = set(resume_keywords.keys())
        jd_keyword_set = set(job_keywords.keys())
        
        intersection = resume_keyword_set & jd_keyword_set
        union = resume_keyword_set | jd_keyword_set
        jaccard_similarity = len(intersection) / len(union) if union else 0
        
        return {
            'match_score': match_score,
            'matched_count': len(matched_keywords),
            'total_jd_keywords': len(job_keywords),
            'missing_count': len(missing_keywords),
            'intersection_keywords': sorted(list(intersection)),
            'missing_keywords': missing_keywords,
            'top_resume_keywords': top_resume_keywords,
            'top_jd_keywords': top_jd_keywords,
            'jaccard_similarity': round(jaccard_similarity, 2),
            'keyword_coverage': round(len(matched_keywords) / max(len(job_keywords), 1) * 100, 2)
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
        Extract keywords from text with intelligent stopword removal.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Counter: Count of extracted keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Extract single words and multi-word technical terms
        # This regex captures words, hyphens, slashes, and plus signs (for C++, C#, etc.)
        words = re.findall(r'\b[a-z][a-z0-9]*(?:[+#/.-][a-z0-9]+)*\b', text)
        
        # Filter out stop words and very short words
        keywords = [
            word for word in words
            if word not in self.stop_words and len(word) > 2 and not self._is_number(word)
        ]
        
        return Counter(keywords)
    
    def _is_number(self, word: str) -> bool:
        """Check if word is purely numeric."""
        try:
            float(word)
            return True
        except ValueError:
            return False
    
    def _find_matching_keywords(
        self,
        resume_keywords: Counter,
        job_keywords: Counter
    ) -> List[KeywordMatch]:
        """
        Find keywords that match between resume and job description.
        Includes exact and partial matches.
        """
        matched = []
        
        for keyword in job_keywords:
            if keyword in resume_keywords:
                # Exact match
                relevance_score = min(resume_keywords[keyword] / 5, 1.0)
                matched.append(KeywordMatch(
                    keyword=keyword,
                    frequency=resume_keywords[keyword],
                    relevance_score=relevance_score
                ))
            else:
                # Check for partial/similar matches
                for resume_keyword in resume_keywords:
                    if self._keywords_similar(keyword, resume_keyword):
                        relevance_score = min(resume_keywords[resume_keyword] / 5, 0.8)
                        matched.append(KeywordMatch(
                            keyword=keyword,
                            frequency=resume_keywords[resume_keyword],
                            relevance_score=relevance_score
                        ))
                        break
        
        # Remove duplicates and sort by relevance score descending
        seen = set()
        unique_matched = []
        for match in matched:
            if match.keyword not in seen:
                unique_matched.append(match)
                seen.add(match.keyword)
        
        unique_matched.sort(key=lambda x: x.relevance_score, reverse=True)
        return unique_matched
    
    def _keywords_similar(self, kw1: str, kw2: str) -> bool:
        """
        Check if two keywords are similar (e.g., singular/plural or variations).
        
        Args:
            kw1: First keyword
            kw2: Second keyword
            
        Returns:
            Boolean indicating similarity
        """
        # Check for substring containment (e.g., 'java' in 'javascript')
        if len(kw1) > 4 and len(kw2) > 4:
            if kw1 in kw2 or kw2 in kw1:
                return True
        
        # Check for common variations
        variations = {
            'python': ['py'],
            'javascript': ['js', 'node'],
            'typescript': ['ts'],
            'react': ['reactjs'],
            'vue': ['vuejs'],
            'angular': ['ng'],
            'database': ['db', 'sql'],
            'management': ['manage'],
            'developer': ['development'],
            'engineer': ['engineering'],
            'admin': ['administrator'],
            'config': ['configure', 'configuration']
        }
        
        for main, alts in variations.items():
            if (kw1 == main and kw2 in alts) or (kw2 == main and kw1 in alts):
                return True
        
        return False
    
    def _find_missing_keywords(
        self,
        resume_keywords: Counter,
        job_keywords: Counter
    ) -> List[str]:
        """
        Find keywords in job description that are missing from resume.
        Returns keywords ranked by frequency in job description.
        """
        missing = []
        
        for keyword, frequency in job_keywords.most_common():
            if keyword not in resume_keywords:
                # Check for partial matches too
                has_similar = any(
                    self._keywords_similar(keyword, rk) 
                    for rk in resume_keywords.keys()
                )
                if not has_similar:
                    missing.append(keyword)
        
        return missing[:15]  # Return top 15 missing keywords
    
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
