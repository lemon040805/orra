import json
import boto3
from datetime import datetime

translate = boto3.client('translate')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        text = body['text']
        source_lang = body['sourceLanguage']
        target_lang = body['targetLanguage']
        
        # Use AWS Translate
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'translatedText': response['TranslatedText'],
                'sourceLanguage': source_lang,
                'targetLanguage': target_lang,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        # Fallback translations
        fallback_translations = {
            'hello': {'es': 'hola', 'fr': 'bonjour', 'de': 'hallo', 'it': 'ciao'},
            'goodbye': {'es': 'adiós', 'fr': 'au revoir', 'de': 'auf wiedersehen', 'it': 'ciao'},
            'thank you': {'es': 'gracias', 'fr': 'merci', 'de': 'danke', 'it': 'grazie'},
            'please': {'es': 'por favor', 'fr': 's\'il vous plaît', 'de': 'bitte', 'it': 'per favore'}
        }
        
        body = json.loads(event['body'])
        text = body['text'].lower()
        target_lang = body['targetLanguage']
        
        translated = fallback_translations.get(text, {}).get(target_lang, f'[Translation of: {text}]')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'translatedText': translated,
                'sourceLanguage': body['sourceLanguage'],
                'targetLanguage': target_lang,
                'timestamp': datetime.utcnow().isoformat(),
                'fallback': True
            })
        }
