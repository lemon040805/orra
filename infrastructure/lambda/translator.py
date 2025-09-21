import json
import boto3
from datetime import datetime
from language_config import get_language_name, LANGUAGE_CONFIG

bedrock = boto3.client('bedrock-runtime')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        text = body['text']
        source_lang = body.get('nativeLanguageName', body.get('nativeLanguage', LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE_NAME']))
        target_lang = body.get('targetLanguageName', body.get('targetLanguage', LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE_NAME']))
        
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
    source_name = source_lang if source_lang in LANGUAGE_CONFIG['SUPPORTED_LANGUAGES'].values() else get_language_name(source_lang)
    target_name = target_lang if target_lang in LANGUAGE_CONFIG['SUPPORTED_LANGUAGES'].values() else get_language_name(target_lang)
    
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
