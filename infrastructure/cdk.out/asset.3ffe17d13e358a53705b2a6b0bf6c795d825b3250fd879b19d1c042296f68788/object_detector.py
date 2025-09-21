import json
import boto3
import base64
import uuid
import os
from datetime import datetime

rekognition = boto3.client('rekognition')
translate = boto3.client('translate')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('MEDIA_BUCKET')

def handler(event, context):
    try:
        # Parse the multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Extract image data from multipart form
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                image_data = base64.b64decode(body)
            else:
                image_data = body.encode() if isinstance(body, str) else body
            
            # Generate unique filename
            image_key = f"images/{uuid.uuid4()}.jpg"
            
            # Upload image to S3
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
                
                # Translate object name to target language
                try:
                    translation_response = translate.translate_text(
                        Text=object_name,
                        SourceLanguageCode='en',
                        TargetLanguageCode='es'  # Default to Spanish
                    )
                    translated_name = translation_response['TranslatedText']
                except Exception as e:
                    print(f"Translation error for {object_name}: {e}")
                    translated_name = get_manual_translation(object_name)
                
                detected_objects.append({
                    'name': object_name,
                    'translation': translated_name,
                    'confidence': confidence
                })
            
            # Clean up - delete the uploaded image
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
                    'method': 'aws_rekognition'
                })
            }
            
        else:
            # Handle direct image data (base64)
            body = json.loads(event.get('body', '{}'))
            
            if 'image' in body:
                # Decode base64 image
                image_data = base64.b64decode(body['image'])
                
                # Detect objects directly from bytes
                response = rekognition.detect_labels(
                    Image={'Bytes': image_data},
                    MaxLabels=10,
                    MinConfidence=70
                )
                
                detected_objects = []
                
                for label in response['Labels']:
                    object_name = label['Name']
                    confidence = label['Confidence'] / 100.0
                    
                    # Translate to Spanish
                    try:
                        translation_response = translate.translate_text(
                            Text=object_name,
                            SourceLanguageCode='en',
                            TargetLanguageCode='es'
                        )
                        translated_name = translation_response['TranslatedText']
                    except:
                        translated_name = get_manual_translation(object_name)
                    
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
                        'method': 'aws_rekognition_direct'
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

def get_manual_translation(object_name):
    """Fallback translations for common objects"""
    translations = {
        'Person': 'Persona',
        'Phone': 'Teléfono',
        'Book': 'Libro',
        'Cup': 'Taza',
        'Computer': 'Computadora',
        'Chair': 'Silla',
        'Table': 'Mesa',
        'Car': 'Coche',
        'Dog': 'Perro',
        'Cat': 'Gato',
        'Tree': 'Árbol',
        'House': 'Casa',
        'Water': 'Agua',
        'Food': 'Comida',
        'Clothing': 'Ropa',
        'Shoe': 'Zapato',
        'Hand': 'Mano',
        'Face': 'Cara',
        'Eye': 'Ojo',
        'Building': 'Edificio'
    }
    return translations.get(object_name, object_name)
