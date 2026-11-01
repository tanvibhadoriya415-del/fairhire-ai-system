import json
import re
import argparse
from pathlib import Path

# Skills the matcher knows how to recognize.
SKILL_VOCABULARY = [
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

SKILL_SYNONYMS = {
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "postgresql": ["postgresql", "postgres"],
    "rest api": ["rest api", "rest apis", "restful api", "restful apis", "restful"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "natural language processing": ["natural language processing", "nlp"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "kubernetes": ["kubernetes", "k8s"],
    "ci/cd": ["ci/cd", "cicd"],
    "power bi": ["power bi", "powerbi"],
    "git": ["git", "github", "gitlab"],
    "aws": ["aws", "amazon web services"],
}


def normalize_skill(skill: str) -> str:
    """Normalize skill names for consistent matching."""
    cleaned = re.sub(r"\s+", " ", skill.strip().lower())
    for canonical, aliases in SKILL_SYNONYMS.items():
        if cleaned in aliases or cleaned == canonical:
            return canonical
    return cleaned


def find_skills(text: str) -> list[str]:
    """Find known skill names in a text block with boundary and synonym checking."""
    found = set()

    for canonical in SKILL_VOCABULARY:
        variants = SKILL_SYNONYMS.get(canonical, [canonical])
        for variant in variants:
            pattern = (
                r"(?<![a-z0-9+#.])"
                + re.escape(variant)
                + r"(?![a-z0-9+#.])"
            )
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.add(canonical)
                break

    return sorted(found)


def extract_job_skills(job_text: str) -> tuple[list[str], list[str]]:
    """
    Extract required and preferred skills from job text.
    Handles multi-line text and single-line form submissions.
    """
    heading_pattern = re.compile(
        r"\b("
        r"job\s+responsibilities|"
        r"responsibilities|"
        r"required\s+skills|"
        r"required|"
        r"preferred\s+skills|"
        r"preferred"
        r")\s*:?",
        flags=re.IGNORECASE,
    )

    headings = list(heading_pattern.finditer(job_text))

    required_text = []
    preferred_text = []

    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(job_text)
        section_text = job_text[start:end]

        heading_name = re.sub(r"\s+", " ", heading.group(1).lower()).strip()

        if heading_name in ("required", "required skills"):
            required_text.append(section_text)
        elif heading_name in ("preferred", "preferred skills"):
            preferred_text.append(section_text)

    # If headings weren't present, extract general skills from whole text as required
    if not required_text and not preferred_text:
        general_skills = find_skills(job_text)
        return general_skills, []

    required_skills = find_skills(" ".join(required_text))
    preferred_skills = find_skills(" ".join(preferred_text))

    return required_skills, preferred_skills


def calculate_match(
    resume_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
    skill_evidence: dict | None = None,
) -> dict:
    """
    Calculate an explainable weighted skill-overlap score.
    Required skills = weight 2
    Preferred skills = weight 1
    """
    resume_set = {normalize_skill(s) for s in resume_skills}
    required_set = {normalize_skill(s) for s in required_skills}
    preferred_set = {normalize_skill(s) for s in preferred_skills}

    matched_required = sorted(resume_set & required_set)
    missing_required = sorted(required_set - resume_set)

    matched_preferred = sorted(resume_set & preferred_set)
    missing_preferred = sorted(preferred_set - resume_set)

    total_weight = (2 * len(required_set)) + len(preferred_set)
    earned_weight = (2 * len(matched_required)) + len(matched_preferred)

    score = (
        round(100.0 * earned_weight / total_weight, 2)
        if total_weight
        else 0.0
    )

    required_coverage = (
        round(100.0 * len(matched_required) / len(required_set), 2)
        if required_set
        else 100.0
    )

    evidence_map = {}
    if skill_evidence:
        for skill in matched_required + matched_preferred:
            evidence_map[skill] = skill_evidence.get(skill, [])

    breakdown = {
        "required_weight": 2,
        "preferred_weight": 1,
        "total_required_skills": len(required_set),
        "matched_required_count": len(matched_required),
        "total_preferred_skills": len(preferred_set),
        "matched_preferred_count": len(matched_preferred),
        "earned_points": earned_weight,
        "possible_points": total_weight,
    }

    return {
        "score_percent": score,
        "required_skill_coverage": required_coverage,
        "scoring_method": "weighted_skill_overlap_baseline",
        "weights": {
            "required_skill": 2,
            "preferred_skill": 1,
        },
        "score_breakdown": breakdown,
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "evidence": evidence_map,
        "explanation": (
            "The score reflects evidence overlap with listed required (weight 2) "
            "and preferred (weight 1) skills. It is an alignment indicator, not a "
            "prediction of job performance. Consequential decisions must remain human-supervised."
        ),
    }


def match_resume_to_job(
    resume_json_path,
    job_description_path,
):
    """Compare structured resume skills with a job description file."""
    resume_path = Path(resume_json_path)
    job_path = Path(job_description_path)

    if not resume_path.exists():
        raise FileNotFoundError(f"Resume analysis JSON not found: {resume_path}")

    if not job_path.exists():
        raise FileNotFoundError(f"Job description not found: {job_path}")

    resume_data = json.loads(resume_path.read_text(encoding="utf-8"))

    if not isinstance(resume_data, dict):
        raise ValueError("Resume analysis JSON must contain a JSON object.")

    resume_skills = resume_data.get("skills_found", [])
    if not isinstance(resume_skills, list):
        raise ValueError("'skills_found' must be a list in resume analysis JSON.")

    evidence = resume_data.get("skill_evidence", {})
    job_text = job_path.read_text(encoding="utf-8")

    required_skills, preferred_skills = extract_job_skills(job_text)

    if not required_skills and not preferred_skills:
        raise ValueError(
            "No known skills found under Required Skills or Preferred Skills. "
            "Check the job description headings and skill vocabulary."
        )

    result = calculate_match(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        skill_evidence=evidence,
    )

    return {
        "candidate_source": resume_data.get("source_file", resume_path.name),
        "job_description_source": job_path.name,
        "resume_skills": sorted({normalize_skill(s) for s in resume_skills}),
        "job_required_skills": required_skills,
        "job_preferred_skills": preferred_skills,
        "matching_results": result,
        "warnings": [
            "This is an evidence-alignment score, not a validated hiring predictor.",
            "Resume-listed skills are not independently verified.",
            "Always use human review and evaluate candidate qualifications holistically.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare extracted resume skills with a job description."
    )
    parser.add_argument("resume", help="Path to structured resume JSON")
    parser.add_argument("job_description", help="Path to job description text file")
    parser.add_argument(
        "--output",
        default="outputs/match_result.json",
        help="Path to save the match result JSON",
    )
    args = parser.parse_args()

    try:
        result = match_resume_to_job(args.resume, args.job_description)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Matching complete. Saved to: {output_path}")
        matching = result["matching_results"]
        print(f"Skill overlap score: {matching['score_percent']}%")
        print(f"Required skill coverage: {matching.get('required_skill_coverage', 'N/A')}%")
        print(f"Matched required skills: {', '.join(matching['matched_required_skills']) or 'None'}")
        print(f"Missing required skills: {', '.join(matching['missing_required_skills']) or 'None'}")

    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
