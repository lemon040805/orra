import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from language_config import (
    refresh_language_globals,
    GLOBAL_NATIVE_LANGUAGE_NAME,
    GLOBAL_TARGET_LANGUAGE_NAME,
)

dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def handler(event, context):
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            return get_user(event)
        elif http_method == 'POST':
            return create_or_update_user(event)
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
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_user(event):
    try:
        user_id = event['queryStringParameters']['userId']
        users_table = dynamodb.Table('language-learning-users')
        
        response = users_table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'user': response['Item']}, cls=DecimalEncoder)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'User not found'})
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

def create_or_update_user(event):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        
        users_table = dynamodb.Table('language-learning-users')
        
        # Check if user exists
        response = users_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            # Create new user with comprehensive profile
            user_item = {
                'userId': user_id,
                'email': body.get('email', ''),
                'name': body.get('name', ''),
                'targetLanguage': body.get('targetLanguage', GLOBAL_TARGET_LANGUAGE_NAME),
                'nativeLanguage': body.get('nativeLanguage', GLOBAL_NATIVE_LANGUAGE_NAME),
                'initialProficiency': body.get('initialProficiency', 'absolute-beginner'),
                'finalLevel': body.get('finalLevel', 'Beginner'),
                'assessmentScore': body.get('assessmentScore', 0),
                'totalQuestions': body.get('totalQuestions', 0),
                'skillBreakdown': body.get('skillBreakdown', {}),
                'weakAreas': body.get('weakAreas', []),
                'strongAreas': body.get('strongAreas', []),
                'recommendedFocus': body.get('recommendedFocus', []),
                'detailedResults': body.get('detailedResults', []),
                'onboardingCompleted': body.get('onboardingCompleted', False),
                'assessmentDate': body.get('assessmentDate', datetime.utcnow().isoformat()),
                'createdAt': datetime.utcnow().isoformat(),
                'lastLoginAt': datetime.utcnow().isoformat(),
                'streak': 0,
                'totalLessons': 0,
                'totalWords': 0,
                'averageAccuracy': 0,
                'preferences': {
                    'difficulty': body.get('finalLevel', 'Beginner').lower(),
                    'topics': ['daily conversation'],
                    'focusAreas': body.get('recommendedFocus', [])
                },
                'learningStats': {
                    'lessonsCompleted': 0,
                    'vocabularyLearned': 0,
                    'hoursStudied': 0,
                    'streakDays': 0,
                    'lastStudyDate': None
                }
            }
            
            users_table.put_item(Item=user_item)
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'User created successfully',
                    'user': user_item
                }, cls=DecimalEncoder)
            }
        else:
            # Update existing user with new assessment data if provided
            update_expression = 'SET lastLoginAt = :timestamp'
            expression_values = {':timestamp': datetime.utcnow().isoformat()}
            
            # Update assessment data if provided
            if 'finalLevel' in body:
                update_expression += ', finalLevel = :finalLevel'
                expression_values[':finalLevel'] = body['finalLevel']
            
            if 'skillBreakdown' in body:
                update_expression += ', skillBreakdown = :skillBreakdown'
                expression_values[':skillBreakdown'] = body['skillBreakdown']
                
            if 'weakAreas' in body:
                update_expression += ', weakAreas = :weakAreas'
                expression_values[':weakAreas'] = body['weakAreas']
                
            if 'recommendedFocus' in body:
                update_expression += ', recommendedFocus = :recommendedFocus'
                expression_values[':recommendedFocus'] = body['recommendedFocus']
            
            if 'onboardingCompleted' in body:
                update_expression += ', onboardingCompleted = :onboardingCompleted'
                expression_values[':onboardingCompleted'] = body['onboardingCompleted']
            
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'User updated successfully',
                    'user': response['Item']
                }, cls=DecimalEncoder)
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

def get_current_user_id():
    """
    Return the current user id.
    Replace this stub with your session/auth logic.
    If your framework injects user context elsewhere, just proxy it here.
    """
    # Example placeholder: read from environment for CLI/scripts
    import os
    return os.getenv("CURRENT_USER_ID")

# ---- Language preferences API ----
def get_user_language_prefs(user_id):
    """
    Return a tuple (native_language, target_language) for the given user_id.
    Replace the internals to hit your real DB/ORM.
    Expected keys on the user record: 'native_language', 'target_language'.
    """
    # ----- BEGIN: replace with your real implementation -----
    user = None
    try:
        if 'get_user' in globals():
            user = get_user(user_id)  # type: ignore[name-defined]
    except Exception:
        user = None
    try:
        if user is None and 'load_user' in globals():
            user = load_user(user_id)  # type: ignore[name-defined]
    except Exception:
        user = None
    try:
        if user is None and 'User' in globals():
            user = User.get(user_id)  # type: ignore[name-defined]
    except Exception:
        user = None

    if not user:
        # As a last resort, read env for demo: CURRENT_NATIVE_LANGUAGE, CURRENT_TARGET_LANGUAGE
        import os
        n = os.getenv("CURRENT_NATIVE_LANGUAGE")
        t = os.getenv("CURRENT_TARGET_LANGUAGE")
        return (n, t)

    native = None
    target = None
    try:
        native = getattr(user, 'native_language', None)
        target = getattr(user, 'target_language', None)
    except Exception:
        pass
    if native is None or target is None:
        try:
            native = (user.get('native_language') if hasattr(user, 'get') else native) or native
            target = (user.get('target_language') if hasattr(user, 'get') else target) or target
        except Exception:
            pass

    return (native, target)
