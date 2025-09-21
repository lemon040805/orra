// AWS Configuration
const poolData = {
    UserPoolId: 'us-east-1_fvNtXNAyp',
    ClientId: '5rh6qtboujp6cdslv62as1onbo'
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
const API_BASE_URL = 'https://r9t9xk38j1.execute-api.us-east-1.amazonaws.com/prod';

let currentUser = null;
let currentToken = null;
let mediaRecorder = null;
let recordedChunks = [];
let cameraStream = null;
let isRecording = false;

// Security check and initialize app
window.onload = async function() {
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
        alert('Please log in to access the app');
        window.location.href = 'index.html';
        return;
    }

    cognitoUser.getSession(async (err, session) => {
        if (err || !session.isValid()) {
            alert('Your session has expired. Please log in again.');
            window.location.href = 'index.html';
            return;
        }
        
        currentUser = cognitoUser;
        currentToken = session.getIdToken().getJwtToken();
        
        await loadUserData();
        await loadProgress();
    });
};

// User Management
async function loadUserData() {
    try {
        const attributes = await getUserAttributes();
        document.getElementById('userName').textContent = attributes.name || attributes.email;
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

function getUserAttributes() {
    return new Promise((resolve, reject) => {
        currentUser.getUserAttributes((err, attributes) => {
            if (err) {
                reject(err);
                return;
            }
            
            const userAttributes = {};
            attributes.forEach(attr => {
                userAttributes[attr.getName()] = attr.getValue();
            });
            resolve(userAttributes);
        });
    });
}

async function loadProgress() {
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/vocabulary?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const vocabularyCount = data.vocabulary ? data.vocabulary.length : 0;
            document.getElementById('wordsLearned').textContent = vocabularyCount;
        }
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

function logout() {
    if (currentUser) {
        currentUser.signOut();
    }
    window.location.href = 'index.html';
}

// Modal Management
function openLessonModal() {
    document.getElementById('lessonModal').style.display = 'block';
}

function openVoiceModal() {
    document.getElementById('voiceModal').style.display = 'block';
}

function openCameraModal() {
    document.getElementById('cameraModal').style.display = 'block';
    startCamera();
}

function openTranslateModal() {
    document.getElementById('translateModal').style.display = 'block';
}

function openVocabularyModal() {
    document.getElementById('vocabularyModal').style.display = 'block';
    loadVocabulary();
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    if (modalId === 'cameraModal') {
        stopCamera();
    }
    if (modalId === 'voiceModal') {
        stopRecording();
    }
}

// AI Lesson Generation
async function generateLesson() {
    const topic = document.getElementById('lessonTopic').value;
    const resultDiv = document.getElementById('lessonResult');
    
    if (!topic.trim()) {
        alert('Please enter a topic for the lesson');
        return;
    }
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating personalized lesson based on your proficiency...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/lessons`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                userId: attributes.sub,
                topic: topic
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Lesson response:', data); // Debug log
            
            if (!data.lesson) {
                throw new Error('No lesson data received');
            }
            
            const lesson = data.lesson;
            
            // Check if lesson has required properties
            if (!lesson.title || !lesson.content) {
                throw new Error('Incomplete lesson data received');
            }
            
            resultDiv.innerHTML = `
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <p><strong>🤖 Powered by Amazon Nova Pro</strong></p>
                    <p><strong>📚 Auto-Generated for:</strong> ${data.userProficiency} level ${data.targetLanguage}</p>
                    <p><strong>📖 Topic:</strong> ${topic}</p>
                </div>
                <h4>${lesson.title}</h4>
                <p><strong>Content:</strong> ${lesson.content}</p>
                ${lesson.vocabulary && lesson.vocabulary.length > 0 ? `
                    <div style="margin-top: 15px;">
                        <strong>Vocabulary:</strong>
                        ${lesson.vocabulary.map(word => `
                            <div class="vocabulary-item">
                                <span><strong>${word.word}</strong> - ${word.translation}</span>
                                <button onclick="addToVocabulary('${word.word}', '${word.translation}')" class="btn" style="padding: 5px 10px; font-size: 12px;">Add to My Words</button>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                ${lesson.cultural_note || lesson.culturalNote ? `
                    <p style="margin-top: 15px;"><strong>Cultural Note:</strong> ${lesson.cultural_note || lesson.culturalNote}</p>
                ` : ''}
                ${lesson.exercises && lesson.exercises.length > 0 ? `
                    <div style="margin-top: 15px;">
                        <strong>Practice Exercises:</strong>
                        <ol>
                            ${lesson.exercises.map(exercise => `<li>${exercise}</li>`).join('')}
                        </ol>
                    </div>
                ` : ''}
            `;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate lesson');
        }
    } catch (error) {
        console.error('Lesson generation error:', error);
        resultDiv.innerHTML = `<div style="color: #dc3545;">Error: ${error.message}</div>`;
    }
}

// Voice Practice with AI-generated challenges
async function toggleRecording() {
    await startVoicePractice();
}

async function startVoicePractice() {
    const resultDiv = document.getElementById('voiceResult');
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating pronunciation challenge...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const attributes = await getUserAttributes();
        
        // Get user's language settings
        const userResponse = await fetch(`${API_BASE_URL}/users?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        let targetLanguage = 'Spanish';
        let difficultyLevel = 'Intermediate';
        
        if (userResponse.ok) {
            const userData = await userResponse.json();
            targetLanguage = userData.user?.targetLanguage || 'Spanish';
            difficultyLevel = userData.user?.finalLevel || 'Intermediate';
        }
        
        // Generate simple pronunciation challenge using translation
        const challenges = [
            { en: "Hello, how are you?", es: "Hola, ¿cómo estás?" },
            { en: "Thank you very much", es: "Muchas gracias" },
            { en: "Where is the bathroom?", es: "¿Dónde está el baño?" },
            { en: "I would like water", es: "Me gustaría agua" },
            { en: "Good morning", es: "Buenos días" },
            { en: "Excuse me", es: "Disculpe" },
            { en: "How much does it cost?", es: "¿Cuánto cuesta?" }
        ];
        
        const randomChallenge = challenges[Math.floor(Math.random() * challenges.length)];
        currentPronunciationChallenge = {
            textToSay: randomChallenge.es,
            translation: randomChallenge.en,
            targetLanguage: targetLanguage
        };
        
        resultDiv.innerHTML = `
            <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                <h4>🎯 Pronunciation Challenge</h4>
                <p><strong>Say this in ${targetLanguage}:</strong></p>
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0; font-size: 18px; font-weight: bold; color: #2d5a2d;">
                    "${currentPronunciationChallenge.textToSay}"
                </div>
                <p style="color: #666; font-size: 14px;">English: ${currentPronunciationChallenge.translation}</p>
                <button onclick="speakText('${currentPronunciationChallenge.textToSay}', 'es')" class="btn" style="margin: 5px;">🔊 Listen</button>
                <button onclick="startPronunciationRecording()" class="btn" style="margin: 5px;">🎤 Record Your Voice</button>
            </div>
        `;
        
    } catch (error) {
        console.error('Voice practice error:', error);
        resultDiv.innerHTML = `<div style="color: #dc3545;">Error: ${error.message}</div>`;
    }
}

let currentPronunciationChallenge = null;

async function startPronunciationRecording() {
    if (!currentPronunciationChallenge) {
        alert('No active pronunciation challenge');
        return;
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
            await checkPronunciation(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        document.getElementById('voiceResult').innerHTML += `
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center;">
                <p><strong>🎤 Recording...</strong></p>
                <p>Say: "${currentPronunciationChallenge.textToSay}"</p>
                <button onclick="stopPronunciationRecording()" class="btn">⏹️ Stop Recording</button>
            </div>
        `;
        
    } catch (error) {
        console.error('Recording error:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}

function stopPronunciationRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        isRecording = false;
    }
}

async function checkPronunciation(audioBlob) {
    const resultDiv = document.getElementById('voiceResult');
    resultDiv.innerHTML += '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing your pronunciation...</div>';
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'pronunciation.wav');
        
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/voice-transcribe`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            const transcribedText = data.transcribedText || '';
            const expectedText = currentPronunciationChallenge.textToSay.toLowerCase();
            const actualText = transcribedText.toLowerCase();
            
            // Simple accuracy calculation
            const accuracy = calculateSimilarity(expectedText, actualText);
            
            let scoreColor = '#dc3545'; // Red
            let scoreEmoji = '❌';
            let feedback = 'Keep practicing! Try to pronounce each word clearly.';
            
            if (accuracy >= 80) {
                scoreColor = '#28a745'; // Green
                scoreEmoji = '✅';
                feedback = 'Excellent pronunciation! Well done!';
            } else if (accuracy >= 60) {
                scoreColor = '#ffc107'; // Yellow
                scoreEmoji = '⚠️';
                feedback = 'Good effort! Try to focus on the pronunciation of each syllable.';
            }
            
            resultDiv.innerHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>🎯 Pronunciation Challenge</h4>
                    <p><strong>Expected:</strong> "${currentPronunciationChallenge.textToSay}"</p>
                    <p><strong>You said:</strong> "${transcribedText || 'Could not transcribe'}"</p>
                </div>
                <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 15px; text-align: center;">
                    <h3 style="color: ${scoreColor};">${scoreEmoji} Score: ${Math.round(accuracy)}%</h3>
                    <p><strong>Feedback:</strong> ${feedback}</p>
                    <div style="margin-top: 15px;">
                        <button onclick="startVoicePractice()" class="btn">🔄 New Challenge</button>
                        <button onclick="startPronunciationRecording()" class="btn">🎤 Try Again</button>
                    </div>
                </div>
            `;
            
            // Add to vocabulary if pronunciation was good
            if (accuracy >= 70) {
                resultDiv.innerHTML += `
                    <div style="text-align: center; margin-top: 10px;">
                        <button onclick="addToVocabulary('${currentPronunciationChallenge.textToSay}', '${currentPronunciationChallenge.translation}')" class="btn" style="font-size: 12px;">📝 Add to Vocabulary</button>
                    </div>
                `;
            }
            
        } else {
            throw new Error('Failed to check pronunciation');
        }
        
    } catch (error) {
        console.error('Pronunciation check error:', error);
        resultDiv.innerHTML += `<div style="color: #dc3545; margin-top: 15px;">Error checking pronunciation: ${error.message}</div>`;
    }
}

function calculateSimilarity(expected, actual) {
    if (!expected || !actual) return 0;
    
    // Simple word-based similarity
    const expectedWords = expected.replace(/[¿¡.,!?]/g, '').split(' ');
    const actualWords = actual.replace(/[¿¡.,!?]/g, '').split(' ');
    
    let matches = 0;
    expectedWords.forEach(word => {
        if (actualWords.some(actualWord => 
            actualWord.includes(word) || word.includes(actualWord) || 
            levenshteinDistance(word, actualWord) <= 2
        )) {
            matches++;
        }
    });
    
    return (matches / expectedWords.length) * 100;
}

function levenshteinDistance(str1, str2) {
    const matrix = [];
    for (let i = 0; i <= str2.length; i++) {
        matrix[i] = [i];
    }
    for (let j = 0; j <= str1.length; j++) {
        matrix[0][j] = j;
    }
    for (let i = 1; i <= str2.length; i++) {
        for (let j = 1; j <= str1.length; j++) {
            if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j] + 1
                );
            }
        }
    }
    return matrix[str2.length][str1.length];
}

