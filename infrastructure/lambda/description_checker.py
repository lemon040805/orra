import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_description = body['userDescription']
        expected_elements = body.get('expectedElements', [])
        target_language = body.get('targetLanguage', 'Spanish')
        image_context = body.get('imageContext', '')
        
        # Use Nova to check description accuracy
        prompt = f"""You are a language learning assistant. A student learning {target_language} has described an image.

Image context: {image_context}
Expected elements: {', '.join(expected_elements)}
Student's description in {target_language}: "{user_description}"

Please evaluate the student's description and provide:
1. Accuracy score (0-100) based on how well they described the image
2. Constructive feedback in English
3. Vocabulary suggestions for improvement

Respond in JSON format:
{{
    "accuracy": 85,
    "feedback": "Good description! You captured the main elements.",
    "suggestions": ["word1", "word2", "word3"]
}}"""

        try:
            response = bedrock.converse(
                modelId='amazon.nova-pro-v1:0',
                messages=[{
                    'role': 'user',
                    'content': [{'text': prompt}]
                }]
            )
            
            result_content = response['output']['message']['content'][0]['text'].strip()
            
            # Clean JSON response
            if result_content.startswith('```json'):
                result_content = result_content[7:]
            if result_content.endswith('```'):
                result_content = result_content[:-3]
            result_content = result_content.strip()
            
            result_data = json.loads(result_content)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'accuracy': result_data.get('accuracy', 0),
                    'feedback': result_data.get('feedback', 'Good effort!'),
                    'suggestions': result_data.get('suggestions', []),
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'amazon_nova_pro'
                })
            }
            
        except Exception as e:
            print(f"Nova error: {e}")
            # Simple fallback scoring
            user_words = user_description.lower().split()
            matches = sum(1 for element in expected_elements 
                         if any(element.lower() in word or word in element.lower() 
                               for word in user_words))
            
            accuracy = (matches / len(expected_elements)) * 100 if expected_elements else 50
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'accuracy': accuracy,
                    'feedback': f'Found {matches} out of {len(expected_elements)} expected elements.',
                    'suggestions': expected_elements[:3],
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'fallback_scoring'
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
