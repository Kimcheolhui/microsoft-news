"""Prompt templates for the report writing step."""

WRITING_SYSTEM_PROMPT = """\
You are a technical writer specializing in Azure cloud services. \
You write clear, actionable reports about Azure updates in both Korean and English. \
Your reports are concise yet thorough, targeting cloud architects and DevOps engineers.
"""

WRITING_USER_TEMPLATE = """\
Based on the following analysis, write a report in both Korean and English.

Analysis:
{analysis_json}

Original Update Title: {title}
Published: {published_date}

For each language, provide:
1. A concise title
2. A 2-3 sentence summary
3. A full report body with sections:
   - Overview
   - Impact & Affected Services
   - Key Details
   - Recommended Actions
   - References

Output as JSON with fields: title_ko, title_en, summary_ko, summary_en, body_ko, body_en
"""
