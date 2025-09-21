import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        text = body['text']
        source_lang = body['sourceLanguage']
        target_lang = body['targetLanguage']
        
        # Use Bedrock for translation since AWS Translate is blocked
        translated_text = translate_with_bedrock(text, source_lang, target_lang)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'translatedText': translated_text,
                'sourceLanguage': source_lang,
                'targetLanguage': target_lang,
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'aws_bedrock_translation'
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
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French', 
        'de': 'German',
        'it': 'Italian'
    }
    
    source_name = language_names.get(source_lang, source_lang)
    target_name = language_names.get(target_lang, target_lang)
    
    prompt = f"""Translate the following {source_name} text to {target_name}. 
Return only the translation, no explanation or additional text.

Text to translate: "{text}"

Translation:"""

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 200,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    result = json.loads(response['body'].read())
    translation = result['content'][0]['text'].strip()
    
    # Clean up any extra formatting
    translation = translation.replace('"', '').strip()
    
    return translation
