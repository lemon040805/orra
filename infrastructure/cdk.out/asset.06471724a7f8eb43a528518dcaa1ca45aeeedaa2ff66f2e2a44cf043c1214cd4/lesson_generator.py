import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        target_language = body.get('targetLanguage', 'Spanish')
        native_language = body.get('nativeLanguage', 'English')
        topic = body.get('topic', 'daily conversation')
        difficulty_level = body.get('difficultyLevel', 'intermediate')
        
        # Get user's assessed level and preferences from database
        users_table = dynamodb.Table('language-learning-users')
        user_response = users_table.get_item(Key={'userId': user_id})
        
        if 'Item' in user_response:
            user_data = user_response['Item']
            # Use user's actual level if available
            assessed_level = user_data.get('finalLevel', difficulty_level)
            weak_areas = user_data.get('weakAreas', [])
            target_language = user_data.get('targetLanguage', target_language)
            native_language = user_data.get('nativeLanguage', native_language)
        else:
            assessed_level = difficulty_level
            weak_areas = []

        # Generate adaptive lesson based on user's profile
        lesson = generate_adaptive_lesson(
            target_language, native_language, topic, 
            assessed_level, weak_areas, user_id
        )
        
        # Store lesson in database
        lesson_id = str(uuid.uuid4())
        lessons_table = dynamodb.Table('language-learning-lessons')
        lesson_item = {
            'lessonId': lesson_id,
            'userId': user_id,
            'targetLanguage': target_language,
            'nativeLanguage': native_language,
            'topic': topic,
            'difficultyLevel': assessed_level,
            'lesson': lesson,
            'createdAt': datetime.utcnow().isoformat(),
            'completed': False
        }
        
        lessons_table.put_item(Item=lesson_item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'lessonId': lesson_id,
                'lesson': lesson,
                'adaptedFor': assessed_level,
                'assessmentBased': True
            }, cls=DecimalEncoder)
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

def generate_adaptive_lesson(target_language, native_language, topic, level, weak_areas, user_id):
    # Map difficulty levels to complexity descriptions
    complexity_map = {
        'beginner': 'very basic vocabulary, present tense only, simple sentence structures',
        'intermediate': 'expanded vocabulary, multiple tenses, complex grammar including subjunctive',
        'advanced': 'sophisticated vocabulary, complex sentence structures, idiomatic expressions, cultural nuances'
    }
    
    complexity = complexity_map.get(level.lower(), 'intermediate level vocabulary and grammar')
    
    # Include weak areas focus if available
    focus_areas = f"Pay special attention to: {', '.join(weak_areas)}" if weak_areas else ""
    
    prompt = f"""Create a comprehensive {target_language} lesson for a {level} learner whose native language is {native_language}.

Topic: {topic}
Complexity Level: {complexity}
{focus_areas}

Create a detailed JSON lesson with the following structure:
{{
    "title": "Engaging lesson title related to {topic}",
    "content": "Main lesson content (3-4 paragraphs) explaining key concepts, grammar, and usage patterns. Include examples and explanations.",
    "vocabulary": [
        {{"word": "target language word", "translation": "native language translation", "pronunciation": "phonetic guide", "example": "example sentence"}},
        // Include 8-10 vocabulary words relevant to the topic
    ],
    "grammar_focus": "Key grammar point for this lesson with clear explanation",
    "cultural_note": "Interesting cultural insight related to the topic and language",
    "exercises": [
        "Practice exercise 1 - specific and actionable",
        "Practice exercise 2 - builds on lesson content", 
        "Practice exercise 3 - real-world application"
    ],
    "phrases": [
        {{"phrase": "useful phrase in target language", "translation": "translation", "context": "when to use this phrase"}},
        // Include 5-6 practical phrases
    ],
    "difficulty_explanation": "Why this lesson matches the {level} level and how it builds language skills"
}}

Make the lesson practical, engaging, and perfectly calibrated for {level} proficiency. Focus on real-world usage and communication."""

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
        lesson_content = result['content'][0]['text']
        
        # Clean up the response to extract JSON
        lesson_content = lesson_content.strip()
        if lesson_content.startswith('```json'):
            lesson_content = lesson_content[7:]
        if lesson_content.endswith('```'):
            lesson_content = lesson_content[:-3]
        lesson_content = lesson_content.strip()
        
        # Try to parse as JSON
        try:
            lesson_data = json.loads(lesson_content)
            return lesson_data
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content: {lesson_content}")
            return create_fallback_lesson(target_language, topic, level, native_language)
            
    except Exception as e:
        print(f"Bedrock error: {e}")
        return create_fallback_lesson(target_language, topic, level, native_language)

