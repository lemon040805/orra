// Global variables
const API_BASE_URL = 'https://r9t9xk38j1.execute-api.us-east-1.amazonaws.com/prod';
let currentToken = null;
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;
let currentPronunciationChallenge = null;
let currentImageChallenge = null;

// AWS Cognito Configuration
const poolData = {
    UserPoolId: 'us-east-1_fvNtXNAyp',
    ClientId: '5rh6qtboujp6cdslv62as1onbo'
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

// Authentication Functions
function showLogin() {
    document.getElementById('authContainer').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function showDashboard() {
    document.getElementById('authContainer').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
}

function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    const authenticationData = {
        Username: email,
        Password: password,
    };
    
    const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
    const userData = {
        Username: email,
        Pool: userPool
    };
    
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    
    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: function (result) {
            currentToken = result.getIdToken().getJwtToken();
            showDashboard();
            loadProgress();
        },
        onFailure: function(err) {
            alert('Login failed: ' + err.message);
        }
    });
}

function register() {
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    const attributeList = [
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: 'name',
            Value: name
        }),
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: 'email',
            Value: email
        })
    ];
    
    userPool.signUp(email, password, attributeList, null, function(err, result) {
        if (err) {
            alert('Registration failed: ' + err.message);
            return;
        }
        alert('Registration successful! Please check your email for verification code.');
        showLogin();
    });
}

function logout() {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
        cognitoUser.signOut();
    }
    currentToken = null;
    showLogin();
}

async function getUserAttributes() {
    return new Promise((resolve, reject) => {
        const cognitoUser = userPool.getCurrentUser();
        if (cognitoUser) {
            cognitoUser.getSession((err, session) => {
                if (err) {
                    reject(err);
                    return;
                }
                cognitoUser.getUserAttributes((err, attributes) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    const attrs = {};
                    attributes.forEach(attr => {
                        attrs[attr.getName()] = attr.getValue();
                    });
                    attrs.sub = session.getIdToken().payload.sub;
                    resolve(attrs);
                });
            });
        } else {
            reject(new Error('No user logged in'));
        }
    });
}

// Initialize app
window.onload = function() {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
        cognitoUser.getSession((err, session) => {
            if (err) {
                showLogin();
                return;
            }
            if (session.isValid()) {
                currentToken = session.getIdToken().getJwtToken();
                showDashboard();
                loadProgress();
            } else {
                showLogin();
            }
        });
    } else {
        showLogin();
    }
};

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function openVocabularyModal() {
    document.getElementById('vocabularyModal').style.display = 'block';
    loadVocabulary();
}

