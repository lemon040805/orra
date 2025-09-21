import json
import boto3
import base64
import uuid
import os
from datetime import datetime

rekognition = boto3.client('rekognition')
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        # Parse multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Extract image from form data
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                image_data = base64.b64decode(body)
            else:
                image_data = body.encode() if isinstance(body, str) else body
            
            # Upload to S3
            image_key = f"images/{uuid.uuid4()}.jpg"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=image_key,
                Body=image_data,
                ContentType='image/jpeg'
            )
            
            # Detect objects using Rekognition
            response = rekognition.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': BUCKET_NAME,
                        'Name': image_key
                    }
                },
                MaxLabels=10,
                MinConfidence=70
            )
            
            detected_objects = []
            
            for label in response['Labels']:
                object_name = label['Name']
                confidence = label['Confidence'] / 100.0
                
                # Translate using Bedrock
                translated_name = translate_with_bedrock(object_name, 'Spanish')
                
                detected_objects.append({
                    'name': object_name,
                    'translation': translated_name,
                    'confidence': confidence
                })
            
            # Clean up
            s3.delete_object(Bucket=BUCKET_NAME, Key=image_key)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'objects': detected_objects,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'aws_rekognition_nova_translation'
                })
            }
            
        else:
            # Handle direct image data
            body = json.loads(event.get('body', '{}'))
            
            if 'image' in body:
                image_data = base64.b64decode(body['image'])
                
                # Detect objects directly
                response = rekognition.detect_labels(
                    Image={'Bytes': image_data},
                    MaxLabels=10,
                    MinConfidence=70
                )
                
                detected_objects = []
                
                for label in response['Labels']:
                    object_name = label['Name']
                    confidence = label['Confidence'] / 100.0
                    
                    translated_name = translate_with_bedrock(object_name, 'Spanish')
                    
                    detected_objects.append({
                        'name': object_name,
                        'translation': translated_name,
                        'confidence': confidence
                    })
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'objects': detected_objects,
                        'timestamp': datetime.utcnow().isoformat(),
                        'method': 'aws_rekognition_nova_direct'
                    })
                }
            else:
                raise Exception("No image data provided")
        
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
        # Fallback dictionary
        translations = {
            'Person': 'Persona', 'Phone': 'Teléfono', 'Book': 'Libro',
            'Cup': 'Taza', 'Computer': 'Computadora', 'Chair': 'Silla',
            'Table': 'Mesa', 'Car': 'Coche', 'Dog': 'Perro', 'Cat': 'Gato'
        }
        return translations.get(text, text)
