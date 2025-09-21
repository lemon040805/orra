import json
import boto3
import base64
import uuid
import os
import time
from datetime import datetime
from language_config import (
    refresh_language_globals,
    GLOBAL_NATIVE_LANGUAGE_NAME,
    GLOBAL_TARGET_LANGUAGE_NAME,
    GLOBAL_NATIVE_LANGUAGE,
    get_language_code
)

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Parse multipart form data
            boundary = content_type.split('boundary=')[1]
            body = event.get('body', '')
            
            if event.get('isBase64Encoded', False):
                body = base64.b64decode(body).decode('utf-8')
            
            # Extract form fields
            parts = body.split('--' + boundary)
            audio_data = None
            user_id = None
            language = None
            
            for part in parts:
                if 'Content-Disposition: form-data; name="audio"' in part:
                    # Extract audio data
                    audio_start = part.find('\r\n\r\n') + 4
                    audio_end = part.rfind('\r\n')
                    if audio_start < audio_end:
                        audio_data = part[audio_start:audio_end].encode('latin1')
                elif 'Content-Disposition: form-data; name="userId"' in part:
                    user_id = part.split('\r\n\r\n')[1].split('\r\n')[0]
                elif 'Content-Disposition: form-data; name="language"' in part:
                    language = part.split('\r\n\r\n')[1].split('\r\n')[0]
            
            if not audio_data or not user_id:
                raise Exception("Missing audio data or user ID")
            
            # Refresh language globals
            refresh_language_globals(user_id)
            
            # Use provided language or default to native language
            language_code = get_language_code(language or GLOBAL_NATIVE_LANGUAGE)
            
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
            
            # Timeout - clean up and return fallback
            try:
                transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                s3.delete_object(Bucket=BUCKET_NAME, Key=audio_key)
            except:
                pass
            
            return get_fallback_response(language_code)
            
        else:
            # Handle JSON request (for testing)
            body = json.loads(event.get('body', '{}'))
            language = body.get('language', 'en-US')
            user_id = body.get('userId')
            
            if user_id:
                refresh_language_globals(user_id)
            
            return get_fallback_response(language)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return get_fallback_response('en-US')


def get_fallback_response(language_code):
    fallback_transcriptions = {
        'en-US': 'Hello, how can I help you today?',
        'ms-MY': 'Selamat datang, bagaimana saya boleh membantu anda?',
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
