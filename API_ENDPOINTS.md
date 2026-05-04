# API Endpoints Reference Guide

## Base URL
```
http://localhost:8000
```

## Endpoints Overview

### Health Check Endpoints

#### GET `/`
**Description**: Root endpoint - checks if API is running

**Response**:
```json
{
  "message": "Resume Keyword Optimizer API",
  "version": "1.0.0",
  "status": "running"
}
```

#### GET `/health`
**Description**: Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

---

## Resume Analysis Endpoints

### POST `/analyze`
**Description**: Analyze a resume and optionally match against a job description

**Request**:
```json
{
  "resume_text": "string (required)",
  "job_description": "string (optional)"
}
```

**Response** (200 OK):
```json
{
  "total_keywords": 45,
  "matched_keywords": [
    {
      "keyword": "python",
      "frequency": 5,
      "relevance_score": 0.85
    },
    {
      "keyword": "docker",
      "frequency": 3,
      "relevance_score": 0.75
    }
  ],
  "missing_keywords": [
    "kubernetes",
    "terraform",
    "ansible"
  ],
  "suggestions": {
    "kubernetes": ["k8s"],
    "docker": ["containerization", "containers"]
  },
  "match_score": 0.72,
  "recommendations": [
    "Good match! Your resume covers most required keywords.",
    "Consider adding these keywords: kubernetes, terraform, ansible"
  ]
}
```

**Error Responses**:
- 400: Resume text cannot be empty
- 500: Internal server error

---

### POST `/parse`
**Description**: Parse a resume and extract structured sections

**Request**:
```json
{
  "resume_text": "string (required)"
}
```

**Response** (200 OK):
```json
{
  "text": "Full resume text...",
  "sections": {
    "experience": "Senior Developer at...",
    "education": "Bachelor of Science...",
    "skills": "Python, Docker, Kubernetes..."
  },
  "contact_info": {
    "email": "john@example.com",
    "phone": "(555) 123-4567",
    "linkedin": "linkedin.com/in/johndoe"
  },
  "experience": [
    "Senior Developer at Tech Corp (2021-2024)",
    "Developer at StartUp Inc (2019-2021)"
  ],
  "skills": [
    "Python",
    "Docker",
    "Kubernetes",
    "AWS"
  ],
  "education": [
    "Bachelor of Science in Computer Science"
  ]
}
```

---

### POST `/upload`
**Description**: Upload and process a resume file

**Supported Formats**: `.txt`, `.pdf`, `.docx`  
**Max File Size**: 5MB

**Request**: Form data with file upload
```
file: <file>  (binary, required)
```

**Response** (200 OK):
Returns `ParsedResume` object (same structure as `/parse`)

**Error Responses**:
- 400: No file provided / Unsupported format / Encoding error
- 413: File size exceeds 5MB
- 500: Error processing file

---

## Keyword Extraction Endpoints

### POST `/keywords/extract`
**Description**: Extract top keywords from text

**Request**:
```json
{
  "resume_text": "string (required)"
}
```

**Response** (200 OK):
```json
{
  "top_keywords": [
    {
      "keyword": "python",
      "frequency": 8
    },
    {
      "keyword": "docker",
      "frequency": 6
    },
    {
      "keyword": "kubernetes",
      "frequency": 5
    }
  ],
  "total_unique_keywords": 24
}
```

---

### POST `/keywords/analyze-jd`
**Description**: Analyze a job description to extract key requirements

**Request**:
```json
{
  "resume_text": "string (required - contains job description)"
}
```

**Response** (200 OK):
```json
{
  "top_keywords": [
    {
      "keyword": "python",
      "frequency": 12
    },
    {
      "keyword": "experience",
      "frequency": 8
    },
    {
      "keyword": "microservices",
      "frequency": 6
    }
  ],
  "total_unique_keywords": 38,
  "keyword_frequency": {
    "python": 12,
    "experience": 8,
    "microservices": 6,
    "docker": 5
  }
}
```

---

## Comparison Endpoints

### POST `/compare`
**Description**: Compare resume keywords with job description requirements

**Request**:
```json
{
  "resume_text": "string (required)",
  "job_description": "string (required)"
}
```

