import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        topic = body.get('topic', 'daily conversation')
        
        # Get user's profile from database
        users_table = dynamodb.Table('language-learning-users')
        user_response = users_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'User profile not found'})
            }
        
        user_data = user_response['Item']
        
        # Use user's saved language settings and proficiency
        target_language = user_data.get('targetLanguage', 'Spanish')
        native_language = user_data.get('nativeLanguage', 'English')
        difficulty_level = user_data.get('finalLevel', 'Intermediate')
        weak_areas = user_data.get('weakAreas', [])
        
        # Generate lesson using user's actual proficiency
        lesson = generate_bedrock_lesson(
            target_language, native_language, topic, 
            difficulty_level, weak_areas
        )
        
        # Store lesson in database
        lesson_id = str(uuid.uuid4())
        lessons_table = dynamodb.Table('language-learning-lessons')
        lesson_item = {
            'lessonId': lesson_id,
            'userId': user_id,
            'targetLanguage': target_language,
            'nativeLanguage': native_language,
            'topic': topic,
            'difficultyLevel': difficulty_level,
            'lesson': lesson,
            'createdAt': datetime.utcnow().isoformat(),
            'completed': False
        }
        
        lessons_table.put_item(Item=lesson_item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'lessonId': lesson_id,
                'lesson': lesson,
                'userProficiency': difficulty_level,
                'targetLanguage': target_language,
                'method': 'aws_bedrock_auto_proficiency'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def generate_bedrock_lesson(target_language, native_language, topic, level, weak_areas):
    focus_areas = f"Pay special attention to: {', '.join(weak_areas)}" if weak_areas else ""
    
    prompt = f"""Create a comprehensive {target_language} lesson for a {level} learner whose native language is {native_language}.

Topic: {topic}
{focus_areas}

Create a detailed JSON lesson with this exact structure:
{{
    "title": "Engaging lesson title",
    "content": "Main lesson content (3-4 paragraphs) with explanations and examples",
    "vocabulary": [
        {{"word": "target word", "translation": "native translation", "pronunciation": "phonetic", "example": "example sentence"}},
        {{"word": "target word 2", "translation": "native translation 2", "pronunciation": "phonetic 2", "example": "example sentence 2"}}
    ],
    "grammar_focus": "Key grammar point with clear explanation",
    "cultural_note": "Cultural insight related to the topic",
    "exercises": [
        "Practice exercise 1",
        "Practice exercise 2", 
        "Practice exercise 3"
    ],
    "phrases": [
        {{"phrase": "useful phrase", "translation": "translation", "context": "when to use"}},
        {{"phrase": "useful phrase 2", "translation": "translation 2", "context": "when to use 2"}}
    ]
}}

Generate 8-10 vocabulary words and 5-6 phrases. Make it practical for {level} level."""

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
        print(f"Bedrock error: {e}")
        raise Exception(f"Failed to generate lesson: {str(e)}")