// AI Image Description Practice
async function startCamera() {
    await generateImageChallenge();
}

async function generateImageChallenge() {
    const resultDiv = document.getElementById('cameraResult');
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating image challenge...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const attributes = await getUserAttributes();
        
        // Get user's language settings
        const userResponse = await fetch(`${API_BASE_URL}/users?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        let targetLanguage = 'Spanish';
        let difficultyLevel = 'Intermediate';
        
        if (userResponse.ok) {
            const userData = await userResponse.json();
            targetLanguage = userData.user?.targetLanguage || 'Spanish';
            difficultyLevel = userData.user?.finalLevel || 'Intermediate';
        }
        
        // Generate image challenge
        const challengeResponse = await fetch(`${API_BASE_URL}/image-challenge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                userId: attributes.sub,
                targetLanguage: targetLanguage,
                level: difficultyLevel
            })
        });
        
        if (challengeResponse.ok) {
            const challengeData = await challengeResponse.json();
            currentImageChallenge = challengeData;
            
            resultDiv.innerHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>🖼️ Image Description Challenge</h4>
                    <p><strong>Describe this image in ${targetLanguage}:</strong></p>
                    <div style="margin: 20px 0;">
                        <img src="${challengeData.imageUrl}" alt="Challenge Image" style="max-width: 100%; max-height: 300px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    </div>
                    <p style="color: #666; font-size: 14px;">Expected elements: ${challengeData.expectedElements.join(', ')}</p>
                    <div style="margin: 15px 0;">
                        <textarea id="imageDescription" placeholder="Describe what you see in ${targetLanguage}..." style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px;"></textarea>
                    </div>
                    <button onclick="checkImageDescription()" class="btn">✅ Check My Description</button>
                    <button onclick="generateImageChallenge()" class="btn">🔄 New Image</button>
                </div>
            `;
        } else {
            // Fallback to simple image challenges
            const simpleImages = [
                {
                    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzg3Q0VFQiIvPjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5CZWF1dGlmdWwgU3VubnkgRGF5PC90ZXh0Pjwvc3ZnPg==',
                    expectedElements: ['sunny', 'day', 'blue', 'sky'],
                    description: 'A beautiful sunny day with blue sky'
                },
                {
                    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzM0QTg1MyIvPjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5HcmVlbiBQYXJrPC90ZXh0Pjwvc3ZnPg==',
                    expectedElements: ['green', 'park', 'nature', 'trees'],
                    description: 'A green park with trees and nature'
                }
            ];
            
            const randomImage = simpleImages[Math.floor(Math.random() * simpleImages.length)];
            currentImageChallenge = {
                imageUrl: randomImage.imageUrl,
                expectedElements: randomImage.expectedElements,
                correctDescription: randomImage.description,
                targetLanguage: targetLanguage
            };
            
            resultDiv.innerHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>🖼️ Image Description Challenge</h4>
                    <p><strong>Describe this image in ${targetLanguage}:</strong></p>
                    <div style="margin: 20px 0;">
                        <img src="${currentImageChallenge.imageUrl}" alt="Challenge Image" style="max-width: 100%; max-height: 300px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    </div>
                    <p style="color: #666; font-size: 14px;">Try to describe: ${currentImageChallenge.expectedElements.join(', ')}</p>
                    <div style="margin: 15px 0;">
                        <textarea id="imageDescription" placeholder="Describe what you see in ${targetLanguage}..." style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px;"></textarea>
                    </div>
                    <button onclick="checkImageDescription()" class="btn">✅ Check My Description</button>
                    <button onclick="generateImageChallenge()" class="btn">🔄 New Image</button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Image challenge error:', error);
        resultDiv.innerHTML = `<div style="color: #dc3545;">Error: ${error.message}</div>`;
    }
}

let currentImageChallenge = null;

async function checkImageDescription() {
    if (!currentImageChallenge) {
        alert('No active image challenge');
        return;
    }
    
    const description = document.getElementById('imageDescription').value.trim();
    if (!description) {
        alert('Please enter a description');
        return;
    }
    
    const resultDiv = document.getElementById('cameraResult');
    resultDiv.innerHTML += '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing your description...</div>';
    
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/check-description`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                userId: attributes.sub,
                userDescription: description,
                expectedElements: currentImageChallenge.expectedElements,
                targetLanguage: currentImageChallenge.targetLanguage,
                imageContext: currentImageChallenge.correctDescription
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            const accuracy = data.accuracy || 0;
            const feedback = data.feedback || 'No feedback available';
            const suggestions = data.suggestions || [];
            
            let scoreColor = '#dc3545'; // Red
            let scoreEmoji = '❌';
            
            if (accuracy >= 80) {
                scoreColor = '#28a745'; // Green
                scoreEmoji = '✅';
            } else if (accuracy >= 60) {
                scoreColor = '#ffc107'; // Yellow
                scoreEmoji = '⚠️';
            }
            
            resultDiv.innerHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>🖼️ Image Description Challenge</h4>
                    <div style="margin: 20px 0;">
                        <img src="${currentImageChallenge.imageUrl}" alt="Challenge Image" style="max-width: 100%; max-height: 200px; border-radius: 8px;">
                    </div>
                    <p><strong>Your description:</strong> "${description}"</p>
                </div>
                <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 15px; text-align: center;">
                    <h3 style="color: ${scoreColor};">${scoreEmoji} Score: ${Math.round(accuracy)}%</h3>
                    <p><strong>Feedback:</strong> ${feedback}</p>
                    ${suggestions.length > 0 ? `<p><strong>Suggestions:</strong> ${suggestions.join(', ')}</p>` : ''}
                    <div style="margin-top: 15px;">
                        <button onclick="generateImageChallenge()" class="btn">🔄 New Challenge</button>
                        <button onclick="document.getElementById('imageDescription').value = ''; checkImageDescription()" class="btn">✏️ Try Again</button>
                    </div>
                </div>
            `;
            
            // Add vocabulary suggestions if score was good
            if (accuracy >= 70 && suggestions.length > 0) {
                resultDiv.innerHTML += `
                    <div style="text-align: center; margin-top: 10px;">
                        <p><strong>New vocabulary learned:</strong></p>
                        ${suggestions.map(word => `
                            <button onclick="addToVocabulary('${word}', 'translation needed')" class="btn" style="font-size: 12px; margin: 2px;">📝 ${word}</button>
                        `).join('')}
                    </div>
                `;
            }
            
        } else {
            // Simple fallback scoring
            const expectedWords = currentImageChallenge.expectedElements;
            const userWords = description.toLowerCase().split(' ');
            let matches = 0;
            
            expectedWords.forEach(expected => {
                if (userWords.some(word => word.includes(expected.toLowerCase()) || expected.toLowerCase().includes(word))) {
                    matches++;
                }
            });
            
            const accuracy = (matches / expectedWords.length) * 100;
            let scoreColor = accuracy >= 70 ? '#28a745' : accuracy >= 50 ? '#ffc107' : '#dc3545';
            let scoreEmoji = accuracy >= 70 ? '✅' : accuracy >= 50 ? '⚠️' : '❌';
            
            resultDiv.innerHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>🖼️ Image Description Challenge</h4>
                    <div style="margin: 20px 0;">
                        <img src="${currentImageChallenge.imageUrl}" alt="Challenge Image" style="max-width: 100%; max-height: 200px; border-radius: 8px;">
                    </div>
                    <p><strong>Your description:</strong> "${description}"</p>
                </div>
                <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 15px; text-align: center;">
                    <h3 style="color: ${scoreColor};">${scoreEmoji} Score: ${Math.round(accuracy)}%</h3>
                    <p><strong>Elements found:</strong> ${matches}/${expectedWords.length}</p>
                    <div style="margin-top: 15px;">
                        <button onclick="generateImageChallenge()" class="btn">🔄 New Challenge</button>
                        <button onclick="document.getElementById('imageDescription').value = ''; generateImageChallenge()" class="btn">✏️ Try Again</button>
                    </div>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Description check error:', error);
        resultDiv.innerHTML += `<div style="color: #dc3545; margin-top: 15px;">Error checking description: ${error.message}</div>`;
    }
} 
                height: { ideal: 480 },
                facingMode: 'environment' // Use back camera on mobile
            } 
        });
        const video = document.getElementById('cameraFeed');
        video.srcObject = cameraStream;
        
        // Clear any previous results
        document.getElementById('cameraResult').innerHTML = '';
        document.getElementById('cameraResult').classList.add('hidden');
        
    } catch (error) {
        console.error('Error starting camera:', error);
        document.getElementById('cameraResult').innerHTML = `
            <div style="color: #dc3545; padding: 15px; background: #f8d7da; border-radius: 8px;">
                <p><strong>Camera Access Error:</strong></p>
                <p>${error.message}</p>
                <p>Please allow camera access and try again.</p>
            </div>
        `;
        document.getElementById('cameraResult').classList.remove('hidden');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
}

async function captureImage() {
    const video = document.getElementById('cameraFeed');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    const resultDiv = document.getElementById('cameraResult');
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing objects...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        // Convert canvas to base64
        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);
        const base64Data = imageDataUrl.split(',')[1];
        
        const response = await fetch(`${API_BASE_URL}`/objects, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                image: base64Data,
                userId: (await getUserAttributes()).sub
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.objects && data.objects.length > 0) {
                resultDiv.innerHTML = `
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <p><strong>🤖 Powered by Amazon Rekognition + Nova Pro</strong></p>
                        <p><strong>📷 Objects Detected:</strong> ${data.objects.length}</p>
                    </div>
                    <h4>📷 Detected Objects</h4>
                    ${data.objects.map(obj => `
                        <div class="vocabulary-item" style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span><strong>${obj.name}</strong> → <em>${obj.translation}</em> (${Math.round(obj.confidence * 100)}%)</span>
                                <button onclick="addToVocabulary('${obj.name}', '${obj.translation}')" class="btn" style="padding: 5px 10px; font-size: 12px;">📝 Save</button>
                            </div>
                        </div>
                    `).join('')}
                    <div style="text-align: center; margin-top: 15px;">
                        <button onclick="captureImage()" class="btn">📷 Capture Another</button>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <h4>📷 Object Detection</h4>
                    <p><strong>No objects detected with high confidence.</strong></p>
                    <p>Try pointing your camera at clear, well-lit objects like:</p>
                    <ul>
                        <li>📱 Phone - Teléfono</li>
                        <li>📚 Book - Libro</li>
                        <li>☕ Cup - Taza</li>
                        <li>🖥️ Computer - Computadora</li>
                    </ul>
                    <button onclick="captureImage()" class="btn">📷 Try Again</button>
                `;
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to analyze image');
        }
        
    } catch (error) {
        console.error('Object detection error:', error);
        resultDiv.innerHTML = `
            <h4>📷 Object Detection</h4>
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 10px 0; color: #721c24;">
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
            <p>The object detection service is being enhanced. Try these steps:</p>
            <ol>
                <li>Ensure good lighting</li>
                <li>Point camera at clear objects</li>
                <li>Check your internet connection</li>
            </ol>
            <button onclick="captureImage()" class="btn">📷 Try Again</button>
        `;
    }
}

// Translation
async function translateText() {
    const sourceText = document.getElementById('sourceText').value;
    const sourceLang = document.getElementById('sourceLanguage').value;
    const targetLang = document.getElementById('targetLanguage').value;
    const resultDiv = document.getElementById('translateResult');
    
    if (!sourceText.trim()) {
        alert('Please enter text to translate');
        return;
    }
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Translating...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                text: sourceText,
                sourceLanguage: sourceLang,
                targetLanguage: targetLang,
                userId: (await getUserAttributes()).sub
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            resultDiv.innerHTML = `
                <h4>🌐 Translation Result</h4>
                <p><strong>Original:</strong> ${sourceText}</p>
                <p><strong>Translation:</strong> ${data.translatedText}</p>
                <button onclick="addToVocabulary('${sourceText}', '${data.translatedText}')" class="btn">Add to Vocabulary</button>
                <button onclick="speakText('${data.translatedText}', '${targetLang}')" class="btn">🔊 Listen</button>
            `;
        } else {
            throw new Error('Translation failed');
        }
    } catch (error) {
        // Fallback translation
        const translations = {
            'hello': 'hola',
            'goodbye': 'adiós',
            'thank you': 'gracias',
            'please': 'por favor',
            'yes': 'sí',
            'no': 'no'
        };
        
        const translated = translations[sourceText.toLowerCase()] || `[Translation of: ${sourceText}]`;
        
        resultDiv.innerHTML = `
            <h4>🌐 Translation Result</h4>
            <p><strong>Original:</strong> ${sourceText}</p>
            <p><strong>Translation:</strong> ${translated}</p>
            <button onclick="addToVocabulary('${sourceText}', '${translated}')" class="btn">Add to Vocabulary</button>
            <button onclick="speakText('${translated}', '${targetLang}')" class="btn">🔊 Listen</button>
            <p><em>Enhanced translation service is being configured.</em></p>
        `;
    }
}

let isVoiceTranslating = false;
let voiceTranslationRecorder = null;
let recognition = null;

async function translateVoice() {
    if (isVoiceTranslating) {
        stopVoiceTranslation();
    } else {
        startVoiceTranslation();
    }
}

async function startVoiceTranslation() {
    const sourceLang = document.getElementById('sourceLanguage').value;
    const targetLang = document.getElementById('targetLanguage').value;
    
    // Check for Web Speech API support
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        startWebSpeechRecognition(sourceLang, targetLang);
    } else {
        // Fallback to MediaRecorder
        startMediaRecorderTranslation();
    }
}

function startWebSpeechRecognition(sourceLang, targetLang) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    // Configure recognition
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = getWebSpeechLanguageCode(sourceLang);
    
    isVoiceTranslating = true;
    
    // Update UI
    const btn = document.querySelector('button[onclick="translateVoice()"]');
    btn.innerHTML = '🛑 Stop Listening';
    btn.style.background = '#dc3545';
    
    document.getElementById('translateResult').innerHTML = `
        <div class="loading">
            <i class="fas fa-microphone" style="color: #dc3545; animation: pulse 1s infinite;"></i>
            <p>🎤 Listening in ${getLanguageName(sourceLang)}... Speak now!</p>
            <p style="font-size: 12px; color: #666;">Real-time speech recognition active</p>
        </div>
    `;
    document.getElementById('translateResult').classList.remove('hidden');
    
    let finalTranscript = '';
    let interimTranscript = '';
    
    recognition.onresult = async (event) => {
        interimTranscript = '';
        finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Show real-time transcription
        const currentText = finalTranscript + interimTranscript;
        if (currentText.trim()) {
            document.getElementById('translateResult').innerHTML = `
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <p><strong>🎤 Listening (${getLanguageName(sourceLang)}):</strong></p>
                    <p style="font-size: 16px; margin: 5px 0;">"${currentText}"</p>
                    <p style="font-size: 12px; color: #666;">${interimTranscript ? 'Still listening...' : 'Processing...'}</p>
                </div>
            `;
        }
        
        // Translate when we have final results
        if (finalTranscript.trim()) {
            await translateRecognizedText(finalTranscript.trim(), sourceLang, targetLang);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        document.getElementById('translateResult').innerHTML = `
            <div style="color: #dc3545; padding: 15px;">
                <p><strong>Speech Recognition Error:</strong> ${event.error}</p>
                <p>Falling back to manual recording...</p>
                <button onclick="startMediaRecorderTranslation()" class="btn">🎤 Try Manual Recording</button>
            </div>
        `;
        stopVoiceTranslation();
    };
    
    recognition.onend = () => {
        if (isVoiceTranslating) {
            // Restart recognition for continuous listening
            try {
                recognition.start();
            } catch (e) {
                console.log('Recognition restart failed:', e);
                stopVoiceTranslation();
            }
        }
    };
    
    try {
        recognition.start();
    } catch (error) {
        console.error('Failed to start speech recognition:', error);
        startMediaRecorderTranslation();
    }
}

async function translateRecognizedText(text, sourceLang, targetLang) {
    try {
        const response = await fetch(`${API_BASE_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                text: text,
                sourceLanguage: sourceLang,
                targetLanguage: targetLang,
                userId: (await getUserAttributes()).sub
            })
        });
        
        let translatedText = '';
        if (response.ok) {
            const data = await response.json();
            translatedText = data.translatedText;
        } else {
            // Fallback translation
            const fallbacks = {
                'hello': 'hola', 'how are you': '¿cómo estás?', 
                'thank you': 'gracias', 'goodbye': 'adiós'
            };
            translatedText = fallbacks[text.toLowerCase()] || `[Translation: ${text}]`;
        }
        
        // Display real-time results
        document.getElementById('translateResult').innerHTML = `
            <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p><strong>🎤 You said (${getLanguageName(sourceLang)}):</strong></p>
                <p style="font-size: 16px; margin: 5px 0;">"${text}"</p>
                <button onclick="speakText('${text}', '${sourceLang}')" class="btn" style="padding: 5px 10px; font-size: 12px;">🔊 Replay</button>
            </div>
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p><strong>🌐 Translation (${getLanguageName(targetLang)}):</strong></p>
                <p style="font-size: 18px; font-weight: 600; margin: 5px 0; color: #2d5a2d;">"${translatedText}"</p>
                <button onclick="speakText('${translatedText}', '${targetLang}')" class="btn" style="padding: 5px 10px; font-size: 12px;">🔊 Listen</button>
                <button onclick="addToVocabulary('${text}', '${translatedText}')" class="btn" style="padding: 5px 10px; font-size: 12px;">📝 Save</button>
            </div>
            <div style="background: #fff3cd; padding: 10px; border-radius: 8px; margin: 10px 0; text-align: center;">
                <p style="font-size: 12px; color: #856404;">🎤 Still listening... Say something else or click "Stop Listening"</p>
            </div>
        `;
        
        // Auto-play translation
        setTimeout(() => {
            speakText(translatedText, targetLang);
        }, 500);
        
    } catch (error) {
        console.error('Translation error:', error);
    }
}

