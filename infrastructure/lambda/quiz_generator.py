import json
import boto3
from datetime import datetime

from language_config import (
    refresh_language_globals,
    GLOBAL_NATIVE_LANGUAGE_NAME,
    GLOBAL_TARGET_LANGUAGE_NAME,
)

bedrock = boto3.client('bedrock-runtime')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId'] 

        refresh_language_globals(user_id)

        target_language=GLOBAL_TARGET_LANGUAGE_NAME
        native_language=GLOBAL_NATIVE_LANGUAGE_NAME
        level = body.get('difficulty', body.get('level', 'beginner'))
        question_count = body.get('questionCount', 10)
        
        # Generate quiz using Bedrock
        quiz = generate_bedrock_quiz(target_language, native_language, level, question_count)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'questions': quiz,
                'level': level,
                'generatedAt': datetime.utcnow().isoformat(),
                'method': 'amazon_nova_pro'
            })
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

def generate_bedrock_quiz(target_language, native_language, level, question_count):
    prompt = f"""Generate exactly {question_count} multiple choice questions to assess {level} level {target_language} proficiency for a {native_language} speaker.

Requirements:
- Each question must have exactly 4 options
- Include "I don't know" as the 4th option for every question
- Questions should test vocabulary, grammar, and practical usage
- Difficulty appropriate for {level} level

Return ONLY a JSON array with this exact format:
[
  {{
    "question": "Question text here",
    "options": ["Correct answer", "Wrong answer 1", "Wrong answer 2", "I don't know"],
    "correct": 0
  }}
]

Generate {question_count} questions for {level} {target_language}:"""

    response = bedrock.converse(
        modelId='amazon.nova-pro-v1:0',
        messages=[{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
    )
    
    quiz_content = response['output']['message']['content'][0]['text'].strip()
    
    # Clean JSON response
    if quiz_content.startswith('```json'):
        quiz_content = quiz_content[7:]
    if quiz_content.endswith('```'):
        quiz_content = quiz_content[:-3]
    quiz_content = quiz_content.strip()
    
    quiz_data = json.loads(quiz_content)
    
    # Ensure "I don't know" option
    for question in quiz_data:
        if len(question['options']) < 4:
            question['options'].append("I don't know")
        elif question['options'][3] != "I don't know":
            question['options'][3] = "I don't know"
    
    return quiz_data[:question_count]
