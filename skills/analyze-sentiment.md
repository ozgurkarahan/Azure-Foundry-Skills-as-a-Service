# Skill: Analyze Sentiment

## Purpose
Analyze the sentiment, emotional tone, and key themes in text such as reviews, feedback, emails, or social media posts.

## When to Use
- User asks about the sentiment or tone of text
- User wants to understand customer feedback trends
- User asks to categorize reviews or comments by sentiment

## Instructions

1. Read the full input text
2. Classify the overall sentiment: Positive, Negative, Neutral, or Mixed
3. Identify specific emotions expressed (e.g., frustration, satisfaction, urgency, enthusiasm)
4. Extract key themes or topics mentioned
5. Provide a confidence level for the classification

## Output Format

**Overall Sentiment:** {Positive / Negative / Neutral / Mixed}
**Confidence:** {High / Medium / Low}

**Emotions Detected:**
- {emotion 1} — supporting quote or evidence
- {emotion 2} — supporting quote or evidence

**Key Themes:**
- {theme 1} — brief context
- {theme 2} — brief context

**Summary:** One-sentence interpretation of the overall sentiment and its implications.

## Rules
- Always cite specific phrases from the text as evidence
- If analyzing multiple items (e.g., a batch of reviews), provide per-item analysis AND an aggregate summary
- Distinguish between sentiment directed at the product/service vs sentiment about the experience
- Flag sarcasm or irony when detected (with Low confidence)
- Never inject your own opinion — report what the text expresses
