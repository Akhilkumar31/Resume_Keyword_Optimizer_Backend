# Developer Guide: Improved Scoring Logic

## Quick Start

### Using the Analyzer
```python
from app.analyzer import KeywordAnalyzer

analyzer = KeywordAnalyzer()

# Analyze a resume against a job description
resume = """
Senior Python Developer with FastAPI experience.
Skills: Python, FastAPI, PostgreSQL, Docker, AWS, pytest, Git
"""

job_description = """
Python Backend Developer Required
Must have: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS
Nice to have: Redis, Machine Learning
"""

result = analyzer.analyze_resume(resume, job_description)

print(f"Match Score: {result.match_score}%")  # e.g., 75.5%
print(f"Matched Keywords: {[m.keyword for m in result.matched_keywords]}")
print(f"Missing Keywords: {result.missing_keywords}")
```

### Understanding Score Output
```python
result.match_score  # Returns value between 0.0 and 100.0
# 0-20%:    Very poor match
# 20-40%:   Poor match
# 40-60%:   Moderate match
# 60-80%:   Good match
# 80-100%:  Excellent match
```

## Architecture

### Score Calculation Flow
```
Resume Text
    ↓
Extract Keywords → Counter{keyword: frequency}
    ↓
Compare with Job Description Keywords
    ↓
Find Matched Keywords
    ↓
Calculate Weighted Score
    ├─ For each matched keyword:
    │  ├─ Get frequency (importance)
    │  ├─ Get weight (2.0 if technical, 1.0 if normal)
    │  └─ Add to matched_weight
    ├─ For all JD keywords:
    │  └─ Calculate total_weight
    └─ Score = (matched_weight / total_weight) × 100
    ↓
Return ResumeAnalysis object
    ├─ match_score: percentage (0-100)
    ├─ matched_keywords: List[KeywordMatch]
    ├─ missing_keywords: List[str]
    └─ recommendations: List[str]
```

## Core Components

### 1. Technical Keywords Set
```python
# Location: app/analyzer.py

TECHNICAL_KEYWORDS = {
    # Languages
    'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'csharp',
    
    # Web Frameworks
    'react', 'vue', 'angular', 'django', 'fastapi', 'flask',
    
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
    
    # DevOps
    'docker', 'kubernetes', 'aws', 'azure', 'gcp',
    
    # More...
}
```

### 2. Keyword Weight Determination
```python
def _get_keyword_weight(self, keyword: str) -> float:
    """
    Determine weight of a keyword.
    
    Returns:
        2.0 if technical keyword, 1.0 if normal
    """
    keyword_lower = keyword.lower()
    
    # Direct match
    if keyword_lower in TECHNICAL_KEYWORDS:
        return TECHNICAL_KEYWORD_WEIGHT
    
    # Partial match (e.g., "python3" contains "python")
    for tech_keyword in TECHNICAL_KEYWORDS:
        if tech_keyword in keyword_lower or keyword_lower in tech_keyword:
            return TECHNICAL_KEYWORD_WEIGHT
    
    return NORMAL_KEYWORD_WEIGHT
```

### 3. Weighted Score Calculation
```python
def _calculate_match_score(
    self,
    matched_keywords: List[KeywordMatch],
    job_keywords: Counter
) -> float:
    """Calculate weighted percentage score."""
    
    if not job_keywords:
        return 0.0
    
    # Sum weighted matched keywords
    matched_weight = 0.0
    for match in matched_keywords:
        keyword = match.keyword.lower()
        importance = job_keywords.get(keyword, 1)
        weight = self._get_keyword_weight(keyword)
        matched_weight += importance * weight
    
    # Sum all weighted job keywords
    total_weight = 0.0
    for keyword, frequency in job_keywords.items():
        weight = self._get_keyword_weight(keyword)
        total_weight += frequency * weight
    
    # Calculate percentage
    if total_weight == 0:
        return 0.0
    
    score = min((matched_weight / total_weight) * 100, 100.0)
    return round(score, 2)
```

## Extending the System

### Adding New Technical Keywords
```python
# In app/analyzer.py, add to TECHNICAL_KEYWORDS set

TECHNICAL_KEYWORDS = {
    # ... existing keywords ...
    'golang',        # New language
    'rust',          # New language
    'terraform',     # New DevOps tool
    'prometheus',    # New monitoring tool
}
```

### Changing Keyword Weights
```python
# In app/analyzer.py, modify weight constants

TECHNICAL_KEYWORD_WEIGHT = 3.0  # Increase weight for technical keywords
NORMAL_KEYWORD_WEIGHT = 0.5     # Decrease weight for normal keywords

# Or modify in _get_keyword_weight method for granular control
def _get_keyword_weight(self, keyword: str) -> float:
    keyword_lower = keyword.lower()
    
    # Critical keywords get highest weight
    if keyword_lower in {'python', 'aws', 'docker'}:
        return 3.0
    
    # Other technical keywords
    if keyword_lower in TECHNICAL_KEYWORDS:
        return 2.0
    
    return 1.0
```

### Industry-Specific Scoring
```python
class IndustryAnalyzer(KeywordAnalyzer):
    """Custom analyzer for specific industry."""
    
    def __init__(self, industry: str):
        super().__init__()
        self.industry = industry
        self._set_industry_keywords()
    
    def _set_industry_keywords(self):
        """Override technical keywords based on industry."""
        if self.industry == "data_science":
            self.technical_keywords = {
                'python', 'r', 'sql', 'tensorflow', 'pytorch',
                'machine learning', 'data science', 'pandas', 'numpy'
            }
        elif self.industry == "frontend":
            self.technical_keywords = {
                'javascript', 'typescript', 'react', 'vue', 'angular',
                'html', 'css', 'webpack', 'typescript'
            }
```

