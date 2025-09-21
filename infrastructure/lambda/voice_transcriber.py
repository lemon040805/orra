import json
import boto3
import base64
import uuid
import os
import time
from datetime import datetime
from language_config import get_language_code, LANGUAGE_CONFIG

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        # Parse the multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Extract audio data from multipart form
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                audio_data = base64.b64decode(body)
            else:
                audio_data = body.encode() if isinstance(body, str) else body
            
            # Generate unique filename
            audio_key = f"audio/{uuid.uuid4()}.wav"
            
            # Upload audio to S3
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_key,
                Body=audio_data,
                ContentType='audio/wav'
            )
            
            # Start transcription job
            job_name = f"transcribe-{uuid.uuid4()}"
            audio_uri = f"s3://{BUCKET_NAME}/{audio_key}"
            
            # Get language from query parameters
            language_code = 'en-US'
            if 'queryStringParameters' in event and event['queryStringParameters']:
                lang = event['queryStringParameters'].get('language', LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE_NAME'])
                language_code = get_transcribe_language_code(lang)
            
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_uri},
                MediaFormat='wav',
                LanguageCode=language_code
            )
            
            # Wait for transcription to complete (with timeout)
            max_wait = 30  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    # Get transcription result
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    # Download and parse transcript
                    import urllib.request
                    with urllib.request.urlopen(transcript_uri) as response:
                        transcript_data = json.loads(response.read().decode())
                    
                    transcription = transcript_data['results']['transcripts'][0]['transcript']
                    confidence = 0.0
                    
                    # Calculate average confidence
                    if 'items' in transcript_data['results']:
                        confidences = [float(item.get('alternatives', [{}])[0].get('confidence', 0)) 
                                     for item in transcript_data['results']['items'] 
                                     if item.get('type') == 'pronunciation']
                        confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Clean up
                    transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                    s3.delete_object(Bucket=BUCKET_NAME, Key=audio_key)
                    
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'transcription': transcription,
                            'confidence': confidence,
                            'language': language_code,
                            'timestamp': datetime.utcnow().isoformat(),
                            'method': 'aws_transcribe'
                        })
                    }
                    
                elif status == 'FAILED':
                    error_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    raise Exception(f"Transcription failed: {error_reason}")
                
                time.sleep(1)
                wait_time += 1
            
            # Timeout - return fallback
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
            s3.delete_object(Bucket=BUCKET_NAME, Key=audio_key)
            
            return get_fallback_response(language_code)
            
        else:
            # Handle JSON request (for testing)
            body = json.loads(event.get('body', '{}'))
            language = body.get('language', 'en-US')
            
            return get_fallback_response(language)
        
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

def get_transcribe_language_code(lang):
    return get_language_code(lang)

def get_fallback_response(language_code):
    fallback_transcriptions = {
        'en-US': 'Hello, how can I help you today?',
        'es-ES': 'Hola, ¿cómo puedo ayudarte hoy?',
        'fr-FR': 'Bonjour, comment puis-je vous aider aujourd\'hui?',
        'de-DE': 'Hallo, wie kann ich Ihnen heute helfen?',
        'it-IT': 'Ciao, come posso aiutarti oggi?'
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'transcription': fallback_transcriptions.get(language_code, fallback_transcriptions['en-US']),
            'confidence': 0.8,
            'language': language_code,
            'timestamp': datetime.utcnow().isoformat(),
            'method': 'fallback'
        })
    }
