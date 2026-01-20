"""
Auto-generate general knowledge quiz questions about media literacy using AI
Uses DeepSeek API to create random, diverse questions
"""

import random
import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI


def generate_quiz_from_analysis(
    article_id: str = None,
    title: str = None,
    sentiment_result: Optional[Dict] = None,
    emotion_result: Optional[Dict] = None,
    propaganda_result: Optional[Dict] = None,
    factcheck_result: Optional[List] = None,
    question_type: str = "bias"
) -> List[Dict[str, Any]]:
    """
    Generate random general knowledge quiz questions about media literacy using AI
    Independent of any specific article.
    
    Returns:
        List of 5 randomly generated quiz questions for the specified category
    """
    questions = generate_ai_quiz_questions(num_questions=5, question_type=question_type)
    return questions


def generate_ai_quiz_questions(num_questions: int = 5, question_type: str = "bias") -> List[Dict[str, Any]]:
    """Use Groq AI to generate category-specific quiz questions"""
    
    api_key = os.getenv('API_KEYDS')
    if not api_key:
        raise Exception("Groq API key not found")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"  # Groq API endpoint
    )
    
    # Category-specific topics mapping
    topic_map = {
        "bias": [
            "identifying political bias in news headlines",
            "detecting slanted reporting and biased language",
            "recognizing one-sided news coverage",
            "spotting selective reporting and cherry-picked facts",
            "finding left-wing and right-wing bias in articles"
        ],
        "sentiment": [
            "comparing tone: uplifting vs downbeat (not political lean)",
            "identifying optimistic vs pessimistic language choices",
            "spotting words with strong positive vs negative emotional weight",
            "recognizing hopeful vs fearful sentiment regardless of topic",
            "detecting enthusiastic vs critical tone in coverage"
        ],
        "emotion": [
            "identifying emotional manipulation in news",
            "detecting emotional hooks in headlines",
            "recognizing fear-based language",
            "spotting appeals to emotion in articles",
            "finding emotional exploitation tactics"
        ],
        "propaganda": [
            "recognizing propaganda techniques (bandwagon, fear appeal, appeal to patriotism)",
            "detecting name-calling and ad hominem attacks",
            "spotting glittering generalities and vague claims",
            "identifying appeal to authority propaganda",
            "finding loaded language and framing in news"
        ],
        "personality": [
            "news consumer personality types and habits",
            "media consumption styles and preferences",
            "identifying your news consumption approach",
            "understanding different ways people consume news",
            "recognizing news consumer archetypes"
        ]
    }
    
    # Get topics for the specific question type, default to bias if not found
    topics = topic_map.get(question_type, topic_map["bias"])
    selected_topics = random.sample(topics, min(num_questions, len(topics)))
    
    # Different prompts for personality vs analysis categories
    if question_type == "personality":
        prompt = f"""Generate {num_questions} multiple-choice quiz questions about news consumption personality types.

Topics to cover (one question per topic):
{chr(10).join([f"- {t}" for t in selected_topics])}

Requirements:
1. Ask about personal news consumption habits and preferences
2. Provide 4 descriptive answer options (A, B, C, D)
3. Each option should describe a different news consumer behavior/personality
4. No "correct" answer - each maps to a personality type
5. Use engaging, relatable scenarios
6. Add a brief debrief explaining what each answer reveals

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "How do you typically consume news?",
    "options": ["I scroll through social media for trending stories", "I read full articles from trusted sources", "I watch TV news broadcasts", "I rely on friends and family to tell me important news"],
    "answer": [0],
    "debrief": "Your news consumption style reflects how you prioritize speed vs depth in staying informed."
  }}
]"""
    else:
        # Build base prompt
        prompt = f"""Generate {num_questions} multiple-choice quiz questions about {question_type.upper()} detection for media literacy.

Topics to cover:
{chr(10).join([f"- {t}" for t in selected_topics])}

Instructions:
1. Focus ONLY on {question_type.upper()} - not other categories
2. Each question should test media literacy concepts
3. Format questions with embedded headlines/scenarios using line breaks
4. Provide options as simple labels: ["A", "B", "Both"] or ["A", "B", "C", "Both A & B"]
5. Provide the correct answer as an index (0=first, 1=second, etc.)
6. Add a 2-3 sentence debrief explaining the answer"""
        
        if question_type == "sentiment":
            prompt += """\n7. CRITICAL FOR SENTIMENT: Do NOT test political bias (left-wing/right-wing). Test emotional tone differences (positive/negative, optimistic/pessimistic, uplifting/critical). Both options must cover the same topic with different emotional tones only."""
        
        prompt += f"""

Return ONLY valid JSON array (no markdown, no extra text):
[
  {{
    "question": "Which headline is more positive in tone? \\n A: 'Headline text' \\n B: 'Headline text'",
    "options": ["A", "B", "Both"],
    "answer": [0],
    "debrief": "Explanation here."
  }}
]"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Groq's smaller, faster Llama model (uses fewer tokens)
        messages=[
            {"role": "system", "content": f"You are an expert in {question_type} detection and media literacy. Generate engaging, accurate quiz questions about {question_type} that follow the JSON structure exactly. Always return ONLY valid JSON, no extra text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON if wrapped in markdown code blocks
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    
    # Try to parse JSON, handling potential control character issues
    try:
        questions = json.loads(content)
    except json.JSONDecodeError as e:
        # If there are invalid control characters, try to fix them
        # Replace literal newlines/tabs within string values (after colons/commas) but not in structure
        import re
        # Remove only truly invalid control characters (not space, tab, newline, carriage return)
        # Keep \n for intentional line breaks in the JSON
        content_fixed = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', content)
        try:
            questions = json.loads(content_fixed)
        except json.JSONDecodeError as e2:
            # Last resort: try to fix by escaping unescaped quotes and newlines in values
            print(f"ERROR parsing {question_type} JSON: {e}")
            print(f"Response content (first 500 chars): {content[:500]}")
            raise
    
    return questions[:num_questions]