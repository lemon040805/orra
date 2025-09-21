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
    GLOBAL_TARGET_LANGUAGE,
    get_language_code
)

transcribe = boto3.client('transcribe')
polly = boto3.client('polly')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        # Handle multipart form data for voice practice
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
            target_language = None
            
            for part in parts:
                if 'Content-Disposition: form-data; name="audio"' in part:
                    # Extract audio data
                    audio_start = part.find('\r\n\r\n') + 4
                    audio_end = part.rfind('\r\n')
                    if audio_start < audio_end:
                        audio_data = part[audio_start:audio_end].encode('latin1')
                elif 'Content-Disposition: form-data; name="userId"' in part:
                    user_id = part.split('\r\n\r\n')[1].split('\r\n')[0]
                elif 'Content-Disposition: form-data; name="targetLanguage"' in part:
                    target_language = part.split('\r\n\r\n')[1].split('\r\n')[0]
            
            if not audio_data or not user_id:
                raise Exception("Missing audio data or user ID")
            
            # Refresh language globals
            refresh_language_globals(user_id)
            
            # Use target language for transcription
            language_code = get_language_code(target_language or GLOBAL_TARGET_LANGUAGE)
            
            # Upload to S3
            audio_key = f"pronunciation/{uuid.uuid4()}.wav"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_key,
                Body=audio_data,
                ContentType='audio/wav'
            )
            
            # Start transcription
            job_name = f"pronunciation-{uuid.uuid4()}"
            audio_uri = f"s3://{BUCKET_NAME}/{audio_key}"
            
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_uri},
                MediaFormat='wav',
                LanguageCode=language_code
            )
            
            # Wait for completion
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    import urllib.request
                    with urllib.request.urlopen(transcript_uri) as resp:
                        transcript_data = json.loads(resp.read().decode())
                    
                    transcription = transcript_data['results']['transcripts'][0]['transcript']
                    
                    # Calculate confidence
                    confidence = 0.0
                    if 'items' in transcript_data['results']:
                        confidences = [float(item.get('alternatives', [{}])[0].get('confidence', 0)) 
                                     for item in transcript_data['results']['items'] 
                                     if item.get('type') == 'pronunciation']
                        confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    feedback = generate_feedback(confidence)
                    suggestions = generate_suggestions(confidence)
                    
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
                            'feedback': feedback,
                            'suggestions': suggestions,
                            'timestamp': datetime.utcnow().isoformat(),
                            'method': 'aws_transcribe'
                        })
                    }
                    
                elif status == 'FAILED':
                    break
                
                time.sleep(1)
                wait_time += 1
            
            # Cleanup on timeout/failure
            try:
                transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                s3.delete_object(Bucket=BUCKET_NAME, Key=audio_key)
            except:
                pass
            
            # Return fallback response
            return get_fallback_response(target_language or GLOBAL_TARGET_LANGUAGE)
            
        else:
            # Handle text-to-speech request
            body = json.loads(event.get('body', '{}'))
            text = body.get('text', 'Hello')
            language = body.get('language', 'en')
            user_id = body.get('userId')
            
            if user_id:
                refresh_language_globals(user_id)
            
            # Generate speech using Polly
            voice_id = get_polly_voice(language)
            language_code = get_language_code(language)
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=language_code
            )
            
            # Convert to base64
            audio_data = response['AudioStream'].read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'audioData': audio_base64,
                    'audioFormat': 'mp3',
                    'text': text,
                    'voice': voice_id,
                    'language': language,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'aws_polly'
                })
            }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return get_fallback_response('en')

def get_polly_voice(language):
    voice_mapping = {
        'en': 'Joanna',
        'ms': 'Aditi',  # Using Hindi voice as closest to Malay
        'es': 'Conchita',
        'fr': 'Celine',
        'de': 'Marlene',
        'it': 'Carla',
        'zh': 'Zhiyu',
        'ja': 'Mizuki',
        'ko': 'Seoyeon'
    }
    return voice_mapping.get(language, 'Joanna')

def generate_feedback(confidence):
    if confidence > 0.9:
        return "Excellent pronunciation! Your accent is very clear."
    elif confidence > 0.8:
        return "Good pronunciation! Keep practicing to improve clarity."
    elif confidence > 0.6:
        return "Fair pronunciation. Focus on speaking more clearly."
    else:
        return "Keep practicing! Try speaking more slowly and clearly."

def generate_suggestions(confidence):
    if confidence < 0.7:
        return "Try speaking more slowly and emphasize each syllable clearly."
    elif confidence < 0.8:
        return "Good effort! Practice the pronunciation of difficult sounds."
    else:
        return "Great job! Continue practicing to maintain this level."

def get_fallback_response(language):
    fallback_responses = {
        'en': {
            'transcription': 'Hello, this is a practice session.',
            'feedback': 'Great job practicing! Keep it up.',
            'suggestions': 'Continue practicing regularly to improve your pronunciation.'
        },
        'ms': {
            'transcription': 'Selamat datang ke sesi latihan.',
            'feedback': 'Bagus! Teruskan berlatih.',
            'suggestions': 'Teruskan berlatih secara berkala untuk meningkatkan sebutan anda.'
        },
        'es': {
            'transcription': 'Hola, esta es una sesión de práctica.',
            'feedback': '¡Buen trabajo practicando!',
            'suggestions': 'Continúa practicando regularmente para mejorar tu pronunciación.'
        }
    }
    
    response_data = fallback_responses.get(language, fallback_responses['en'])
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'transcription': response_data['transcription'],
            'confidence': 0.8,
            'feedback': response_data['feedback'],
            'suggestions': response_data['suggestions'],
            'timestamp': datetime.utcnow().isoformat(),
            'method': 'fallback'
        })
    }
