// Test what values are actually displayed
const GLOBAL_NATIVE_LANGUAGE = 'en';
const GLOBAL_TARGET_LANGUAGE = 'ms';
const GLOBAL_NATIVE_LANGUAGE_NAME = 'English';
const GLOBAL_TARGET_LANGUAGE_NAME = 'Malay';

let userNativeLanguageName = GLOBAL_NATIVE_LANGUAGE_NAME;
let userTargetLanguageName = GLOBAL_TARGET_LANGUAGE_NAME;

console.log('=== WHAT SCREEN SHOWS ===');
console.log(`From: ${userNativeLanguageName} (Native)`);
console.log(`To: ${userTargetLanguageName} (Target)`);
console.log('');
console.log('=== GLOBAL CONSTANTS ===');
console.log(`GLOBAL_NATIVE_LANGUAGE_NAME: ${GLOBAL_NATIVE_LANGUAGE_NAME}`);
console.log(`GLOBAL_TARGET_LANGUAGE_NAME: ${GLOBAL_TARGET_LANGUAGE_NAME}`);
console.log('');
console.log('=== CONSISTENCY CHECK ===');
console.log(`Native consistent: ${userNativeLanguageName === GLOBAL_NATIVE_LANGUAGE_NAME}`);
console.log(`Target consistent: ${userTargetLanguageName === GLOBAL_TARGET_LANGUAGE_NAME}`);
