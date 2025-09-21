import json
import boto3
import base64
import os
from datetime import datetime
import re
from typing import Optional, Tuple

import language_config as langcfg

rekognition = boto3.client('rekognition')
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        
        langcfg.refresh_language_globals(user_id)
        target_name = langcfg.GLOBAL_TARGET_LANGUAGE_NAME  # e.g., "Malay"
        native_name = langcfg.GLOBAL_NATIVE_LANGUAGE_NAME  # if you need it

        # Get content type
        headers = event.get('headers', {})
        content_type = headers.get('content-type') or headers.get('Content-Type', '')
        
        # Handle multipart form data
        if 'multipart/form-data' in content_type:
            body = event.get('body', '')
            is_base64 = event.get('isBase64Encoded', False)
            
            if is_base64:
                body = base64.b64decode(body).decode('utf-8')
            
            # Extract image from multipart data
            image_data = extract_image_from_multipart(body, content_type)
            
            if not image_data:
                raise Exception("No image found in multipart data")
            
            # Process with Rekognition directly
            response = rekognition.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=10,
                MinConfidence=70
            )
            
        else:
            # Handle JSON body with base64 image
            try:
                body = json.loads(event.get('body', '{}'))
            except:
                raise Exception("Invalid JSON body")
            
            if 'image' not in body:
                raise Exception("No image data provided in request")
            
            # Decode base64 image
            try:
                image_data = base64.b64decode(body['image'])
            except:
                raise Exception("Invalid base64 image data")
            
            # Process with Rekognition
            response = rekognition.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=10,
                MinConfidence=70
            )
        
        # Process detected objects
        detected_objects = []
        
        for label in response['Labels']:
            object_name = label['Name']
            confidence = label['Confidence'] / 100.0
            
            # Translate using Bedrock
            translated_name = translate_with_bedrock(object_name, target_name)
            
            detected_objects.append({
                'name': object_name,
                'translation': translated_name,
                'confidence': confidence
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'objects': detected_objects,
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'aws_rekognition_enhanced'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def extract_image_from_multipart(body, content_type):
    """Extract image data from multipart form data"""
    try:
        # Get boundary from content type
        boundary_match = re.search(r'boundary=([^;\s]+)', content_type)
        if not boundary_match:
            return None
        
        boundary = boundary_match.group(1)
        
        # Split by boundary
        parts = body.split(f'--{boundary}')
        
        for part in parts:
            if 'Content-Type: image/' in part or 'filename=' in part:
                # Find the start of binary data (after double CRLF)
                data_start = part.find('\r\n\r\n')
                if data_start == -1:
                    data_start = part.find('\n\n')
                
                if data_start != -1:
                    # Extract binary data
                    image_data = part[data_start + 4:].rstrip('\r\n-')
                    
                    # If it's base64 encoded, decode it
                    try:
                        return base64.b64decode(image_data)
                    except:
                        # If not base64, return as bytes
                        return image_data.encode('latin-1')
        
        return None
    except Exception as e:
        print(f"Error extracting image: {e}")
        return None

def translate_with_bedrock(text, target_language):
    try:
        prompt = f"Translate '{text}' to {target_language}. Return only the translation, no explanation."
        
        response = bedrock.converse(
            modelId='amazon.nova-pro-v1:0',
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }]
        )
        
        translation = response['output']['message']['content'][0]['text'].strip()
        return translation
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Multi-language fallback using global config
        global_target = LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE_NAME']
        is_malay = global_target == get_language_name(LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE'])
        translations = {
            global_target: {'Person': 'Orang' if is_malay else 'Persona', 'Phone': 'Telefon' if is_malay else 'Teléfono', 'Book': 'Buku' if is_malay else 'Libro'},
            'Fallback': {'Person': 'Person', 'Phone': 'Phone', 'Book': 'Book'},
            'Korean': {'Person': '사람', 'Phone': '전화기', 'Book': '책'},
            'Chinese': {'Person': '人', 'Phone': '电话', 'Book': '书'},
            'French': {'Person': 'Personne', 'Phone': 'Téléphone', 'Book': 'Livre'}
        }
        lang_dict = translations.get(target_language, translations[global_target])
        return lang_dict.get(text, text)