## Testing Guide

### Unit Tests
```python
def test_technical_keyword_weight(analyzer):
    """Verify technical keywords get 2x weight."""
    weight = analyzer._get_keyword_weight("python")
    assert weight == 2.0

def test_normal_keyword_weight(analyzer):
    """Verify normal keywords get 1x weight."""
    weight = analyzer._get_keyword_weight("communication")
    assert weight == 1.0

def test_score_percentage_range(analyzer):
    """Verify score is always in valid range."""
    result = analyzer.analyze_resume("test resume", "test job description")
    assert 0.0 <= result.match_score <= 100.0
```

### Integration Tests
```python
def test_perfect_match_score():
    """Perfect match should return 100%."""
    text = "python docker kubernetes aws"
    analyzer = KeywordAnalyzer()
    result = analyzer.analyze_resume(text, text)
    assert result.match_score == 100.0

def test_no_match_score():
    """No matching keywords should return 0%."""
    resume = "customer service representative"
    jd = "python docker kubernetes machine learning"
    analyzer = KeywordAnalyzer()
    result = analyzer.analyze_resume(resume, jd)
    assert result.match_score == 0.0
```

## Performance Considerations

### Time Complexity Analysis
```
analyze_resume():
  - Extract keywords: O(w) where w = words in text
  - Find matches: O(m × j) where m = matched, j = job keywords
  - Calculate score: O(m + j)
  - Total: O(w + m×j) ≈ O(w) for typical resumes

_get_keyword_weight():
  - Set lookup: O(1)
  - Substring search: O(k × len(keyword)) where k = technical keywords (55)
  - Total: O(1) average case, O(k) worst case
```

### Memory Usage
```
TECHNICAL_KEYWORDS set:     ~10 KB
Counter objects:             Proportional to unique words (~100-500)
ResumeAnalysis object:       ~5-20 KB
Total typical memory:        <1 MB per analysis
```

### Optimization Tips
1. **Cache keyword weights**: Use functools.lru_cache for _get_keyword_weight
2. **Batch processing**: Process multiple resumes together
3. **Lazy loading**: Load technical keywords only when needed

## API Integration

### FastAPI Endpoint Response
```python
{
    "total_keywords": 25,
    "matched_keywords": [
        {
            "keyword": "python",
            "frequency": 3,
            "relevance_score": 0.85
        },
        {
            "keyword": "docker",
            "frequency": 2,
            "relevance_score": 0.80
        }
    ],
    "missing_keywords": ["kubernetes", "terraform"],
    "suggestions": {
        "kubernetes": ["k8s", "orchestration"],
        "terraform": ["infrastructure as code", "iac"]
    },
    "match_score": 72.5,  # Now a percentage!
    "recommendations": [
        "Good match! Your resume covers most required keywords.",
        "Consider adding these keywords: kubernetes, terraform"
    ]
}
```

## Common Use Cases

### Use Case 1: Resume Screening
```python
def screen_resume(resume: str, jd: str) -> bool:
    """Automatically reject if score is too low."""
    analyzer = KeywordAnalyzer()
    result = analyzer.analyze_resume(resume, jd)
    
    if result.match_score < 40:
        return False  # Below threshold
    
    return True  # Worth reviewing
```

### Use Case 2: Resume Ranking
```python
def rank_resumes(resumes: List[str], jd: str) -> List[Tuple[str, float]]:
    """Rank resumes by match score."""
    analyzer = KeywordAnalyzer()
    scores = []
    
    for resume in resumes:
        result = analyzer.analyze_resume(resume, jd)
        scores.append((resume, result.match_score))
    
    return sorted(scores, key=lambda x: x[1], reverse=True)
```

### Use Case 3: Skills Gap Analysis
```python
def analyze_skills_gap(resume: str, jd: str) -> Dict:
    """Identify skills gaps and improvement areas."""
    analyzer = KeywordAnalyzer()
    result = analyzer.analyze_resume(resume, jd)
    
    return {
        "current_score": result.match_score,
        "critical_missing": [
            kw for kw in result.missing_keywords
            if analyzer._get_keyword_weight(kw) == 2.0
        ],
        "nice_to_have": [
            kw for kw in result.missing_keywords
            if analyzer._get_keyword_weight(kw) == 1.0
        ],
        "improvement_areas": result.recommendations
    }
```

## Troubleshooting

### Score is always 0%
```python
# Check if keywords are being extracted
keywords = analyzer._extract_keywords(resume_text)
if not keywords:
    print("No keywords found - check stopwords list")

# Verify job description has keywords
jd_keywords = analyzer._extract_keywords(job_description)
print(f"JD Keywords found: {len(jd_keywords)}")
```

### Technical keywords not recognized
```python
# Check if keyword is in the set
keyword = "pytorch"
if keyword in TECHNICAL_KEYWORDS:
    print("Keyword recognized as technical")
else:
    # Add it to the set
    TECHNICAL_KEYWORDS.add(keyword)
```

### Score seems too low
```python
# Check if technical keywords are being weighted
for kw in matched_keywords:
    weight = analyzer._get_keyword_weight(kw.keyword)
    print(f"{kw.keyword}: weight={weight}")

# If all technical keywords have weight=1.0, check TECHNICAL_KEYWORDS set
print(TECHNICAL_KEYWORDS)
```

## Resources

- Main Implementation: `app/analyzer.py`
- Data Models: `app/schemas.py`
- Demo Script: `demo_improved_scoring.py`
- Documentation: `SCORING_IMPROVEMENTS.md`
- Quick Reference: `SCORING_QUICK_REFERENCE.md`