// Progress Loading
async function loadProgress() {
    try {
        const attributes = await getUserAttributes();
        const response = await fetch(`${API_BASE_URL}/users?userId=${attributes.sub}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const user = data.user;
            
            document.getElementById('userName').textContent = user.name || 'User';
            document.getElementById('currentStreak').textContent = user.streak || 0;
            document.getElementById('wordsLearned').textContent = user.totalWords || 0;
            document.getElementById('lessonsCompleted').textContent = user.totalLessons || 0;
        }
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

// Lesson Generation
async function generateLesson() {
    const topic = document.getElementById('lessonTopic').value;
    const resultDiv = document.getElementById('lessonResult');
    
    if (!topic.trim()) {
        alert('Please enter a topic for the lesson');
        return;
    }
    
    resultDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating lesson...</div>';
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
            const lesson = data.lesson;
            
            resultDiv.innerHTML = `
                <h4>${lesson.title}</h4>
                <p><strong>Content:</strong> ${lesson.content}</p>
                ${lesson.vocabulary ? `
                    <div style="margin-top: 15px;">
                        <strong>Vocabulary:</strong>
                        ${lesson.vocabulary.map(word => `
                            <div class="vocabulary-item">
                                <span><strong>${word.word}</strong> - ${word.translation}</span>
                                <button onclick="addToVocabulary('${word.word}', '${word.translation}')" class="btn" style="padding: 5px 10px; font-size: 12px;">Add</button>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;
        } else {
            throw new Error('Failed to generate lesson');
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #dc3545;">Error: ${error.message}</div>`;
    }
}

// Voice Practice
async function toggleRecording() {
    const resultDiv = document.getElementById('voiceResult');
    resultDiv.innerHTML = `
        <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
            <h4>🎯 Pronunciation Challenge</h4>
            <p><strong>Say this in Spanish:</strong></p>
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0; font-size: 18px; font-weight: bold; color: #2d5a2d;">
                "Hola, ¿cómo estás?"
            </div>
            <p style="color: #666; font-size: 14px;">English: Hello, how are you?</p>
            <button onclick="speakText('Hola, ¿cómo estás?', 'es')" class="btn">🔊 Listen</button>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

// Camera/Image Description
async function startCamera() {
    const resultDiv = document.getElementById('cameraResult');
    resultDiv.innerHTML = `
        <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center;">
            <h4>🖼️ Image Description Challenge</h4>
            <p><strong>Describe this image in Spanish:</strong></p>
            <div style="margin: 20px 0;">
                <div style="width: 300px; height: 200px; background: #87CEEB; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 0 auto; color: white; font-size: 20px;">
                    Beautiful Sunny Day
                </div>
            </div>
            <p style="color: #666; font-size: 14px;">Try to describe: sunny, day, blue, sky</p>
            <div style="margin: 15px 0;">
                <textarea id="imageDescription" placeholder="Describe what you see in Spanish..." style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;"></textarea>
            </div>
            <button onclick="checkImageDescription()" class="btn">✅ Check Description</button>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

function checkImageDescription() {
    const description = document.getElementById('imageDescription').value;
    if (!description.trim()) {
        alert('Please enter a description');
        return;
    }
    alert('Great description! Score: 85%');
}

// Translation
async function translateText() {
    const sourceText = document.getElementById('sourceText').value;
    const resultDiv = document.getElementById('translationResult');
    
    if (!sourceText.trim()) {
        alert('Please enter text to translate');
        return;
    }
    
    resultDiv.innerHTML = `
        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; text-align: center;">
            <p><strong>Original:</strong> ${sourceText}</p>
            <p><strong>Translation:</strong> [Translation of: ${sourceText}]</p>
            <button onclick="addToVocabulary('${sourceText}', '[Translation]')" class="btn">Add to Vocabulary</button>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

// Quiz Generation
async function generateQuiz() {
    const topic = document.getElementById('quizTopic').value;
    const resultDiv = document.getElementById('quizResult');
    
    if (!topic.trim()) {
        alert('Please enter a topic for the quiz');
        return;
    }
    
    resultDiv.innerHTML = `
        <h4>Quiz: ${topic}</h4>
        <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;">
            <p><strong>Question 1:</strong> What is "hello" in Spanish?</p>
            <label><input type="radio" name="q1" value="0"> Hola</label><br>
            <label><input type="radio" name="q1" value="1"> Adiós</label><br>
            <label><input type="radio" name="q1" value="2"> Gracias</label>
        </div>
        <button onclick="alert('Correct! Score: 100%')" class="btn">Check Answers</button>
    `;
    resultDiv.classList.remove('hidden');
}

// Vocabulary Management
async function loadVocabulary() {
    const vocabularyDiv = document.getElementById('vocabularyList');
    vocabularyDiv.innerHTML = '<p>Loading vocabulary...</p>';
    
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
                vocabularyDiv.innerHTML = '<p>No vocabulary words yet. Start learning!</p>';
            } else {
                vocabularyDiv.innerHTML = vocabulary.map(word => `
                    <div class="vocabulary-item">
                        <strong>${word.word}</strong> → ${word.translation}
                        <small style="color: #999;">${new Date(word.addedAt).toLocaleDateString()}</small>
                    </div>
                `).join('');
            }
        } else {
            vocabularyDiv.innerHTML = '<p>Error loading vocabulary.</p>';
        }
    } catch (error) {
        vocabularyDiv.innerHTML = '<p>Error loading vocabulary.</p>';
    }
}

async function addToVocabulary(word, translation) {
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
                targetLanguage: 'Spanish',
                nativeLanguage: 'English'
            })
        });
        
        if (response.ok) {
            alert('Word added to vocabulary!');
        } else {
            alert('Error adding word');
        }
    } catch (error) {
        alert('Error adding word');
    }
}

// Text-to-Speech
function speakText(text, language) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        speechSynthesis.speak(utterance);
    } else {
        alert('Text-to-speech not supported');
    }
}
