"""Resume parsing module for extracting structured data from resume text."""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from app.schemas import ParsedResume

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None


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
    
    def parse_file(self, file_path: str) -> ParsedResume:
        """
        Parse a resume file in multiple formats (.txt, .pdf, .docx).
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            ParsedResume: Structured resume data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.txt':
            resume_text = self._read_txt_file(file_path)
        elif file_extension == '.pdf':
            resume_text = self._read_pdf_file(file_path)
        elif file_extension == '.docx':
            resume_text = self._read_docx_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: .txt, .pdf, .docx")
        
        return self.parse(resume_text)
    
    def _read_txt_file(self, file_path: str) -> str:
        """
        Read a .txt resume file.
        
        Args:
            file_path: Path to the .txt file
            
        Returns:
            str: The contents of the .txt file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _read_pdf_file(self, file_path: str) -> str:
        """
        Read a .pdf resume file using pdfplumber.
        
        Args:
            file_path: Path to the .pdf file
            
        Returns:
            str: Extracted text from the PDF
            
        Raises:
            ImportError: If pdfplumber is not installed
        """
        if pdfplumber is None:
            raise ImportError("pdfplumber is not installed. Install it with: pip install pdfplumber")
        
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")
    
    def _read_docx_file(self, file_path: str) -> str:
        """
        Read a .docx resume file using python-docx.
        
        Args:
            file_path: Path to the .docx file
            
        Returns:
            str: Extracted text from the .docx file
            
        Raises:
            ImportError: If python-docx is not installed
        """
        if Document is None:
            raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading DOCX file: {str(e)}")
    
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
