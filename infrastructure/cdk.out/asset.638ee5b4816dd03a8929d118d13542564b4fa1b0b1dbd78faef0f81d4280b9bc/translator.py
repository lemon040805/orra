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
                'sourceLanguage': source_lang,
                'targetLanguage': target_lang,
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'aws_bedrock_nova'
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
    
    prompt = f"Translate '{text}' from {source_name} to {target_name}. Return only the translation."

    response = bedrock.converse(
        modelId='amazon.nova-pro-v1:0',
        messages=[{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
    )
    
    translation = response['output']['message']['content'][0]['text'].strip()
    
    return translation