def create_fallback_lesson(target_language, topic, level, native_language):
    # Language-specific vocabulary based on topic
    vocabulary_map = {
        'Spanish': {
            'daily conversation': [
                {"word": "Hola", "translation": "Hello", "pronunciation": "OH-lah", "example": "Hola, ¿cómo estás?"},
                {"word": "Gracias", "translation": "Thank you", "pronunciation": "GRAH-see-ahs", "example": "Gracias por tu ayuda"},
                {"word": "Por favor", "translation": "Please", "pronunciation": "por fah-VOR", "example": "¿Puedes ayudarme, por favor?"},
                {"word": "Disculpe", "translation": "Excuse me", "pronunciation": "dees-KOOL-peh", "example": "Disculpe, ¿dónde está el baño?"},
                {"word": "¿Cómo está?", "translation": "How are you?", "pronunciation": "KOH-moh ehs-TAH", "example": "¡Hola María! ¿Cómo está?"},
                {"word": "Muy bien", "translation": "Very well", "pronunciation": "moo-ee bee-EHN", "example": "Estoy muy bien, gracias"},
                {"word": "Hasta luego", "translation": "See you later", "pronunciation": "AHS-tah loo-EH-goh", "example": "Hasta luego, nos vemos mañana"},
                {"word": "De nada", "translation": "You're welcome", "pronunciation": "deh NAH-dah", "example": "De nada, fue un placer ayudarte"}
            ],
            'food': [
                {"word": "Comida", "translation": "Food", "pronunciation": "koh-MEE-dah", "example": "La comida está deliciosa"},
                {"word": "Restaurante", "translation": "Restaurant", "pronunciation": "rehs-tow-RAHN-teh", "example": "Vamos al restaurante nuevo"},
                {"word": "Menú", "translation": "Menu", "pronunciation": "meh-NOO", "example": "¿Puedo ver el menú, por favor?"},
                {"word": "Camarero", "translation": "Waiter", "pronunciation": "kah-mah-REH-roh", "example": "El camarero es muy amable"},
                {"word": "Cuenta", "translation": "Bill", "pronunciation": "KWEN-tah", "example": "La cuenta, por favor"},
                {"word": "Delicioso", "translation": "Delicious", "pronunciation": "deh-lee-see-OH-soh", "example": "Este plato está delicioso"},
                {"word": "Tengo hambre", "translation": "I'm hungry", "pronunciation": "TEHN-goh AHM-breh", "example": "Tengo hambre, vamos a comer"},
                {"word": "Beber", "translation": "To drink", "pronunciation": "beh-BEHR", "example": "¿Qué quieres beber?"}
            ]
        }
    }
    
    # Get vocabulary for the topic and language
    vocab_key = topic.lower() if topic.lower() in vocabulary_map.get(target_language, {}) else 'daily conversation'
    vocabulary = vocabulary_map.get(target_language, {}).get(vocab_key, vocabulary_map['Spanish']['daily conversation'])
    
    # Create phrases based on topic
    phrases_map = {
        'daily conversation': [
            {"phrase": "¿Cómo te llamas?", "translation": "What's your name?", "context": "When meeting someone new"},
            {"phrase": "Mucho gusto", "translation": "Nice to meet you", "context": "After being introduced"},
            {"phrase": "¿De dónde eres?", "translation": "Where are you from?", "context": "Getting to know someone"},
            {"phrase": "No hablo español muy bien", "translation": "I don't speak Spanish very well", "context": "When struggling with the language"},
            {"phrase": "¿Puedes repetir, por favor?", "translation": "Can you repeat, please?", "context": "When you didn't understand"}
        ],
        'food': [
            {"phrase": "¿Qué recomienda?", "translation": "What do you recommend?", "context": "Asking the waiter for suggestions"},
            {"phrase": "Quisiera...", "translation": "I would like...", "context": "Polite way to order food"},
            {"phrase": "¿Está incluida la propina?", "translation": "Is the tip included?", "context": "Asking about service charge"},
            {"phrase": "La cuenta, por favor", "translation": "The bill, please", "context": "When ready to pay"},
            {"phrase": "¿Tienen opciones vegetarianas?", "translation": "Do you have vegetarian options?", "context": "Asking about dietary restrictions"}
        ]
    }
    
    phrases = phrases_map.get(topic.lower(), phrases_map['daily conversation'])
    
    return {
        "title": f"{level.title()} {target_language}: {topic.title()}",
        "content": f"Welcome to your {level} level {target_language} lesson on {topic}! This lesson is designed to help you communicate effectively in real-world situations. We'll focus on practical vocabulary and phrases that you can use immediately in conversations.\n\nIn this lesson, you'll learn essential words and expressions related to {topic}. Each vocabulary item includes pronunciation guides to help you speak with confidence. Pay attention to the cultural notes as they provide valuable insights into how native speakers actually use these expressions.\n\nPractice is key to mastering any language. Use the exercises provided to reinforce what you've learned, and don't be afraid to make mistakes – they're an important part of the learning process!",
        "vocabulary": vocabulary,
        "grammar_focus": f"Present tense usage and basic sentence structure appropriate for {level} level. Focus on subject-verb agreement and common verb conjugations used in {topic} contexts.",
        "cultural_note": f"In {target_language}-speaking countries, {topic} involves specific cultural practices and etiquette. Understanding these cultural nuances will help you communicate more naturally and avoid misunderstandings.",
        "exercises": [
            f"Practice pronouncing each vocabulary word 5 times, focusing on the pronunciation guides provided",
            f"Create 3 original sentences using the new vocabulary in {topic} contexts",
            f"Role-play a {topic} scenario using the phrases and vocabulary from this lesson"
        ],
        "phrases": phrases,
        "difficulty_explanation": f"This lesson is calibrated for {level} learners, featuring vocabulary and grammar structures appropriate for your current proficiency level. The content builds on fundamental concepts while introducing new elements to advance your skills."
    }