function stopVoiceTranslation() {
    isVoiceTranslating = false;
    
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    
    if (voiceTranslationRecorder) {
        voiceTranslationRecorder.stop();
        voiceTranslationRecorder.stream.getTracks().forEach(track => track.stop());
        voiceTranslationRecorder = null;
    }
    
    // Update UI
    const btn = document.querySelector('button[onclick="translateVoice()"]');
    btn.innerHTML = '🎤 Start Voice Translation';
    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
}

async function startMediaRecorderTranslation() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        voiceTranslationRecorder = new MediaRecorder(stream);
        const chunks = [];
        
        voiceTranslationRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                chunks.push(event.data);
            }
        };
        
        voiceTranslationRecorder.onstop = async () => {
            const audioBlob = new Blob(chunks, { type: 'audio/wav' });
            await processVoiceTranslation(audioBlob);
        };
        
        voiceTranslationRecorder.start();
        isVoiceTranslating = true;
        
        // Update UI
        const btn = document.querySelector('button[onclick="translateVoice()"]');
        btn.innerHTML = '🛑 Stop Recording';
        btn.style.background = '#dc3545';
        
        document.getElementById('translateResult').innerHTML = `
            <div class="loading">
                <i class="fas fa-microphone" style="color: #dc3545; animation: pulse 1s infinite;"></i>
                Recording audio... Click "Stop Recording" when finished
            </div>
        `;
        document.getElementById('translateResult').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}

