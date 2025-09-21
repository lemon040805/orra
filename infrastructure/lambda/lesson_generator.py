import json
import boto3
import os
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        topic = body.get('topic', 'greetings')
        
        # Get user profile for language preferences
        user_id = body.get('userId')
        target_lang = body.get('targetLanguage', 'Spanish')
        native_lang = body.get('sourceLanguage', 'English')
        
        if user_id:
            try:
                import boto3
                dynamodb = boto3.resource('dynamodb')
                users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'language-learning-users'))
                response = users_table.get_item(Key={'userId': user_id})
                if 'Item' in response:
                    target_lang = response['Item'].get('targetLanguage', target_lang)
                    native_lang = response['Item'].get('nativeLanguage', native_lang)
            except:
                pass
        
        # Use Nova Pro with user's languages
        prompt = f'''Create a {target_lang} lesson about "{topic}" for beginners. Translate to {native_lang}. Return ONLY valid JSON:
{{
  "title": "lesson title",
  "content": "lesson description",
  "vocabulary": [
    {{"{target_lang.lower()}_word": "{target_lang} word", "translation": "{native_lang} translation"}}
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
                'targetLanguage': target_lang,
                'nativeLanguage': native_lang
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