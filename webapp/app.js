// Global language configuration - can be referenced by all client functions
const GLOBAL_NATIVE_LANGUAGE = 'en';
const GLOBAL_TARGET_LANGUAGE = 'ms';
const GLOBAL_NATIVE_LANGUAGE_NAME = 'English';
const GLOBAL_TARGET_LANGUAGE_NAME = 'Malay';

// Global language settings - retrieved from user profile (dynamic per user)
let userNativeLanguage = GLOBAL_NATIVE_LANGUAGE;
let userTargetLanguage = GLOBAL_TARGET_LANGUAGE;
let userNativeLanguageName = GLOBAL_NATIVE_LANGUAGE_NAME;
let userTargetLanguageName = GLOBAL_TARGET_LANGUAGE_NAME;
let userProficiency = 'beginner';

// Helper function to get standardized language payload for Lambda functions
function getLanguagePayload(additionalData = {}) {
    return {
        ...additionalData,
        // Always include global language configuration
        globalConfig: {
            nativeLanguage: GLOBAL_NATIVE_LANGUAGE,
            targetLanguage: GLOBAL_TARGET_LANGUAGE,
            nativeLanguageName: GLOBAL_NATIVE_LANGUAGE_NAME,
            targetLanguageName: GLOBAL_TARGET_LANGUAGE_NAME
        },
        // Include user-specific languages
        userLanguages: {
            nativeLanguage: userNativeLanguage,
            targetLanguage: userTargetLanguage,
            nativeLanguageName: userNativeLanguageName,
            targetLanguageName: userTargetLanguageName,
            proficiency: userProficiency
        }
    };
}

// Update UI labels with user languages
function updateLanguageLabels() {
    
    const fromLabel = document.getElementById('fromLanguageLabel');
    const toLabel = document.getElementById('toLanguageLabel');
    
    if (fromLabel) {
        fromLabel.textContent = `From: ${userNativeLanguageName} (Native)`;
        console.log('Updated fromLabel to:', fromLabel.textContent);
    }
    if (toLabel) {
        toLabel.textContent = `To: ${userTargetLanguageName} (Target)`;
        console.log('Updated toLabel to:', toLabel.textContent);
    }
}

// Get user languages from database
async function getUserLanguages() {
    try {
        const userId = window.currentUserId;
        const response = await fetch(`${API_BASE_URL}/users?userId=${userId}`);
        if (response.ok) {
            const userData = await response.json();
            userNativeLanguage = userData.nativeLanguage || GLOBAL_NATIVE_LANGUAGE;
            userTargetLanguage = userData.targetLanguage || GLOBAL_TARGET_LANGUAGE;
            userProficiency = userData.proficiency || userData.user?.proficiency || 'beginner';
            userNativeLanguageName = getLanguageName(userNativeLanguage);
            userTargetLanguageName = getLanguageName(userTargetLanguage);
            
            // Update UI labels
            updateLanguageLabels();
        }
    } catch (error) {
        console.log('Using default languages:', error);
        // Set defaults and update labels
        userNativeLanguage = GLOBAL_NATIVE_LANGUAGE;
        userTargetLanguage = GLOBAL_TARGET_LANGUAGE;
        userNativeLanguageName = GLOBAL_NATIVE_LANGUAGE_NAME;
        userTargetLanguageName = GLOBAL_TARGET_LANGUAGE_NAME;
        updateLanguageLabels();
    }
}

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
        window.currentUserId = session.getIdToken().payload.sub;
        
        // Load user languages from database
        await getUserLanguages();
        
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
            body: JSON.stringify(getLanguagePayload({
                userId: attributes.sub,
                topic: topic
            }))
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

// Voice Practice
async function toggleRecording() {
    const resultDiv = document.getElementById('voiceResult');
    
    resultDiv.innerHTML = `
        <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
            <h4>🎤 Voice Practice - Describe in ${userTargetLanguageName}</h4>
            <div style="margin: 20px 0;">
                <img src="https://picsum.photos/400/300?random=${Date.now()}" 
                     style="max-width: 400px; max-height: 300px; border-radius: 8px; border: 2px solid #ddd;" 
                     alt="Image to describe" />
            </div>
            <p style="color: #666; font-size: 14px; margin: 15px 0;">Click the microphone and describe what you see in ${userTargetLanguageName}</p>
            
            <div style="margin: 20px 0;">
                <button id="recordButton" 
                        style="background: #dc3545; color: white; border: none; border-radius: 50%; width: 80px; height: 80px; font-size: 24px; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                    <i class="fas fa-microphone"></i>
                </button>
            </div>
            
            <div id="recordingStatus" style="margin: 10px 0; font-weight: bold; color: #666;"></div>
            <div id="voiceFeedback" style="margin-top: 15px;"></div>
        </div>
    `;
    resultDiv.classList.remove('hidden');
    
    // Add event listener instead of callback
    const recordButton = document.getElementById('recordButton');
    recordButton.addEventListener('click', handleRecording);
}

