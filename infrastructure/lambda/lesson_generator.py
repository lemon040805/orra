import json
import boto3
import os
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        topic = body.get('topic', 'greetings')
        
        # Use Nova Pro
        prompt = f'''Create a Spanish lesson about "{topic}" for beginners. Return ONLY valid JSON:
{{
  "title": "lesson title",
  "content": "lesson description",
  "vocabulary": [
    {{"word": "spanish_word", "translation": "english_translation"}}
  ],
  "cultural_note": "cultural information",
  "exercises": ["exercise 1", "exercise 2"]
}}'''
        
        response = bedrock.converse(
            modelId='amazon.nova-pro-v1:0',
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }]
        )
        
        lesson_text = response['output']['message']['content'][0]['text'].strip()
        lesson = json.loads(lesson_text)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'lesson': lesson,
                'userProficiency': 'Beginner',
                'targetLanguage': 'Spanish'
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