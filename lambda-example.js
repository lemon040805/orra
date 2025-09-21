// Example Lambda function showing how to use global language configuration
const LANGUAGE_CONFIG = require('./lambda-config');

exports.handler = async (event) => {
    try {
        // Parse request body
        const body = JSON.parse(event.body);
        const { userId, text } = body;
        
        // Get user data from database (example)
        const userData = await getUserFromDatabase(userId);
        
        // Use global language configuration
        const userLanguages = LANGUAGE_CONFIG.getUserLanguages(userData);
        
        console.log('User Languages:', {
            native: userLanguages.nativeLanguage,
            target: userLanguages.targetLanguage,
            nativeName: userLanguages.nativeLanguageName,
            targetName: userLanguages.targetLanguageName,
            proficiency: userLanguages.proficiency
        });
        
        // Use global defaults if needed
        const sourceLanguage = userLanguages.nativeLanguage || LANGUAGE_CONFIG.GLOBAL_NATIVE_LANGUAGE;
        const targetLanguage = userLanguages.targetLanguage || LANGUAGE_CONFIG.GLOBAL_TARGET_LANGUAGE;
        
        // Example: Translation logic using global config
        const translatedText = await translateText(
            text,
            sourceLanguage,
            targetLanguage
        );
        
        // Example: Generate lesson using global config
        const lesson = await generateLesson({
            topic: body.topic,
            targetLanguage: userLanguages.targetLanguageName,
            nativeLanguage: userLanguages.nativeLanguageName,
            proficiency: userLanguages.proficiency
        });
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                translatedText,
                lesson,
                userLanguages
            })
        };
        
    } catch (error) {
        console.error('Lambda error:', error);
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                error: error.message,
                // Always provide fallback using global config
                fallbackLanguages: {
                    native: LANGUAGE_CONFIG.GLOBAL_NATIVE_LANGUAGE,
                    target: LANGUAGE_CONFIG.GLOBAL_TARGET_LANGUAGE,
                    nativeName: LANGUAGE_CONFIG.GLOBAL_NATIVE_LANGUAGE_NAME,
                    targetName: LANGUAGE_CONFIG.GLOBAL_TARGET_LANGUAGE_NAME
                }
            })
        };
    }
};

// Helper functions (examples)
async function getUserFromDatabase(userId) {
    // Implementation would fetch from DynamoDB or other database
    return {
        userId,
        nativeLanguage: 'en',
        targetLanguage: 'ms',
        proficiency: 'intermediate'
    };
}

async function translateText(text, sourceLanguage, targetLanguage) {
    // Implementation would call translation service
    return `[Translated from ${sourceLanguage} to ${targetLanguage}]: ${text}`;
}

async function generateLesson(params) {
    // Implementation would generate lesson content
    return {
        title: `${params.targetLanguage} Lesson: ${params.topic}`,
        content: `Learning ${params.topic} in ${params.targetLanguage}`,
        difficulty: params.proficiency
    };
}
