# GetProg.ai Candidate Scraper

This project contains two Python scripts for scraping candidate information from GetProg.ai. The scripts are designed to extract candidate profiles based on specific search criteria and save them to a JSON file.

## Scripts

- `scraping_v1.py`: Original version of the scraper
- `scraping_v2.py`: Alternative version with additional debug print statements

## Features

- Automated login to GetProg.ai
- Multi-page candidate data extraction
- Automatic pagination handling
- Duplicate candidate detection and merging
- Data cleaning and validation
- JSON output format

## Data Fields

The scraper extracts the following information for each candidate:

- Name
- Position
- Experience
- Location
- GitHub URL
- LinkedIn URL
- Education (currently limited matching)
- Skills
- Page number (source page)

## Known Issues

### Education Field Matching

The current implementation has limited education field matching capabilities:

1. Only matches basic education keywords:
   - "University"
   - "College"
   - "Bachelor"
   - "Master"
   - "PhD"
   - "B.S."
   - "M.S."
   - "Ph.D."

2. Limitations:
   - May miss education information if it doesn't contain these exact keywords
   - Doesn't handle variations in education degree formats
   - May not capture full education history if multiple entries exist
   - Doesn't distinguish between different types of degrees (e.g., B.S. vs B.A.)

## Usage

1. Install required dependencies:
```bash
pip install selenium
```

2. Run either script:
```bash
python scraping_v1.py
# or
python scraping_v2.py
```

3. Enter your GetProg.ai credentials when prompted

4. The script will:
   - Log in to your account
   - Navigate through search results
   - Extract candidate information
   - Clean and deduplicate data
   - Save results to `getprog_candidates.json`

## Output

The script generates a JSON file (`getprog_candidates.json`) containing an array of candidate objects. Each object includes the candidate's information in the following format:

```json
{
  "name": "John Doe",
  "position": "Software Engineer",
  "experience": "5 years",
  "location": "San Francisco, California",
  "github": "https://github.com/johndoe",
  "linkedin": "https://linkedin.com/in/johndoe",
  "education": "Bachelor of Science in Computer Science",
  "skills": ["Python", "Java", "JavaScript"],
  "page": 1
}
```

## Future Improvements

1. Enhance education field matching:
   - Add support for more education keywords
   - Implement fuzzy matching for degree variations
   - Add support for multiple education entries
   - Improve degree type detection

2. Additional features:
   - Add support for custom search criteria
   - Implement rate limiting
   - Add proxy support
   - Improve error handling and recovery
   - Add support for different output formats 