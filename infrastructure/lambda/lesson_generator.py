import json, boto3, uuid
from datetime import datetime
from decimal import Decimal

from language_config import (
    refresh_language_globals,
    GLOBAL_NATIVE_LANGUAGE_NAME,
    GLOBAL_TARGET_LANGUAGE_NAME,
)

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']  # required; no defaults allowed
        topic = body.get('topic', 'daily conversation')

        # IMPORTANT: set globals for *this* request's user
        refresh_language_globals(user_id)

        users_table = dynamodb.Table('language-learning-users')
        user_response = users_table.get_item(Key={'userId': user_id})
        item = user_response.get('Item') or {}
        proficiency = (item.get('proficiency') or 'beginner')

        lesson = generate_bedrock_lesson(
            target_language=GLOBAL_TARGET_LANGUAGE_NAME,
            native_language=GLOBAL_NATIVE_LANGUAGE_NAME,
            topic=topic,
            level=proficiency,
            weak_areas=item.get('weakAreas', []),
        )

        lesson_id = str(uuid.uuid4())
        lessons_table = dynamodb.Table('language-learning-lessons')
        lessons_table.put_item(Item={
            'lessonId': lesson_id,
            'userId': user_id,
            'targetLanguage': GLOBAL_TARGET_LANGUAGE_NAME,
            'nativeLanguage': GLOBAL_NATIVE_LANGUAGE_NAME,
            'topic': topic,
            'difficultyLevel': proficiency,
            'lesson': lesson,
            'createdAt': datetime.utcnow().isoformat(),
            'completed': False
        })

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'lessonId': lesson_id,
                'lesson': lesson,
                'userProficiency': proficiency,
                'targetLanguage': GLOBAL_TARGET_LANGUAGE_NAME,
                'method': 'amazon_nova_pro',
            }, cls=DecimalEncoder),
        }
    except KeyError as e:
        return _bad_request(f"Missing required field: {e}")
    except ValueError as e:
        return _bad_request(str(e))
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error'}),
        }

def _bad_request(msg: str):
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': msg})
    }

def generate_bedrock_lesson(target_language, native_language, topic, level, weak_areas):
    focus_areas = f"Pay special attention to: {', '.join(weak_areas)}" if weak_areas else ""
    
    prompt = f"""
You are an expert {target_language} lesson designer for a mobile language learning app (like Duolingo).
Design a CEFR-aligned lesson for a {level} learner whose native language is {native_language}.
The lesson must be engaging, realistic, and PRACTICAL for mobile practice (short tasks, tap/drag/select, sentence completion, multiple choice). 
Avoid tasks that are unrealistic for a phone (e.g., reading long books, filming vlogs). 

Topic: {topic}
Focus areas: {focus_areas}

OUTPUT FORMAT (strict):
Return ONLY a single valid JSON object with this EXACT structure and keys:
{{
  "title": "Engaging lesson title",
  "content": "3–4 short learner-friendly paragraphs (max 5 sentences each) explaining the topic with examples by using {native_language}",
  "vocabulary": [
    {{"word": "target word", "translation": "native translation", "pronunciation": "IPA or phonetic", "example": "short example sentence"}}
  ],
  "grammar_focus": "One key grammar point with 1–2 clear examples",
  "cultural_note": "Brief cultural insight directly tied to the topic",
  "exercises": [
    "Mobile-friendly task 1 (multiple choice, fill-in-the-blank, reorder words, or short translation)",
    "Mobile-friendly task 2",
    "Mobile-friendly task 3"
  ],
  "phrases": [
    {{"phrase": "useful phrase", "translation": "translation", "context": "when to use"}}
  ]
}}

QUANTITY RULES:
- Vocabulary: 8–10 useful words tied to the Topic. Each has an example sentence the learner could realistically say.
- Phrases: 5–6 natural phrases (short, everyday, level-appropriate).
- Exercises: exactly 3, realistic for a phone: (e.g., choose the correct answer, drag words into order, short gap-fill, select the matching translation).
- Content length: 
  - A1–A2: 180–250 words total
  - B1–B2: 220–300 words total
  - C1: 250–350 words total

LEVEL RULES:
- A1: very short, simple sentences; basic survival words; present tense.
- A2: simple past/future, frequent connectors (“and, but, because”).
- B1: longer sentences with common phrasal verbs/collocations.
- B2: natural collocations, wider vocabulary, discourse markers.
- C1: idiomatic, nuanced, formal/informal register awareness.

PRONUNCIATION:
- Always use IPA or the standard system for {target_language}.
- Show stress/tones if relevant.

CULTURAL NOTE:
- Must be short, practical, and tied to the topic (e.g., polite forms in greetings, tipping habits in cafés).

FINAL VALIDATION:
- Return ONLY the JSON object (no markdown, no explanation).
- Ensure counts are correct: 8–10 vocabulary items, 5–6 phrases, 3 exercises, 3–4 short paragraphs.
"""

    try:
        response = bedrock.converse(
            modelId='amazon.nova-pro-v1:0',
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }]
        )
        
        lesson_content = response['output']['message']['content'][0]['text'].strip()
        
        # Clean JSON response
        if lesson_content.startswith('```json'):
            lesson_content = lesson_content[7:]
        if lesson_content.endswith('```'):
            lesson_content = lesson_content[:-3]
        lesson_content = lesson_content.strip()
        
        lesson_data = json.loads(lesson_content)
        return lesson_data
            
    except Exception as e:
        print(f"Nova error: {e}")
        raise Exception(f"Failed to generate lesson: {str(e)}")
