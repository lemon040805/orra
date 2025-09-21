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
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'aws_translate'
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
