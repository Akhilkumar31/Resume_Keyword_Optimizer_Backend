"""Demo script showcasing the synonym suggestion feature."""

from app.analyzer import KeywordAnalyzer

def main():
    """Demonstrate synonym suggestions for missing keywords."""
    
    analyzer = KeywordAnalyzer()
    
    # Sample resume with limited keywords
    resume = """
    John Smith
    Software Developer
    
    EXPERIENCE
    - 3 years developing websites with HTML and CSS
    - Built applications using Node.js
    - Basic SQL database experience
    
    SKILLS
    - HTML, CSS, JavaScript
    - Node.js, Express
    - MySQL, Git
    """
    
    # Job description looking for specific technologies
    job_description = """
    Senior Full Stack Developer Required
    
    Required Skills:
    - 5+ years with Python and TypeScript
    - React.js for frontend development
    - Docker and Kubernetes for containerization
    - AWS cloud platform experience
    - PostgreSQL database expertise
    - CI/CD pipeline implementation
    - Machine Learning basics
    - Microservices architecture
    """
    
    print("=" * 80)
    print("SYNONYM SUGGESTION FEATURE DEMO")
    print("=" * 80)
    print()
    
    # Analyze resume vs job description
    analysis = analyzer.analyze_resume(resume, job_description)
    
    print(f"Total Keywords Found: {analysis.total_keywords}")
    print()
    
    print("MATCHED KEYWORDS:")
    print("-" * 40)
    if analysis.matched_keywords:
        for match in analysis.matched_keywords:
            print(f"  ✓ {match.keyword} (frequency: {match.frequency}, relevance: {match.relevance_score})")
    else:
        print("  No matches found")
    print()
    
    print("MISSING KEYWORDS:")
    print("-" * 40)
    if analysis.missing_keywords:
        for keyword in analysis.missing_keywords[:10]:
            print(f"  ✗ {keyword}")
    else:
        print("  All keywords covered!")
    print()
    
    print("SYNONYM SUGGESTIONS FOR MISSING KEYWORDS:")
    print("-" * 40)
    if analysis.suggestions:
        for keyword, synonyms in analysis.suggestions.items():
            print(f"  {keyword}:")
            for synonym in synonyms:
                print(f"    → {synonym}")
    else:
        print("  No suggestions available")
    print()
    
    print("ANALYSIS METRICS:")
    print("-" * 40)
    print(f"  Match Score: {analysis.match_score * 100:.1f}%")
    print()
    
    print("RECOMMENDATIONS:")
    print("-" * 40)
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"  {i}. {rec}")
    print()
    
    print("=" * 80)
    print("KEY BENEFITS OF SYNONYM SUGGESTIONS:")
    print("=" * 80)
    print("""
    1. QUICK REFERENCE: See alternative keywords you should add to your resume
    2. SKILL MAPPING: Understand how your current skills map to job requirements
    3. BETTER MATCHING: Add synonyms to improve ATS (Applicant Tracking System) scores
    4. CAREER GUIDANCE: Identify industry-standard terminology for your role
    
    Example Output Format:
    {
        "python": ["py", "python3"],
        "react": ["reactjs", "react.js"],
        "docker": ["containerization", "containers"],
        "aws": ["amazon", "amazon web services"]
    }
    """)

if __name__ == "__main__":
    main()