**Response** (200 OK):
```json
{
  "match_score": 0.72,
  "matched_count": 18,
  "total_jd_keywords": 25,
  "missing_count": 7,
  "keyword_coverage_percentage": 72.0,
  "jaccard_similarity": 0.62,
  "top_resume_keywords": [
    {
      "keyword": "python",
      "frequency": 8
    },
    {
      "keyword": "docker",
      "frequency": 6
    }
  ],
  "top_jd_keywords": [
    {
      "keyword": "python",
      "frequency": 12
    },
    {
      "keyword": "microservices",
      "frequency": 6
    }
  ],
  "matched_keywords": [
    "python",
    "docker",
    "kubernetes",
    "aws",
    "git"
  ],
  "missing_keywords": [
    "terraform",
    "ansible",
    "jenkins",
    "prometheus"
  ]
}
```

**Error Responses**:
- 400: Resume text or job description cannot be empty
- 500: Comparison error

---

## Response Metrics Explained

### `match_score` (0.0 - 1.0)
- Percentage of job description keywords found in resume
- 0.0 = No matches
- 1.0 = All keywords matched
- 0.7+ = Good match

### `keyword_coverage_percentage` (0-100%)
- Same as match_score but as a percentage
- 70%+ = Strong candidate

### `jaccard_similarity` (0.0 - 1.0)
- Intersection / Union of all unique keywords
- 0.0 = Completely different
- 1.0 = Identical keyword sets
- 0.6+ = Significant overlap

### `relevance_score` (0.0 - 1.0)
- How relevant a matched keyword is
- Based on frequency in resume
- 0.8+ = Highly relevant

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|---|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid input (empty text, unsupported format) |
| 413 | Payload Too Large | Uploaded file exceeds 5MB |
| 500 | Internal Server Error | Unexpected server error |

---

## Example Usage - Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Example 1: Analyze resume with job description
response = requests.post(
    f"{BASE_URL}/analyze",
    json={
        "resume_text": "Python developer with 5 years experience...",
        "job_description": "Senior Python Developer needed..."
    }
)
analysis = response.json()
print(f"Match Score: {analysis['match_score']}")
print(f"Missing Keywords: {analysis['missing_keywords']}")

# Example 2: Upload file
with open("resume.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/upload", files=files)
parsed = response.json()
print(f"Skills: {parsed['skills']}")

# Example 3: Extract keywords
response = requests.post(
    f"{BASE_URL}/keywords/extract",
    json={"resume_text": "Python, Docker, Kubernetes..."}
)
keywords = response.json()
print(f"Top Keywords: {keywords['top_keywords']}")
```

---

## Example Usage - JavaScript/TypeScript

```javascript
const BASE_URL = "http://localhost:8000";

// Example 1: Analyze resume
async function analyzeResume() {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_text: "Python developer with 5 years experience...",
      job_description: "Senior Python Developer needed..."
    })
  });
  const analysis = await response.json();
  console.log(`Match Score: ${analysis.match_score}`);
  console.log(`Missing Keywords: ${analysis.missing_keywords}`);
}

// Example 2: Upload file
async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData
  });
  const parsed = await response.json();
  console.log(`Skills: ${parsed.skills}`);
}

// Example 3: Extract keywords
async function extractKeywords(text) {
  const response = await fetch(`${BASE_URL}/keywords/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: text })
  });
  const keywords = await response.json();
  console.log(`Top Keywords: ${keywords.top_keywords}`);
}
```

---

## API Documentation (Swagger/OpenAPI)

Full interactive API documentation available at:
```
http://localhost:8000/docs
```

Alternative (ReDoc format):
```
http://localhost:8000/redoc
```

---

## Rate Limiting & Best Practices

**Current Implementation**: No rate limiting (add in production)

**Recommendations**:
1. Limit file uploads to <5MB ✅ (Implemented)
2. Limit text input to reasonable size (recommended: 1MB)
3. Add rate limiting per IP (recommended: 100 requests/minute)
4. Cache JD analysis for identical inputs

---

## Troubleshooting

### "Resume text cannot be empty"
- Ensure your text field has content
- Check for encoding issues if uploading files

### "File must be valid UTF-8 encoded"
- Try saving file with UTF-8 encoding
- Alternative: Latin-1 encoding is supported

### "File size exceeds maximum allowed size"
- Reduce file size (current limit: 5MB)
- Use `.txt` format instead of `.pdf` for smaller size

### Low match score even with relevant keywords
- Keywords might be written differently (e.g., "Python" vs "python")
- Check the `missing_keywords` and `suggestions` for alternatives
- Use `/keywords/extract` endpoint to see what was extracted