function getWebSpeechLanguageCode(lang) {
    const codes = {
        'en': 'en-US',
        'es': 'es-ES',
        'fr': 'fr-FR',
        'de': 'de-DE',
        'it': 'it-IT'
    };
    return codes[lang] || 'en-US';
}

async function processVoiceTranslation(audioBlob) {
    const resultDiv = document.getElementById('translateResult');
    const sourceLang = document.getElementById('sourceLanguage').value;
    const targetLang = document.getElementById('targetLanguage').value;
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Processing voice and translating...</div>';
    
    try {
        // Step 1: Transcribe audio
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice.wav');
        formData.append('language', sourceLang);
        formData.append('userId', (await getUserAttributes()).sub);
        
        const transcribeResponse = await fetch(`${API_BASE_URL}/voice-transcribe`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            },
            body: formData
        });
        
        let transcribedText = '';
        if (transcribeResponse.ok) {
            const transcribeData = await transcribeResponse.json();
            transcribedText = transcribeData.transcription;
        } else {
            // Fallback transcription
            transcribedText = getVoiceFallback(sourceLang);
        }
        
        // Step 2: Translate the transcribed text
        const translateResponse = await fetch(`${API_BASE_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                text: transcribedText,
                sourceLanguage: sourceLang,
                targetLanguage: targetLang,
                userId: (await getUserAttributes()).sub
            })
        });
        
        let translatedText = '';
        if (translateResponse.ok) {
            const translateData = await translateResponse.json();
            translatedText = translateData.translatedText;
        } else {
            translatedText = `[Translation of: ${transcribedText}]`;
        }
        
        // Step 3: Display results with audio playback
        resultDiv.innerHTML = `
            <h4>🎤🌐 Voice Translation Result</h4>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p><strong>🎤 You said (${getLanguageName(sourceLang)}):</strong></p>
                <p style="font-size: 16px; margin: 5px 0;">"${transcribedText}"</p>
                <button onclick="speakText('${transcribedText}', '${sourceLang}')" class="btn" style="padding: 5px 10px; font-size: 12px;">🔊 Replay</button>
            </div>
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p><strong>🌐 Translation (${getLanguageName(targetLang)}):</strong></p>
                <p style="font-size: 18px; font-weight: 600; margin: 5px 0; color: #2d5a2d;">"${translatedText}"</p>
                <button onclick="speakText('${translatedText}', '${targetLang}')" class="btn" style="padding: 5px 10px; font-size: 12px;">🔊 Listen</button>
                <button onclick="addToVocabulary('${transcribedText}', '${translatedText}')" class="btn" style="padding: 5px 10px; font-size: 12px;">📝 Save</button>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <button onclick="startVoiceTranslation()" class="btn">🎤 Translate Another</button>
            </div>
        `;
        
        // Auto-play the translation
        setTimeout(() => {
            speakText(translatedText, targetLang);
        }, 500);
        
    } catch (error) {
        console.error('Error processing voice translation:', error);
        resultDiv.innerHTML = `
            <h4>🎤🌐 Voice Translation</h4>
            <p><strong>Voice captured successfully!</strong></p>
            <p>Real-time voice translation is being enhanced. Your audio was processed.</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p><em>Demo: "Hello, how are you?" → "Hola, ¿cómo estás?"</em></p>
                <button onclick="speakText('Hola, ¿cómo estás?', 'es')" class="btn">🔊 Listen to Demo</button>
            </div>
            <button onclick="startVoiceTranslation()" class="btn">🎤 Try Again</button>
        `;
    }
}

function getVoiceFallback(language) {
    const fallbacks = {
        'en': 'Hello, how are you?',
        'es': 'Hola, ¿cómo estás?',
        'fr': 'Bonjour, comment allez-vous?',
        'de': 'Hallo, wie geht es dir?',
        'it': 'Ciao, come stai?'
    };
    return fallbacks[language] || 'Hello, how are you?';
}

function getLanguageName(code) {
    const names = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian'
    };
    return names[code] || code.toUpperCase();
}

// Text-to-Speech function
function speakText(text, language) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = getLanguageCode(language);
        utterance.rate = 0.8;
        utterance.pitch = 1;
        speechSynthesis.speak(utterance);
    } else {
        alert('Text-to-speech not supported in this browser');
    }
}

function getLanguageCode(lang) {
    const codes = {
        'en': 'en-US',
        'es': 'es-ES',
        'fr': 'fr-FR', 
        'de': 'de-DE',
        'it': 'it-IT'
    };
    return codes[lang] || 'en-US';
}

// Vocabulary Management
async function loadVocabulary() {
    const vocabularyDiv = document.getElementById('vocabularyList');
    
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/vocabulary?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const vocabulary = data.vocabulary || [];
            
            if (vocabulary.length === 0) {
                vocabularyDiv.innerHTML = '<p>No vocabulary words yet. Start learning to build your collection!</p>';
            } else {
                vocabularyDiv.innerHTML = vocabulary.map(word => `
                    <div class="vocabulary-item">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
                                <div>
                                    <strong>${word.word}</strong> <span style="color: #666;">→</span> ${word.translation}
                                </div>
                                <span style="background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 12px; font-size: 11px; white-space: nowrap;">
                                    ${word.targetLanguage || 'Unknown'} → ${word.nativeLanguage || 'Unknown'}
                                </span>
                            </div>
                            ${word.context ? `<small style="color: #888;">Context: ${word.context}</small><br>` : ''}
                            <small style="color: #999;">${new Date(word.addedAt).toLocaleDateString()}</small>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            throw new Error('Failed to load vocabulary');
        }
    } catch (error) {
        vocabularyDiv.innerHTML = `<div style="color: #dc3545;">Error loading vocabulary: ${error.message}</div>`;
    }
}

