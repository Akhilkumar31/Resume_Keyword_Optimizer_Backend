"""Keyword analysis module for resume optimization."""

import re
from typing import List, Dict, Tuple, Set
from collections import Counter
from app.schemas import KeywordMatch, ResumeAnalysis, KeywordSuggestion

# Constants for keyword analysis
MIN_KEYWORD_LENGTH = 3
RELEVANCE_SCORE_DIVISOR = 5  # Used to normalize frequency to 0-1 score
DEFAULT_TOP_N_KEYWORDS = 20
DEFAULT_MISSING_KEYWORDS_LIMIT = 15
SIMILARITY_CHECK_MIN_LENGTH = 4
PARTIAL_MATCH_SCORE = 0.8

# Technical keyword weights for improved scoring
TECHNICAL_KEYWORDS = {
    'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
    'node', 'nodejs', 'java', 'c++', 'c#', '.net', 'csharp',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra',
    'docker', 'kubernetes', 'k8s', 'aws', 'azure', 'gcp',
    'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops',
    'fastapi', 'django', 'flask', 'spring', 'springboot',
    'html', 'css', 'sass', 'scss', 'graphql', 'rest', 'api',
    'machine learning', 'ml', 'ai', 'tensorflow', 'pytorch',
    'data science', 'analytics', 'linux', 'unix', 'windows',
    'microservices', 'linux', 'aws', 'azure', 'gcp', 'firebase'
}
TECHNICAL_KEYWORD_WEIGHT = 2.0  # Technical keywords count twice
NORMAL_KEYWORD_WEIGHT = 1.0     # Normal keywords count once


