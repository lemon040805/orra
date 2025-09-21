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
        text = body['text']
        refresh_language_globals(user_id)
        source_lang = GLOBAL_NATIVE_LANGUAGE_NAME
        target_lang = GLOBAL_TARGET_LANGUAGE_NAME
        
        # Use Bedrock Nova model for translation
        translated_text = translate_with_bedrock(text, source_lang, target_lang)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'translatedText': translated_text,
                'nativeLanguage': source_lang,
                'targetLanguage': target_lang,
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'amazon_nova_pro'
            })
        }
        
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def translate_with_bedrock(text, source_lang, target_lang):
    # Convert language names to proper format if needed
    
    prompt = f"Translate '{text}' from {source_lang} to {target_lang}. Return only the translation."

    response = bedrock.converse(
        modelId='amazon.nova-pro-v1:0',
        messages=[{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
    )
    
    translation = response['output']['message']['content'][0]['text'].strip()
    
    return translation