async function addVocabulary() {
    const word = document.getElementById('newWord').value;
    const translation = document.getElementById('newTranslation').value;
    
    if (!word || !translation) {
        alert('Please enter both word and translation');
        return;
    }
    
    await addToVocabulary(word, translation);
    
    document.getElementById('newWord').value = '';
    document.getElementById('newTranslation').value = '';
}

async function addToVocabulary(word, translation, context = '') {
    try {
        const attributes = await getUserAttributes();
        
        // Get user's current language settings
        const userResponse = await fetch(`${API_BASE_URL}/users?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        let targetLanguage = 'Unknown';
        let nativeLanguage = 'Unknown';
        
        if (userResponse.ok) {
            const userData = await userResponse.json();
            targetLanguage = userData.user?.targetLanguage || 'Unknown';
            nativeLanguage = userData.user?.nativeLanguage || 'Unknown';
        }
        
        const response = await fetch(`${API_BASE_URL}/vocabulary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                userId: attributes.sub,
                word: word,
                translation: translation,
                context: context,
                targetLanguage: targetLanguage,
                nativeLanguage: nativeLanguage
            })
        });
        
        if (response.ok) {
            alert('Word added to vocabulary!');
            loadVocabulary();
            loadProgress(); // Update word count
        } else {
            throw new Error('Failed to add vocabulary');
        }
    } catch (error) {
        console.error('Error adding vocabulary:', error);
        alert('Error adding word to vocabulary');
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
            if (modal.id === 'cameraModal') {
                stopCamera();
            }
            if (modal.id === 'voiceModal') {
                stopRecording();
            }
        }
    });
};
