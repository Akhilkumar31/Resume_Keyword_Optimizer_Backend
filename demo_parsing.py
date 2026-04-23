"""Demonstration of resume parsing with multiple file formats."""

from pathlib import Path
from app.parser import ResumeParser


def demo_file_parsing():
    """Demonstrate parsing resumes in different formats."""
    parser = ResumeParser()
    tests_dir = Path(__file__).parent / "tests"
    
    print("=" * 60)
    print("Resume File Format Support - Demonstration")
    print("=" * 60)
    
    # Test TXT file
    print("\n[1] Testing TXT File Parsing")
    print("-" * 60)
    txt_file = tests_dir / "sample_resume.txt"
    if txt_file.exists():
        try:
            result = parser.parse_file(str(txt_file))
            print(f"✓ Successfully parsed: {txt_file.name}")
            print(f"  - Text length: {len(result.text)} characters")
            print(f"  - Contact info: {result.contact_info}")
            print(f"  - Skills found: {len(result.skills)}")
            print(f"  - Experience entries: {len(result.experience)}")
            print(f"  - Education entries: {len(result.education)}")
            print(f"  - Sections extracted: {list(result.sections.keys())}")
        except Exception as e:
            print(f"✗ Error parsing TXT: {e}")
    else:
        print(f"✗ Sample TXT file not found at {txt_file}")
    
    # Test DOCX file
    print("\n[2] Testing DOCX File Parsing")
    print("-" * 60)
    docx_file = tests_dir / "sample_resume.docx"
    if docx_file.exists():
        try:
            result = parser.parse_file(str(docx_file))
            print(f"✓ Successfully parsed: {docx_file.name}")
            print(f"  - Text length: {len(result.text)} characters")
            print(f"  - Contact info: {result.contact_info}")
            print(f"  - Skills found: {len(result.skills)}")
            print(f"  - Experience entries: {len(result.experience)}")
            print(f"  - Education entries: {len(result.education)}")
            print(f"  - Sections extracted: {list(result.sections.keys())}")
        except ImportError as e:
            print(f"⚠ Warning: {e}")
        except Exception as e:
            print(f"✗ Error parsing DOCX: {e}")
    else:
        print(f"✗ Sample DOCX file not found at {docx_file}")
    
    # Test direct text parsing
    print("\n[3] Testing Direct Text Parsing")
    print("-" * 60)
    sample_text = """
    John Doe
    john@example.com | (555) 123-4567
    
    SKILLS
    Python, JavaScript, SQL
    
    EXPERIENCE
    Senior Developer at Tech Corp
    """
    try:
        result = parser.parse(sample_text)
        print("✓ Successfully parsed direct text")
        print(f"  - Contact info: {result.contact_info}")
        print(f"  - Skills: {result.skills}")
        print(f"  - Sections: {list(result.sections.keys())}")
    except Exception as e:
        print(f"✗ Error parsing text: {e}")
    
    print("\n" + "=" * 60)
    print("Demonstration Complete")
    print("=" * 60)


if __name__ == "__main__":
    demo_file_parsing()
