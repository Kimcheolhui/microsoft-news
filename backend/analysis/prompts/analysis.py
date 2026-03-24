"""Prompt templates for the analysis step."""

ANALYSIS_SYSTEM_PROMPT = """\
You are an Azure cloud services analyst. Your job is to analyze Azure updates \
and produce structured analysis results including:
- Update type classification (new_feature, retirement, preview, ga, update)
- Affected services identification
- Impact assessment
- Key technical details
"""

ANALYSIS_USER_TEMPLATE = """\
Analyze the following Azure update:

Title: {title}
Published: {published_date}
Source URL: {source_url}

Content:
{content}

Related Updates:
{related_updates}

Provide a structured JSON analysis with the following fields:
- update_type: one of (new_feature, retirement, preview, ga, update)
- affected_services: list of Azure service names
- impact_summary: brief impact description
- key_details: list of important technical details
- action_items: list of recommended actions for users
"""
