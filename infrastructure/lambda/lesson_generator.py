import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    try:
        body = json.loads(event['body']) 
        topic = body['topic']
  
        response = bedrock.converse(
            modelId='amazon.nova-pro-v1:0',
            messages=[{
                'role': 'user',
                'content': [{'text': f'Create a Spanish lesson about {topic}. Return JSON with title, content, vocabulary array, cultural_note, exercises array.'}]
            }]
        )
        
        lesson_text = response['output']['message']['content'][0]['text'].strip()
        
        try:
            lesson = json.loads(lesson_text)
        except:
            lesson = {
                "title": f"Spanish Lesson: {topic}",
                "content": f"Learn Spanish vocabulary about {topic}",
                "vocabulary": [{"word": "hola", "translation": "hello"}],
                "cultural_note": "Spanish greetings are important",
                "exercises": ["Practice pronunciation", "Use in sentences"]
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'lesson': lesson})
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