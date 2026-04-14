---
name: summarize
version: "1.0"
tags: [text-processing, productivity]
dependencies: []
---

# Skill: Summarize

## Purpose
Summarize documents, emails, meeting notes, or any text into concise, actionable output.

## When to Use
- User asks to summarize, condense, or give a TL;DR of content
- User provides a long document and wants key points
- User asks for an executive summary or brief

## Instructions

1. Read the full input text provided by the user
2. Identify the key themes, decisions, action items, and conclusions
3. Produce a summary in the requested format (default: bullet points)

## Output Format

### Default (Bullet Points)
- **Key point 1** — brief explanation
- **Key point 2** — brief explanation
- **Action items:** list any next steps mentioned

### If user requests a paragraph
Write a concise paragraph (3-5 sentences) covering the main points.

### If user requests an executive summary
- **Context:** one sentence on what this is about
- **Key findings:** 3-5 bullet points
- **Recommendation / Next steps:** what should happen next

## Dependencies
- If the user asks for a summary of translated content, first use the **Translate** skill, then summarize the result.

## Rules
- Never add information not present in the source
- Preserve the original tone (formal stays formal, casual stays casual)
- If the text is under 100 words, tell the user it's already concise
- Cap summaries at 30% of the original length
