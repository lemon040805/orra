import json
import boto3
import base64
import uuid
from datetime import datetime

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

def handler(event, context):
    try:
        # For demo purposes, return mock transcription
        # In production, this would process the audio file
        
        language = 'en'  # Default
        if 'queryStringParameters' in event and event['queryStringParameters']:
            language = event['queryStringParameters'].get('language', 'en')
        
        # Mock transcriptions based on language
        mock_transcriptions = {
            'en': 'Hello, how are you today?',
            'es': 'Hola, ¿cómo estás hoy?',
            'fr': 'Bonjour, comment allez-vous aujourd\'hui?',
            'de': 'Hallo, wie geht es dir heute?',
            'it': 'Ciao, come stai oggi?'
        }
        
        transcription = mock_transcriptions.get(language, mock_transcriptions['en'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'transcription': transcription,
                'confidence': 0.95,
                'language': language,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
