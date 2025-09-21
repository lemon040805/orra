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
)

transcribe = boto3.client('transcribe')
polly = boto3.client('polly')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        refresh_language_globals(user_id)

        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle pronunciation analysis
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                audio_data = base64.b64decode(body)
            else:
                audio_data = body.encode() if isinstance(body, str) else body
            
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
                LanguageCode='es-ES'
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
            
            raise Exception("Transcription timeout or failed")
            
        else:
            # Handle text-to-speech request
            body = json.loads(event.get('body', '{}'))
            text = body.get('text', 'Hello')
            language = body.get('language', LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE_NAME'])
            
            # Generate speech using Polly
            voice_id = get_polly_voice(language)
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=get_polly_language_code(language)
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
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_polly_voice(language):
    # Map to Polly voice names using global config
    voice_mapping = {
        LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE_NAME']: 'Joanna',
        LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE_NAME']: 'Aditi',
        'French': 'Celine',
        'German': 'Marlene',
        'Italian': 'Carla'
    }
    return voice_mapping.get(language, 'Joanna')

def get_polly_language_code(language):
    return get_language_code(language)

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
