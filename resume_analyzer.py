import json
import re
import argparse
from datetime import datetime
from pathlib import Path


# Expanded skill vocabulary with common industry technologies
SKILLS = [
    "python",
    "java",
    "c++",
    "c",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "express",
    "html",
    "css",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "machine learning",
    "deep learning",
    "natural language processing",
    "data analysis",
    "pandas",
    "numpy",
    "scikit-learn",
    "git",
    "docker",
    "aws",
    "communication",
    "teamwork",
    "rest api",
    "fastapi",
    "django",
    "flask",
    "graphql",
    "kubernetes",
    "ci/cd",
    "tableau",
    "power bi",
    "linux",
    "agile",
    "scrum",
    "tensorflow",
    "pytorch",
    "excel",
]

# Aliases and normalization mapping
SKILL_ALIASES = {
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "postgresql": ["postgresql", "postgres"],
    "rest api": ["rest api", "rest apis", "restful api", "restful apis", "restful"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "natural language processing": ["natural language processing", "nlp"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "kubernetes": ["kubernetes", "k8s"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration"],
    "power bi": ["power bi", "powerbi"],
    "git": ["git", "github", "gitlab"],
    "aws": ["aws", "amazon web services"],
}

SECTION_ALIASES = {
    "education": [
        "education",
        "academic background",
        "educational qualifications",
        "academics",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "key skills",
        "technologies",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship",
        "internships",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "licenses",
        "credentials",
    ],
    "summary": [
        "summary",
        "professional summary",
        "career objective",
        "objective",
        "about me",
    ],
}


def normalize_line(line):
    """Normalize a line for section-heading comparison."""
    return re.sub(r"[^a-z ]", "", line.lower()).strip()


def detect_sections(text):
    """Split text into recognized resume sections."""
    sections = {}
    current_section = "other"
    sections[current_section] = []

    alias_lookup = {}
    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            alias_lookup[normalize_line(alias)] = section

    for line in text.splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        heading = normalize_line(cleaned.rstrip(":"))
        matched_section = alias_lookup.get(heading)

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(cleaned)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if lines
    }


def find_skills(text):
    """Find vocabulary matches using case-insensitive boundaries and synonyms."""
    found = set()

    for canonical_skill in SKILLS:
        aliases = SKILL_ALIASES.get(canonical_skill, [canonical_skill])
        for variant in aliases:
            pattern = (
                r"(?<![a-z0-9+#.])"
                + re.escape(variant)
                + r"(?![a-z0-9+#.])"
            )
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.add(canonical_skill)
                break

    return sorted(found, key=str.lower)


def extract_skill_evidence(text: str, skills: list[str]) -> dict[str, list[str]]:
    """Extract context sentences or bullet points where each skill was found."""
    evidence = {}
    lines = [line.strip() for line in re.split(r"[\n\r]+", text) if line.strip()]

    for skill in skills:
        aliases = SKILL_ALIASES.get(skill, [skill])
        excerpts = []
        for line in lines:
            for variant in aliases:
                pattern = r"(?<![a-z0-9+#.])" + re.escape(variant) + r"(?![a-z0-9+#.])"
                if re.search(pattern, line, flags=re.IGNORECASE):
                    cleaned = line.strip(" -*•|")
                    if cleaned and cleaned not in excerpts:
                        excerpts.append(cleaned[:180])
                    break
            if len(excerpts) >= 3:
                break
        evidence[skill] = excerpts
    return evidence


def estimate_experience_years(text: str) -> float | None:
    """
    Extract explicitly stated experience years or date ranges.
    Returns None if unknown — avoids defaulting unknown experience to 0.0.
    """
    # 1. Direct mention: "X years of experience" or "X+ years"
    matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience",
        text,
        flags=re.IGNORECASE,
    )
    if matches:
        try:
            return round(float(matches[0]), 1)
        except ValueError:
            pass

    # 2. Year ranges: e.g. "2021 - 2024", "2022 – Present"
    ranges = re.findall(
        r"\b(20\d{2}|19\d{2})\s*[-–—to]+\s*(20\d{2}|present|current)\b",
        text,
        flags=re.IGNORECASE,
    )
    if ranges:
        current_year = datetime.now().year
        total = 0.0
        for start_s, end_s in ranges:
            try:
                start = int(start_s)
                end = current_year if end_s.lower() in ("present", "current") else int(end_s)
                if 0 <= (end - start) <= 40:
                    total += (end - start)
            except ValueError:
                pass
        if total > 0:
            return round(min(40.0, total), 1)

    return None


def extract_profile(text, sections):
    """
    Extract basic contact and profile information using heuristics.
    Name and headline are identified from introductory lines.
    """
    email_match = re.search(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        text,
        flags=re.IGNORECASE,
    )

    phone_match = re.search(
        r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?"
        r"(?:\(?\d{3,5}\)?[-.\s]?)"
        r"\d{3,5}[-.\s]?\d{3,5}(?!\w)",
        text,
    )

    intro_lines = [
        line.strip()
        for line in sections.get("other", "").splitlines()
        if line.strip()
    ]

    intro_lines = [
        line for line in intro_lines
        if not re.search(r"@|https?://|www\.", line, flags=re.IGNORECASE)
        and not re.search(r"\d{5,}", line)
    ]

    full_name = None
    headline = None

    if intro_lines:
        first_line = intro_lines[0]
        name_pattern = r"[A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){1,3}"
        if re.fullmatch(name_pattern, first_line):
            full_name = first_line
            if len(intro_lines) > 1:
                headline = intro_lines[1]
        else:
            headline = first_line

    summary = sections.get("summary", "")

    return {
        "full_name": full_name,
        "headline": headline,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "summary": summary,
    }


def extract_education(sections):
    return sections.get("education", "")


def extract_experience(sections):
    return sections.get("experience", "")


def analyze_resume(input_file):
    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(f"Input JSON not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        raise ValueError("Input JSON must contain a string field named 'text'.")

    resume_text = data["text"]
    sections = detect_sections(resume_text)
    profile = extract_profile(resume_text, sections)
    skills = find_skills(resume_text)
    evidence = extract_skill_evidence(resume_text, skills)
    experience_years = estimate_experience_years(resume_text)

    warnings = []
    for section in ("education", "skills", "experience", "projects"):
        if not sections.get(section):
            warnings.append(f"Could not identify an explicit {section} section.")

    if not skills:
        warnings.append("No skills from the current vocabulary were found.")

    if not profile["full_name"]:
        warnings.append("Could not confidently identify a candidate name.")

    return {
        "source_file": data.get("file_name", path.name),
        "extraction_method": "dictionary_heading_regex_and_evidence_extraction",
        "profile": profile,
        "skills_found": skills,
        "skill_evidence": evidence,
        "experience_years_detected": experience_years,
        "education_text": extract_education(sections),
        "experience_text": extract_experience(sections),
        "projects_text": sections.get("projects", ""),
        "certifications_text": sections.get("certifications", ""),
        "detected_sections": sections,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured information from parsed resume JSON."
    )
    parser.add_argument("input", help="Path to parsed resume JSON")
    parser.add_argument(
        "--output",
        default="outputs/structured_resume.json",
        help="Path for structured output JSON",
    )
    args = parser.parse_args()

    try:
        result = analyze_resume(args.input)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Analysis complete. Saved to: {output_path}")
        print(f"Name: {result['profile']['full_name'] or 'Not detected'}")
        print(f"Headline: {result['profile']['headline'] or 'Not detected'}")
        print(f"Skills found: {', '.join(result['skills_found']) or 'None'}")
        print(f"Experience years: {result['experience_years_detected'] or 'Unknown'}")
        print(f"Warnings: {len(result['warnings'])}")

    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