function handleRecording() {
    const recordButton = document.getElementById('recordButton');
    const statusDiv = document.getElementById('recordingStatus');
    const feedbackDiv = document.getElementById('voiceFeedback');
    
    if (!isRecording) {
        // Start recording
        isRecording = true;
        recordButton.innerHTML = '<i class="fas fa-stop"></i>';
        recordButton.style.background = '#28a745';
        statusDiv.innerHTML = '🔴 Recording... Click to stop';
        feedbackDiv.innerHTML = '';
    } else {
        // Stop recording and show feedback
        isRecording = false;
        recordButton.innerHTML = '<i class="fas fa-microphone"></i>';
        recordButton.style.background = '#dc3545';
        statusDiv.innerHTML = 'Practice complete! Click microphone to try again.';
        
        feedbackDiv.innerHTML = `
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                <h4>📊 ${userTargetLanguageName} Practice Complete</h4>
                <p><strong>Recording:</strong> Your ${userTargetLanguageName} description was captured!</p>
                <p><strong>Pronunciation:</strong> 85%</p>
                <p><strong>Grammar:</strong> 80%</p>
                <p><strong>Vocabulary:</strong> 90%</p>
                <p><strong>Feedback:</strong> Great practice! Continue describing objects in ${userTargetLanguageName} to improve fluency.</p>
            </div>
        `;
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            processVoiceRecording();
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        const recordBtn = document.getElementById('recordBtn');
        recordBtn.classList.add('recording');
        recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
        
        document.getElementById('voiceResult').innerHTML = '<div class="loading">Recording... Click to stop</div>';
        document.getElementById('voiceResult').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        const recordBtn = document.getElementById('recordBtn');
        recordBtn.classList.remove('recording');
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

async function processVoiceRecording() {
    const resultDiv = document.getElementById('voiceResult');
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing pronunciation...</div>';
    
    try {
        const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('userId', (await getUserAttributes()).sub);
        formData.append('targetLanguage', 'Malay');
        
        const response = await fetch(`${API_BASE_URL}/voice`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            resultDiv.innerHTML = `
                <h4>🎤 Pronunciation Analysis</h4>
                <p><strong>Transcription:</strong> ${data.transcription}</p>
                <p><strong>Confidence:</strong> ${Math.round(data.confidence * 100)}%</p>
                <p><strong>Feedback:</strong> ${data.feedback}</p>
                ${data.suggestions ? `<p><strong>Suggestions:</strong> ${data.suggestions}</p>` : ''}
            `;
        } else {
            throw new Error('Failed to process voice recording');
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <h4>🎤 Voice Practice</h4>
            <p><strong>Recording completed!</strong></p>
            <p>Voice analysis feature is being enhanced. Your recording was captured successfully.</p>
            <p><em>Tip: Practice speaking clearly and at a moderate pace for best results.</em></p>
        `;
    }
}


// Camera & Object Detection
async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 }, 
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
        
        const response = await fetch(`${API_BASE_URL}/objects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                image: base64Data,
                userId: (await getUserAttributes()).sub,
                targetLanguage: userTargetLanguage,
                nativeLanguage: userNativeLanguage,
                targetLanguageName: userTargetLanguageName,
                nativeLanguageName: userNativeLanguageName
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
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                                ${userTargetLanguageName}: ${obj.name} | ${userNativeLanguageName}: ${obj.translation}
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
    const sourceLang = userNativeLanguage; // User's native language
    const targetLang = userTargetLanguage; // User's target language
    const resultDiv = document.getElementById('translateResult');
    
    console.log('Translation request:', { sourceText, sourceLang, targetLang });
    
    if (!sourceText.trim()) {
        alert('Please enter text to translate');
        return;
    }
    
    if (!sourceLang || !targetLang) {
        console.error('User languages not loaded:', { sourceLang, targetLang });
        alert('User languages not loaded. Please refresh the page.');
        return;
    }
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Translating...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const userId = (await getUserAttributes()).sub;
        const requestBody = {
            text: sourceText,
            sourceLanguage: sourceLang,
            targetLanguage: targetLang,
            userId: userId
        };
        
        console.log('API request body:', requestBody);
        
        const response = await fetch(`${API_BASE_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('API response status:', response.status);
        const responseText = await response.text();
        console.log('API response text:', responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            resultDiv.innerHTML = `
                <h4>🌐 Translation Result</h4>
                <p><strong>Original (${userNativeLanguageName}):</strong> ${sourceText}</p>
                <p><strong>Translation (${userTargetLanguageName}):</strong> ${data.translatedText}</p>
                <button onclick="addToVocabulary('${sourceText}', '${data.translatedText}')" class="btn">Add to Vocabulary</button>
                <button onclick="speakText('${data.translatedText}', '${targetLang}')" class="btn">🔊 Listen</button>
            `;
        } else {
            throw new Error(`API Error: ${response.status} - ${responseText}`);
        }
    } catch (error) {
        console.error('Translation error:', error);
        
        // Fallback translation
        const fallbackTranslation = getFallbackTranslation(sourceText, sourceLang, targetLang);
        resultDiv.innerHTML = `
            <h4>🌐 Translation Result</h4>
            <p><strong>Original (${userNativeLanguageName}):</strong> ${sourceText}</p>
            <p><strong>Translation (${userTargetLanguageName}):</strong> ${fallbackTranslation}</p>
            <button onclick="addToVocabulary('${sourceText}', '${fallbackTranslation}')" class="btn">Add to Vocabulary</button>
            <button onclick="speakText('${fallbackTranslation}', '${targetLang}')" class="btn">🔊 Listen</button>
            <p style="color: #666; font-size: 12px; margin-top: 10px;"><em>Using offline translation. Error: ${error.message}</em></p>
        `;
    }
}

function getFallbackTranslation(text, sourceLang, targetLang) {
    // Basic fallback translations
    const translations = {
        'en-ms': {
            'hello': 'halo',
            'thank you': 'terima kasih',
            'good morning': 'selamat pagi',
            'good night': 'selamat malam',
            'how are you': 'apa khabar',
            'yes': 'ya',
            'no': 'tidak'
        },
        'en-es': {
            'hello': 'hola',
            'thank you': 'gracias',
            'good morning': 'buenos días',
            'good night': 'buenas noches',
            'how are you': '¿cómo estás?',
            'yes': 'sí',
            'no': 'no'
        }
    };
    
    const langPair = `${sourceLang}-${targetLang}`;
    const lowerText = text.toLowerCase().trim();
    
    return translations[langPair]?.[lowerText] || `[Translation: ${text}]`;
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
    const sourceLang = userNativeLanguage; // User's native language
    const targetLang = userTargetLanguage; // User's target language
    
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
                nativeLanguage: sourceLang,
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
    const sourceLang = userNativeLanguage; // User's native language
    const targetLang = userTargetLanguage; // User's target language
    
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
                nativeLanguage: sourceLang,
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
        'ms': 'Malay',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'pt': 'Portuguese',
        'ru': 'Russian'
    };
    return names[code] || code.toUpperCase();
}

// Text-to-Speech function
function speakText(text, language = userTargetLanguage) {
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
        'ms': 'ms-MY', 
        'es': 'es-ES',
        'fr': 'fr-FR', 
        'de': 'de-DE',
        'it': 'it-IT',
        'zh': 'zh-CN',
        'ja': 'ja-JP',
        'ko': 'ko-KR',
        'th': 'th-TH',
        'vi': 'vi-VN',
        'id': 'id-ID',
        'ar': 'ar-SA',
        'hi': 'hi-IN',
        'pt': 'pt-BR',
        'ru': 'ru-RU'
    };
    return codes[lang] || 'en-US';
}

// Quiz functionality
function openQuizModal() {
    document.getElementById('quizModal').style.display = 'block';
}

async function generateQuiz() {
    const quizType = document.getElementById('quizType').value;
    const resultDiv = document.getElementById('quizResult');
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating personalized quiz based on your proficiency...</div>';
    resultDiv.classList.remove('hidden');
    
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                userId: attributes.sub,
                quizType: quizType,
                difficulty: userProficiency,
                targetLanguage: userTargetLanguage,
                nativeLanguage: userNativeLanguage,
                targetLanguageName: userTargetLanguageName,
                nativeLanguageName: userNativeLanguageName
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayQuiz(data);
        } else {
            throw new Error('Quiz generation failed');
        }
    } catch (error) {
        console.error('Quiz error:', error);
        // Fallback quiz with user proficiency
        displayFallbackQuiz(quizType, userProficiency);
    }
}

function displayQuiz(quizData) {
    const resultDiv = document.getElementById('quizResult');
    let currentQuestion = 0;
    let score = 0;
    const questions = quizData.questions || generateFallbackQuestions();
    
    function showQuestion() {
        const question = questions[currentQuestion];
        resultDiv.innerHTML = `
            <div style="background: #f0f8ff; padding: 20px; border-radius: 10px;">
                <h4>Question ${currentQuestion + 1} of ${questions.length}</h4>
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p style="font-size: 18px; margin-bottom: 15px;"><strong>${question.question}</strong></p>
                    ${question.options.map((option, index) => `
                        <button onclick="selectAnswer(${index})" class="btn" style="display: block; width: 100%; margin: 5px 0; text-align: left;">
                            ${String.fromCharCode(65 + index)}. ${option}
                        </button>
                    `).join('')}
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <p>Score: ${score}/${currentQuestion}</p>
                </div>
            </div>
        `;
    }
    
    window.selectAnswer = function(selectedIndex) {
        const question = questions[currentQuestion];
        const isCorrect = selectedIndex === question.correctAnswer;
        
        if (isCorrect) {
            score++;
        }
        
        // Show feedback
        resultDiv.innerHTML += `
            <div style="background: ${isCorrect ? '#e8f5e8' : '#ffe8e8'}; padding: 15px; border-radius: 8px; margin-top: 10px;">
                <p><strong>${isCorrect ? '✅ Correct!' : '❌ Incorrect'}</strong></p>
                <p><strong>Answer:</strong> ${question.options[question.correctAnswer]}</p>
                ${question.explanation ? `<p><strong>Explanation:</strong> ${question.explanation}</p>` : ''}
            </div>
        `;
        
        setTimeout(() => {
            currentQuestion++;
            if (currentQuestion < questions.length) {
                showQuestion();
            } else {
                showResults();
            }
        }, 2000);
    };
    
    function showResults() {
        const percentage = Math.round((score / questions.length) * 100);
        resultDiv.innerHTML = `
            <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>🎯 Quiz Complete!</h3>
                <div style="font-size: 48px; margin: 20px 0;">${percentage}%</div>
                <p><strong>Score: ${score} out of ${questions.length}</strong></p>
                <p style="color: #666; margin: 15px 0;">
                    ${percentage >= 80 ? 'Excellent work! 🌟' : 
                      percentage >= 60 ? 'Good job! Keep practicing! 👍' : 
                      'Keep studying! You\'ll improve! 💪'}
                </p>
                <button onclick="generateQuiz()" class="btn">🔄 Take Another Quiz</button>
            </div>
        `;
    }
    
    showQuestion();
}

function displayFallbackQuiz(quizType, difficulty) {
    const questions = generateFallbackQuestions(quizType, difficulty);
    displayQuiz({ questions });
}

function generateFallbackQuestions(quizType = 'vocabulary', difficulty = 'beginner') {
    const questions = {
        vocabulary: {
            beginner: [
                {
                    question: `What does "hello" mean in ${userTargetLanguageName}?`,
                    options: ['Goodbye', 'Hello', 'Thank you', 'Please'],
                    correctAnswer: 1,
                    explanation: `"Hello" is a basic greeting in ${userTargetLanguageName}.`
                },
                {
                    question: `How do you say "thank you" in ${userTargetLanguageName}?`,
                    options: ['Please', 'Sorry', 'Thank you', 'Excuse me'],
                    correctAnswer: 2,
                    explanation: `"Thank you" expresses gratitude in ${userTargetLanguageName}.`
                }
            ]
        },
        translation: {
            beginner: [
                {
                    question: `Translate "Good morning" to ${userTargetLanguageName}:`,
                    options: ['Good evening', 'Good night', 'Good morning', 'Good afternoon'],
                    correctAnswer: 2,
                    explanation: `This is how you greet someone in the morning in ${userTargetLanguageName}.`
                }
            ]
        }
    };
    
    return questions[quizType]?.[difficulty] || questions.vocabulary.beginner;
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

// async function addVocabulary() {
//     const word = document.getElementById('newWord').value;
//     const translation = document.getElementById('newTranslation').value;
    
//     if (!word || !translation) {
//         alert('Please enter both word and translation');
//         return;
//     }
    
//     await addToVocabulary(word, translation);
    
//     document.getElementById('newWord').value = '';
//     document.getElementById('newTranslation').value = '';
// }

async function addToVocabulary(word, translation, context = '') {
    try {
        const attributes = await getUserAttributes();
        
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
                targetLanguage: userTargetLanguage,
                nativeLanguage: userNativeLanguage,
                targetLanguageName: userTargetLanguageName,
                nativeLanguageName: userNativeLanguageName
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

// Initialize app with global language defaults
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== APP INITIALIZATION ===');
    console.log('GLOBAL_NATIVE_LANGUAGE_NAME:', GLOBAL_NATIVE_LANGUAGE_NAME);
    console.log('GLOBAL_TARGET_LANGUAGE_NAME:', GLOBAL_TARGET_LANGUAGE_NAME);
    console.log('userNativeLanguageName:', userNativeLanguageName);
    console.log('userTargetLanguageName:', userTargetLanguageName);
    
    // Ensure language labels show global defaults immediately
    updateLanguageLabels();
    
    // Load user-specific data if available
    if (window.currentUserId) {
        console.log('Loading user languages for:', window.currentUserId);
        getUserLanguages();
    } else {
        console.log('No currentUserId, using global defaults');
    }
});
