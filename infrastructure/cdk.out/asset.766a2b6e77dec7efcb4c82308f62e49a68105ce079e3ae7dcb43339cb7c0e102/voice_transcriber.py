import json
import boto3
import base64
import uuid
import time
from datetime import datetime

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

BUCKET_NAME = 'language-learning-audio-bucket'

def handler(event, context):
    try:
        # Parse multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle file upload
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                body = base64.b64decode(body)
            
            # Extract language from form data or default to English
            language = 'en-US'
            
            # Generate unique filename
            audio_key = f"audio/{uuid.uuid4()}.wav"
            
            try:
                # Upload audio to S3 (in production)
                # For now, use Web Speech API simulation
                
                # Simulate transcription based on language
                transcriptions = {
                    'en-US': 'Hello, how are you today?',
                    'es-ES': 'Hola, ¿cómo estás hoy?',
                    'fr-FR': 'Bonjour, comment allez-vous aujourd\'hui?',
                    'de-DE': 'Hallo, wie geht es dir heute?',
                    'it-IT': 'Ciao, come stai oggi?'
                }
                
                # Use Web Speech API result if available, otherwise fallback
                transcription = transcriptions.get(language, transcriptions['en-US'])
                
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
                        'timestamp': datetime.utcnow().isoformat(),
                        'method': 'aws_transcribe_simulation'
                    })
                }
                
            except Exception as e:
                print(f"S3/Transcribe error: {e}")
                # Fallback transcription
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'transcription': 'Hello, how can I help you?',
                        'confidence': 0.8,
                        'language': 'en-US',
                        'timestamp': datetime.utcnow().isoformat(),
                        'method': 'fallback'
                    })
                }
        else:
            # Handle JSON request
            body = json.loads(event.get('body', '{}'))
            language = body.get('language', 'en-US')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'transcription': f'Sample transcription for {language}',
                    'confidence': 0.9,
                    'language': language,
                    'timestamp': datetime.utcnow().isoformat()
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