class KeywordAnalyzer:
    """Analyzes keywords in resumes and job descriptions."""
    
    def __init__(self):
        """Initialize the keyword analyzer with comprehensive stopwords and synonym dictionary."""
        # Synonym dictionary mapping keywords to their common synonyms/alternatives
        self.synonym_dictionary = {
            'javascript': ['js', 'ecmascript', 'node.js', 'nodejs'],
            'python': ['py', 'python3'],
            'typescript': ['ts'],
            'react': ['reactjs', 'react.js'],
            'vue': ['vuejs', 'vue.js'],
            'angular': ['ng', 'angular.js'],
            'node': ['nodejs', 'node.js'],
            'database': ['db', 'sql', 'nosql'],
            'sql': ['mysql', 'postgresql', 'mssql'],
            'nosql': ['mongodb', 'redis', 'cassandra'],
            'docker': ['containerization', 'containers'],
            'kubernetes': ['k8s'],
            'aws': ['amazon', 'amazon web services'],
            'gcp': ['google cloud', 'google cloud platform'],
            'azure': ['microsoft azure'],
            'git': ['github', 'gitlab', 'bitbucket', 'version control'],
            'rest': ['restful', 'api'],
            'graphql': ['graph ql'],
            'django': ['django rest framework'],
            'flask': ['flask framework'],
            'spring': ['spring boot', 'spring framework'],
            'junit': ['testing', 'unit testing'],
            'pytest': ['testing', 'unit testing'],
            'jest': ['testing', 'javascript testing'],
            'ci/cd': ['continuous integration', 'continuous deployment', 'devops'],
            'devops': ['ci/cd', 'deployment'],
            'agile': ['scrum', 'kanban'],
            'scrum': ['agile', 'sprint'],
            'management': ['manage', 'leading'],
            'leadership': ['leading', 'management'],
            'communication': ['collaborate', 'collaboration', 'teamwork'],
            'problem solving': ['analytical', 'troubleshooting'],
            'html': ['markup', 'web development'],
            'css': ['styling', 'sass', 'scss'],
            'sass': ['css', 'scss', 'styling'],
            'react native': ['mobile development', 'react'],
            'swift': ['ios', 'ios development'],
            'kotlin': ['android', 'android development'],
            'java': ['j2ee', 'enterprise java'],
            'c++': ['cpp', 'c plus plus'],
            'c#': ['csharp', 'c sharp'],
            '.net': ['dotnet', 'microsoft dot net'],
            'linux': ['unix', 'ubuntu'],
            'windows': ['microsoft windows'],
            'macos': ['mac', 'osx'],
            'api': ['rest', 'graphql', 'integration'],
            'microservices': ['service oriented', 'distributed systems'],
            'machine learning': ['ml', 'ai', 'artificial intelligence'],
            'ai': ['artificial intelligence', 'machine learning'],
            'tensorflow': ['keras', 'deep learning'],
            'pytorch': ['deep learning', 'neural networks'],
            'data science': ['analytics', 'data analytics'],
            'analytics': ['data analysis', 'business intelligence'],
            'excel': ['spreadsheet', 'data management'],
            'tableau': ['visualization', 'business intelligence'],
            'power bi': ['visualization', 'business intelligence'],
            'jira': ['project management', 'issue tracking'],
            'confluence': ['documentation', 'wiki'],
            'slack': ['communication', 'messaging'],
            'jenkins': ['ci/cd', 'automation'],
            'gitlab': ['git', 'version control', 'ci/cd'],
            'github': ['git', 'version control'],
        }
        
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
            'day', 'time', 'use', 'part', 'area', 'level',
            # Generic qualifier words that dilute phrase quality
            'skills', 'knowledge', 'proficiency', 'candidate', 'need', 'needs',
            'requirements', 'understanding', 'background', 'expertise', 'strong',
            'good', 'great', 'excellent', 'hands', 'solid', 'proven', 'plus'
        }
    
    def extract_top_keywords(self, text: str, top_n: int = DEFAULT_TOP_N_KEYWORDS) -> List[Tuple[str, int]]:
        """
        Extract top N most frequent meaningful keywords from text.
        
        Requirements met:
        - Normalizes text (lowercase, removes special characters)
        - Removes stopwords from text
        - Tokenizes words properly using regex patterns
        - Counts word frequency using collections.Counter
        - Ignores very short words (length < 3)
        - Returns keywords sorted by importance (frequency)
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return (default: 20)
            
        Returns:
            List[Tuple[str, int]]: List of (keyword, frequency) tuples sorted by frequency descending
        """
        keywords = self._extract_keywords(text)
        # Counter.most_common() returns list sorted by frequency (importance)
        return keywords.most_common(top_n)
    
    def analyze_job_description(self, job_description: str, top_n: int = DEFAULT_TOP_N_KEYWORDS) -> Dict:
        """
        Analyze job description to extract key information.
        
        Uses improved keyword extraction that:
        - Normalizes and cleans text
        - Removes stopwords
        - Handles technical terms and special characters
        - Counts frequencies with collections.Counter
        - Returns top keywords sorted by frequency (importance)
        
        Args:
            job_description: The job description text
            top_n: Number of top keywords to extract (default: 30)
            
        Returns:
            Dictionary with:
            - top_keywords: List of (keyword, frequency) tuples sorted by importance
            - total_keywords: Total count of unique keywords found
            - keyword_frequency: Dict mapping keywords to their frequencies
        """
        top_keywords = self.extract_top_keywords(job_description, top_n)
        keywords_counter = self._extract_keywords(job_description)
        
        return {
            'top_keywords': top_keywords,
            'total_keywords': len(keywords_counter),
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
        
        # Calculate metrics using improved scoring
        match_score = self._calculate_match_score(matched_keywords, job_keywords)
        
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
        suggestions = {}
        match_score = 0.0
        recommendations = []
        
        if job_description:
            job_keywords = self._extract_keywords(job_description)
            
            # Find matches
            matched_keywords = self._find_matching_keywords(resume_keywords, job_keywords)
            
            # Find missing keywords
            missing_keywords = self._find_missing_keywords(resume_keywords, job_keywords)

            # --- Phrase matching ---
            jd_phrases = self._extract_phrases(job_description)
            matched_phrases, missing_phrases = self._match_phrases(resume_text, jd_phrases)
            matched_keywords = matched_keywords + matched_phrases
            missing_keywords = missing_keywords + missing_phrases
            # ----------------------
            
            # Generate suggestions for missing keywords
            suggestions = self._get_suggestions_for_keywords(missing_keywords)
            
            # Calculate match score using improved scoring logic
            match_score = self._calculate_match_score(matched_keywords, job_keywords, jd_phrases)
            
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
            match_score = 100.0
        
        return ResumeAnalysis(
            total_keywords=len(resume_keywords),
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
            match_score=match_score,
            recommendations=recommendations
        )
    
    def _extract_keywords(self, text: str) -> Counter:
        """
        Extract keywords from text with intelligent stopword removal.
        
        Performs the following steps:
        1. Normalizes text (lowercase, removes special characters)
        2. Tokenizes words properly using regex
        3. Filters stopwords and very short words (length < 3)
        4. Removes numeric-only tokens
        5. Counts word frequencies using collections.Counter
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Counter: Count of extracted keywords sorted by frequency
        """
        # Step 1: Normalize text - convert to lowercase
        text = text.lower()
        
        # Step 2: Remove special characters while preserving meaningful ones for technical terms
        # Keep hyphens, forward slashes, and plus signs for terms like C++, C#, .NET, etc.
        # Remove other punctuation like commas, periods, parentheses, etc.
        text = re.sub(r'[^\w\s+#./\-]', ' ', text)
        
        # Step 3: Tokenize words properly
        # This regex pattern captures:
        # - Words with alphanumeric characters
        # - Special sequences like C++, C#, .NET, Python-3, etc.
        # - Words starting with a letter followed by any alphanumeric chars and optional special chars
        words = re.findall(r'\b[a-z][a-z0-9]*(?:[+#/.-][a-z0-9]+)*\b', text)
        
        # Step 4: Filter keywords by multiple criteria
        keywords = []
        for word in words:
            # Criteria for filtering:
            # 1. Must not be a stopword
            # 2. Must have length >= 3 (ignore very short words)
            # 3. Must not be purely numeric
            if (word not in self.stop_words and 
                len(word) >= MIN_KEYWORD_LENGTH and 
                not self._is_number(word)):
                keywords.append(word)
        
        # Step 5: Count word frequencies and return sorted by importance
        return Counter(keywords)
    
    def _is_number(self, word: str) -> bool:
        """Check if word is purely numeric."""
        try:
            float(word)
            return True
        except ValueError:
            return False
    
    def _get_keyword_weight(self, keyword: str) -> float:
        """
        Determine the weight of a keyword based on whether it's technical.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            float: Weight factor (2.0 for technical, 1.0 for normal)
        """
        keyword_lower = keyword.lower()
        
        # Check if keyword is in technical keywords set
        if keyword_lower in TECHNICAL_KEYWORDS:
            return TECHNICAL_KEYWORD_WEIGHT
        
        # Check for partial matches (e.g., "python3" contains "python")
        for tech_keyword in TECHNICAL_KEYWORDS:
            if tech_keyword in keyword_lower or keyword_lower in tech_keyword:
                return TECHNICAL_KEYWORD_WEIGHT
        
        return NORMAL_KEYWORD_WEIGHT
    
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
                relevance_score = min(resume_keywords[keyword] / RELEVANCE_SCORE_DIVISOR, 1.0)
                matched.append(KeywordMatch(
                    keyword=keyword,
                    frequency=resume_keywords[keyword],
                    relevance_score=relevance_score
                ))
            else:
                # Check for partial/similar matches
                for resume_keyword in resume_keywords:
                    if self._keywords_similar(keyword, resume_keyword):
                        relevance_score = min(resume_keywords[resume_keyword] / RELEVANCE_SCORE_DIVISOR, PARTIAL_MATCH_SCORE)
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
    
    def _keywords_similar(self, first_keyword: str, second_keyword: str) -> bool:
        """
        Check if two keywords are similar (e.g., singular/plural or variations).
        
        Matches keywords using:
        - Substring containment (e.g., 'java' in 'javascript')
        - Common variations from predefined mapping
        
        Args:
            first_keyword: First keyword to compare
            second_keyword: Second keyword to compare
            
        Returns:
            Boolean indicating if keywords are similar
        """
        # Check for substring containment (e.g., 'java' in 'javascript')
        # Only for reasonably long keywords to avoid false positives
        if len(first_keyword) > SIMILARITY_CHECK_MIN_LENGTH and len(second_keyword) > SIMILARITY_CHECK_MIN_LENGTH:
            if first_keyword in second_keyword or second_keyword in first_keyword:
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
            if (first_keyword == main and second_keyword in alts) or (second_keyword == main and first_keyword in alts):
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
        
        return missing[:DEFAULT_MISSING_KEYWORDS_LIMIT]  # Return top N missing keywords
    
    def _calculate_match_score(
        self,
        matched_keywords: List[KeywordMatch],
        job_keywords: Counter,
        jd_phrases: Counter = None
    ) -> float:
        """
        Calculate weighted match score based on keyword importance and frequency.
        
        Scoring logic:
        - Technical keywords (Python, React, SQL, FastAPI, etc.) have weight 2.0
        - Normal keywords have weight 1.0
        - Keyword frequency from job description indicates importance
        - Score is returned as percentage (0-100)
        
        Args:
            matched_keywords: List of KeywordMatch objects from resume
            job_keywords: Counter of keywords from job description
            
        Returns:
            float: Match score as percentage (0-100)
        """
        if not job_keywords:
            return 0.0

        # Separate single-word matches from phrase matches for scoring
        phrase_set = set(jd_phrases.keys()) if jd_phrases else set()

        # Calculate total weighted importance of matched keywords (single words)
        matched_weight = 0.0
        matched_phrase_weight = 0.0
        for match in matched_keywords:
            keyword = match.keyword.lower()
            if keyword in phrase_set:
                # Phrases score proportionally to their JD frequency
                matched_phrase_weight += jd_phrases.get(keyword, 1)
            else:
                keyword_importance = job_keywords.get(keyword, 1)
                keyword_weight = self._get_keyword_weight(keyword)
                matched_weight += keyword_importance * keyword_weight
        
        # Calculate total weighted importance of all single-word job keywords
        total_keyword_weight = 0.0
        for keyword, frequency in job_keywords.items():
            keyword_weight = self._get_keyword_weight(keyword)
            total_keyword_weight += frequency * keyword_weight

        total_phrase_weight = sum(jd_phrases.values()) if jd_phrases else 0

        if total_phrase_weight > 0:
            # Phrases contribute 20 %, keywords contribute 80 %
            phrase_score = min((matched_phrase_weight / total_phrase_weight) * 20.0, 20.0)
            keyword_score = (
                min((matched_weight / total_keyword_weight) * 80.0, 80.0)
                if total_keyword_weight > 0 else 0.0
            )
        else:
            # No phrases available — keywords contribute the full 100 %
            phrase_score = 0.0
            keyword_score = (
                min((matched_weight / total_keyword_weight) * 100.0, 100.0)
                if total_keyword_weight > 0 else 0.0
            )

        score_percentage = min(keyword_score + phrase_score, 100.0)
        return round(score_percentage, 2)
    
    def _generate_recommendations(
        self,
        matched_keywords: List[KeywordMatch],
        missing_keywords: List[str],
        match_score: float
    ) -> List[str]:
        """
        Generate recommendations based on analysis.
        
        Args:
            matched_keywords: List of matched keywords
            missing_keywords: List of missing keywords
            match_score: Match score as percentage (0-100)
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if match_score < 30:
            recommendations.append(
                "Low match score. Consider adding more relevant keywords from the job description."
            )
        elif match_score < 60:
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
    
    def _get_suggestions_for_keywords(self, keywords: List[str]) -> dict:
        """
        Get synonym suggestions for a list of keywords.
        
        Returns a dictionary where keys are keywords and values are lists of synonyms.
        
        Args:
            keywords: List of keywords to get suggestions for
            
        Returns:
            dict: Dictionary with keyword -> list of synonyms mapping
        """
        suggestions = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Check if keyword exists in synonym dictionary
            if keyword_lower in self.synonym_dictionary:
                suggestions[keyword] = self.synonym_dictionary[keyword_lower]
            else:
                # Check for partial matches (e.g., if keyword contains a word in the dictionary)
                for dict_key, dict_synonyms in self.synonym_dictionary.items():
                    if dict_key in keyword_lower or keyword_lower in dict_key:
                        suggestions[keyword] = dict_synonyms
                        break
        
        return suggestions

    # ------------------------------------------------------------------
    # Phrase matching helpers
    # ------------------------------------------------------------------

    def _extract_phrases(self, text: str) -> Counter:
        """
        Extract meaningful 2-3 word phrases (n-grams) from text.

        A phrase is kept only when at least one of its words is NOT a
        stop word, ensuring that phrases like "machine learning" or
        "data analysis" are retained while noise phrases are dropped.

        Args:
            text: Source text (job description or resume)

        Returns:
            Counter mapping phrase -> occurrence count
        """
        # Normalise: lowercase and strip to plain words only
        normalised = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
        tokens = normalised.split()

        phrases: Counter = Counter()
        for n in (2, 3):  # bigrams then trigrams
            for i in range(len(tokens) - n + 1):
                gram = tokens[i:i + n]
                # Keep phrase only when ALL words are meaningful (non-stop, length >= 3)
                # This prevents noise like "we need" or "a candidate" from appearing
                if all(w not in self.stop_words and len(w) >= MIN_KEYWORD_LENGTH for w in gram):
                    phrase = ' '.join(gram)
                    phrases[phrase] += 1

        return phrases

    def _match_phrases(
        self,
        resume_text: str,
        jd_phrases: Counter,
    ) -> Tuple[List[KeywordMatch], List[str]]:
        """
        Check which job-description phrases appear in the resume text.

        Matching is done as a substring check on the normalised resume
        text so that word boundaries and minor spacing differences are
        handled gracefully.

        Args:
            resume_text: Full resume text
            jd_phrases: Counter of phrases extracted from job description

        Returns:
            Tuple of (matched_phrases, missing_phrases)
        """
        normalised_resume = re.sub(r'[^a-z0-9\s]', ' ', resume_text.lower())

        matched: List[KeywordMatch] = []
        missing: List[str] = []

        # Only consider the top phrases by frequency to keep output focused
        for phrase, freq in jd_phrases.most_common(30):
            if phrase in normalised_resume:
                relevance = min(freq / RELEVANCE_SCORE_DIVISOR, 1.0)
                matched.append(KeywordMatch(
                    keyword=phrase,
                    frequency=normalised_resume.count(phrase),
                    relevance_score=relevance,
                ))
            else:
                missing.append(phrase)

        return matched, missing
