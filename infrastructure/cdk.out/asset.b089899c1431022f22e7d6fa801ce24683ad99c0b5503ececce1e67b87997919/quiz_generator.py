import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        target_language = body['targetLanguage']
        native_language = body['nativeLanguage']
        level = body['level']
        question_count = body.get('questionCount', 10)
        
        # Generate AI quiz
        quiz = generate_ai_quiz(target_language, native_language, level, question_count)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'questions': quiz,
                'level': level,
                'generatedAt': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def generate_ai_quiz(target_language, native_language, level, question_count):
    level_descriptions = {
        'elementary': 'basic vocabulary, present tense, simple phrases',
        'pre-intermediate': 'past/future tenses, everyday conversations, basic grammar',
        'intermediate': 'complex grammar, subjunctive, conditional, opinions',
        'upper-intermediate': 'idiomatic expressions, abstract topics, nuanced meanings',
        'advanced': 'sophisticated vocabulary, cultural references, professional language'
    }
    
    level_desc = level_descriptions.get(level, 'appropriate for the specified level')
    
    prompt = f"""Generate exactly {question_count} multiple choice questions to assess {level} level {target_language} proficiency for a {native_language} speaker.

Level focus: {level_desc}

Requirements:
- Each question must have exactly 4 options
- Include "I don't know" as the 4th option for every question
- Questions should test: vocabulary, grammar, cultural knowledge, and practical usage
- Difficulty appropriate for {level} level
- Mix question types: translation, grammar, usage, cultural context
- Make questions progressively challenging within the level

Return ONLY a JSON array with this exact format:
[
  {{
    "question": "Question text here",
    "options": ["Correct answer", "Wrong answer 1", "Wrong answer 2", "I don't know"],
    "correct": 0
  }}
]

Generate {question_count} questions for {level} {target_language}:"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 3000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        quiz_content = result['content'][0]['text']
        
        # Clean up the response to extract JSON
        quiz_content = quiz_content.strip()
        if quiz_content.startswith('```json'):
            quiz_content = quiz_content[7:]
        if quiz_content.endswith('```'):
            quiz_content = quiz_content[:-3]
        quiz_content = quiz_content.strip()
        
        # Try to parse as JSON
        try:
            quiz_data = json.loads(quiz_content)
            if isinstance(quiz_data, list) and len(quiz_data) > 0:
                # Ensure all questions have "I don't know" option
                for question in quiz_data:
                    if len(question['options']) < 4:
                        question['options'].append("I don't know")
                    elif question['options'][3] != "I don't know":
                        question['options'][3] = "I don't know"
                return quiz_data[:question_count]
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content: {quiz_content}")
            
        # Fallback if parsing fails
        return generate_fallback_quiz(target_language, level, question_count)
            
    except Exception as e:
        print(f"Bedrock error: {e}")
        return generate_fallback_quiz(target_language, level, question_count)

def generate_fallback_quiz(target_language, level, question_count):
    # Language-specific fallback questions
    base_questions = {
        'Spanish': {
            'elementary': [
                {
                    "question": "What does 'Hola' mean?",
                    "options": ["Hello", "Goodbye", "Thank you", "I don't know"],
                    "correct": 0
                },
                {
                    "question": "How do you say 'Thank you' in Spanish?",
                    "options": ["Gracias", "Por favor", "De nada", "I don't know"],
                    "correct": 0
                },
                {
                    "question": "Complete: 'Me _____ María' (My name is María)",
                    "options": ["llamo", "soy", "tengo", "I don't know"],
                    "correct": 0
                }
            ],
            'intermediate': [
                {
                    "question": "Choose the correct subjunctive: 'Espero que _____ bien'",
                    "options": ["estés", "estás", "estar", "I don't know"],
                    "correct": 0
                },
                {
                    "question": "What's the difference between 'ser' and 'estar'?",
                    "options": ["Ser is permanent, estar is temporary", "No difference", "Estar is formal", "I don't know"],
                    "correct": 0
                }
            ]
        },
        'French': {
            'elementary': [
                {
                    "question": "What does 'Bonjour' mean?",
                    "options": ["Hello", "Goodbye", "Thank you", "I don't know"],
                    "correct": 0
                },
                {
                    "question": "How do you say 'Thank you' in French?",
                    "options": ["Merci", "S'il vous plaît", "De rien", "I don't know"],
                    "correct": 0
                }
            ]
        }
    }
    
    # Get questions for the language and level, or use Spanish elementary as fallback
    questions = base_questions.get(target_language, {}).get(level, base_questions['Spanish']['elementary'])
    
    # Repeat questions if we need more
    result = []
    for i in range(question_count):
        if i < len(questions):
            result.append(questions[i])
        else:
            # Create generic question
            result.append({
                "question": f"Question {i+1} for {level} {target_language}",
                "options": ["Option A", "Option B", "Option C", "I don't know"],
                "correct": 0
            })
    
    return result
