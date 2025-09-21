import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            return get_vocabulary(event)
        elif http_method == 'POST':
            return add_vocabulary(event)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
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

def get_vocabulary(event):
    try:
        user_id = event['queryStringParameters']['userId']
        vocabulary_table = dynamodb.Table('language-learning-vocabulary')
        
        response = vocabulary_table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'vocabulary': response['Items']})
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

def add_vocabulary(event):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        word = body['word']
        translation = body['translation']
        context = body.get('context', '')
        
        vocabulary_table = dynamodb.Table('language-learning-vocabulary')
        
        word_item = {
            'userId': user_id,
            'wordId': str(uuid.uuid4()),
            'word': word,
            'translation': translation,
            'context': context,
            'addedAt': datetime.utcnow().isoformat(),
            'masteryLevel': 1,
            'reviewCount': 0,
            'correctCount': 0
        }
        
        vocabulary_table.put_item(Item=word_item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Vocabulary added successfully',
                'word': word_item
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
