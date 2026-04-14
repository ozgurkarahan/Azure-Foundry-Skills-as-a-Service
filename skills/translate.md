# Skill: Translate

## Purpose
Translate text between languages while preserving meaning, tone, and formatting.

## When to Use
- User asks to translate text to/from any language
- User provides text in one language and wants it in another
- User asks for a localized version of content

## Instructions

1. Detect the source language (or use the one specified by the user)
2. Translate to the target language specified by the user
3. Preserve the original formatting (markdown, bullet points, headings)
4. Maintain the tone and register (formal/informal/technical)

## Output Format

**Source language:** {detected or specified}
**Target language:** {specified by user}

---

{translated text, preserving original formatting}

---

**Translation notes:** (only if relevant)
- Flag any terms that don't have a direct translation
- Note cultural adaptations made

## Rules
- If the target language is not specified, ask the user
- Preserve all proper nouns, brand names, and technical terms unless the user asks to localize them
- For technical documents, prefer accuracy over fluency
- For marketing/creative text, prefer fluency over literal translation
- Never add content not present in the original
- If the text contains code blocks, leave code unchanged — only translate comments and strings
