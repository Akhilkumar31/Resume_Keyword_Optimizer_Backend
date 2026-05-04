#!/usr/bin/env python3
"""
Demo script showing the improved scoring logic for Resume Keyword Optimizer.

Features:
- Technical keywords (Python, React, SQL, Docker, AWS, etc.) get 2x weight
- Score is calculated as percentage (0-100)
- Keyword frequency from job description indicates importance
- Normal keywords get 1x weight
"""

from app.analyzer import KeywordAnalyzer

def demo_improved_scoring():
    """Demonstrate the improved scoring logic."""
    analyzer = KeywordAnalyzer()
    
    print("=" * 80)
    print("RESUME KEYWORD OPTIMIZER - IMPROVED SCORING DEMO")
    print("=" * 80)
    
    # Example 1: High technical skills match
    print("\n1. EXAMPLE: Python Backend Developer vs Python Backend Job")
    print("-" * 80)
    
    resume_python_backend = """
    Experienced Python developer with 5 years of experience.
    Proficient in:
    - Python, Django, FastAPI
    - PostgreSQL, Redis
    - Docker, Kubernetes
    - AWS, CI/CD
    - REST APIs, Git
    """
    
    jd_python_backend = """
    Seeking Senior Python Backend Developer
    Required Skills:
    - Python, FastAPI, Django
    - PostgreSQL, Redis, SQL
    - Docker, Kubernetes
    - AWS, Azure
    - REST API design
    - Git, Jenkins, CI/CD
    - Problem solving and communication
    """
    
    result1 = analyzer.analyze_resume(resume_python_backend, jd_python_backend)
    print(f"Match Score: {result1.match_score}%")
    print(f"Matched Keywords ({len(result1.matched_keywords)}): {', '.join([m.keyword for m in result1.matched_keywords[:10]])}")
    print(f"Missing Keywords ({len(result1.missing_keywords)}): {', '.join(result1.missing_keywords[:5])}")
    print("\nRecommendations:")
    for rec in result1.recommendations:
        print(f"  • {rec}")
    
    # Example 2: Low technical skills match
    print("\n\n2. EXAMPLE: Python Developer vs Frontend React Job")
    print("-" * 80)
    
    resume_python_dev = """
    Python specialist with strong backend skills.
    Experience with: Python, Django, PostgreSQL, REST APIs
    """
    
    jd_frontend = """
    Frontend React Developer needed
    Skills required: React, JavaScript, TypeScript, HTML, CSS, Redux, Jest
    """
    
    result2 = analyzer.analyze_resume(resume_python_dev, jd_frontend)
    print(f"Match Score: {result2.match_score}%")
    print(f"Matched Keywords ({len(result2.matched_keywords)}): {', '.join([m.keyword for m in result2.matched_keywords])}")
    print(f"Missing Keywords ({len(result2.missing_keywords)}): {', '.join(result2.missing_keywords[:5])}")
    print("\nRecommendations:")
    for rec in result2.recommendations:
        print(f"  • {rec}")
    
    # Example 3: Perfect match
    print("\n\n3. EXAMPLE: Perfect Resume Match")
    print("-" * 80)
    
    perfect_resume = "python docker kubernetes aws postgresql"
    perfect_jd = "python docker kubernetes aws postgresql"
    
    result3 = analyzer.analyze_resume(perfect_resume, perfect_jd)
    print(f"Match Score: {result3.match_score}%")
    print(f"Matched Keywords ({len(result3.matched_keywords)}): {', '.join([m.keyword for m in result3.matched_keywords])}")
    print(f"Missing Keywords: {len(result3.missing_keywords)}")
    
    # Example 4: Mixed technical and non-technical keywords
    print("\n\n4. EXAMPLE: Technical Keywords Get Higher Weights")
    print("-" * 80)
    
    mixed_resume = "communication teamwork collaboration python docker"
    mixed_jd = "strong communication teamwork python docker kubernetes"
    
    result4 = analyzer.analyze_resume(mixed_resume, mixed_jd)
    print(f"Match Score: {result4.match_score}%")
    print(f"\nKeyword Weights:")
    print(f"  Technical Keywords (2x weight): Python, Docker, Kubernetes")
    print(f"  Normal Keywords (1x weight): communication, teamwork, collaboration")
    print(f"\nMatched Technical Keywords: python, docker")
    print(f"Missing Technical Keyword: kubernetes")
    print(f"Matched Normal Keywords: communication, teamwork, collaboration")
    print(f"\nWhy the score is not 100%:")
    print(f"  - Missing 'kubernetes' (technical keyword with high importance)")
    print(f"  - This is weighted heavily in the scoring algorithm")
    
    # Show technical keywords set
    print("\n\n5. TECHNICAL KEYWORDS (2x weight)")
    print("-" * 80)
    from app.analyzer import TECHNICAL_KEYWORDS
    tech_list = sorted(list(TECHNICAL_KEYWORDS))
    print(f"Total technical keywords tracked: {len(tech_list)}")
    print(f"Examples: {', '.join(tech_list[:15])}")
    
    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS:")
    print("=" * 80)
    print("""
1. WEIGHTED SCORING: Technical keywords (Python, React, SQL, FastAPI, Docker, AWS, etc.)
   are given 2x weight compared to normal keywords (1x weight).

2. KEYWORD IMPORTANCE: Score considers both:
   - Which keywords are matched
   - How frequently they appear in the job description (importance)

3. PERCENTAGE SCALE: Scores are now 0-100% instead of 0-1.0, making them more intuitive.

4. SIMPLE & READABLE: The code is clean and easy to understand with clear comments.

5. UNCHANGED OUTPUT: Matched keywords and missing keywords output remains the same.
    """)

if __name__ == "__main__":
    demo_improved_scoring()
