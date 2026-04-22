"""Resume parsing module for extracting structured data from resume text."""

import re
from typing import Dict, List
from app.schemas import ParsedResume


class ResumeParser:
    """Parses resume text and extracts structured information."""
    
    # Common section headers
    SECTION_HEADERS = {
        'experience': ['experience', 'work experience', 'professional experience', 'employment'],
        'education': ['education', 'academic', 'qualification'],
        'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
        'contact': ['contact', 'contact information', 'personal information'],
        'summary': ['summary', 'objective', 'professional summary', 'executive summary']
    }
    
    def __init__(self):
        """Initialize the resume parser."""
        pass
    
    def parse(self, resume_text: str) -> ParsedResume:
        """
        Parse resume text and extract sections.
        
        Args:
            resume_text: The raw resume text to parse
            
        Returns:
            ParsedResume: Structured resume data
        """
        sections = self._extract_sections(resume_text)
        contact_info = self._extract_contact_info(resume_text)
        skills = self._extract_skills(sections)
        experience = self._extract_experience(sections)
        education = self._extract_education(sections)
        
        return ParsedResume(
            text=resume_text,
            sections=sections,
            contact_info=contact_info,
            experience=experience,
            skills=skills,
            education=education
        )
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract resume sections based on common headers."""
        sections = {}
        lines = text.split('\n')
        current_section = 'other'
        section_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            found_section = False
            for section_name, headers in self.SECTION_HEADERS.items():
                if any(header in line_lower for header in headers):
                    if section_content:
                        sections[current_section] = '\n'.join(section_content)
                    current_section = section_name
                    section_content = []
                    found_section = True
                    break
            
            if not found_section and line.strip():
                section_content.append(line)
        
        if section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from resume."""
        contact = {}
        
        # Email pattern
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone pattern
        phone_match = re.search(r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        # LinkedIn pattern
        linkedin_match = re.search(r'linkedin\.com/in/[^\s]+', text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = linkedin_match.group()
        
        return contact if contact else None
    
    def _extract_skills(self, sections: Dict[str, str]) -> List[str]:
        """Extract skills from parsed sections."""
        skills = []
        
        if 'skills' in sections:
            # Split by common delimiters
            skill_text = sections['skills']
            # Remove section headers and split
            for item in re.split(r'[,•\n]', skill_text):
                item = item.strip()
                if item and len(item) > 1:
                    skills.append(item)
        
        return skills
    
    def _extract_experience(self, sections: Dict[str, str]) -> List[str]:
        """Extract work experience entries."""
        experience = []
        
        if 'experience' in sections:
            # Split experience entries (usually separated by newlines or bullets)
            entries = re.split(r'\n(?=[A-Z])', sections['experience'])
            experience = [entry.strip() for entry in entries if entry.strip()]
        
        return experience
    
    def _extract_education(self, sections: Dict[str, str]) -> List[str]:
        """Extract education entries."""
        education = []
        
        if 'education' in sections:
            entries = re.split(r'\n(?=[A-Z])', sections['education'])
            education = [entry.strip() for entry in entries if entry.strip()]
        
        return education
