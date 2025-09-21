#!/usr/bin/env python3
"""
Detailed consistency checker to find exact language inconsistencies
"""

import os
import re

def analyze_lambda_function(filepath):
    """Analyze a Lambda function for language usage patterns"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    issues = []
    
    # Check what global config values are being used
    global_native_usage = re.findall(r"LANGUAGE_CONFIG\['GLOBAL_NATIVE_LANGUAGE[^']*'\]", content)
    global_target_usage = re.findall(r"LANGUAGE_CONFIG\['GLOBAL_TARGET_LANGUAGE[^']*'\]", content)
    
    # Check parameter names being used
    param_patterns = [
        ('targetLanguage', re.findall(r"['\"]targetLanguage['\"]", content)),
        ('nativeLanguage', re.findall(r"['\"]nativeLanguage['\"]", content)),
        ('targetLanguageName', re.findall(r"['\"]targetLanguageName['\"]", content)),
        ('nativeLanguageName', re.findall(r"['\"]nativeLanguageName['\"]", content)),
        ('sourceLanguage', re.findall(r"['\"]sourceLanguage['\"]", content)),
    ]
    
    # Check fallback values
    fallback_patterns = [
        ('Spanish fallback', re.findall(r"['\"]Spanish['\"]", content)),
        ('English fallback', re.findall(r"['\"]English['\"]", content)),
        ('Malay fallback', re.findall(r"['\"]Malay['\"]", content)),
        ('en fallback', re.findall(r"['\"]en['\"]", content)),
        ('ms fallback', re.findall(r"['\"]ms['\"]", content)),
        ('es fallback', re.findall(r"['\"]es['\"]", content)),
    ]
    
    return {
        'filename': filename,
        'global_native_usage': global_native_usage,
        'global_target_usage': global_target_usage,
        'param_patterns': [(name, matches) for name, matches in param_patterns if matches],
        'fallback_patterns': [(name, matches) for name, matches in fallback_patterns if matches],
        'has_language_config_import': 'from language_config import' in content or 'import language_config' in content
    }

def main():
    lambda_dir = '/Users/syuen/language-learning-app/infrastructure/lambda'
    
    print("🔍 DETAILED LANGUAGE CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    for filename in sorted(os.listdir(lambda_dir)):
        if filename.endswith('.py') and filename != 'language_config.py':
            filepath = os.path.join(lambda_dir, filename)
            analysis = analyze_lambda_function(filepath)
            
            print(f"\n📁 {analysis['filename']}")
            print(f"   Import: {'✅' if analysis['has_language_config_import'] else '❌'}")
            
            if analysis['global_native_usage']:
                print(f"   Native: {analysis['global_native_usage']}")
            if analysis['global_target_usage']:
                print(f"   Target: {analysis['global_target_usage']}")
            
            if analysis['param_patterns']:
                print(f"   Params: {[name for name, _ in analysis['param_patterns']]}")
            
            if analysis['fallback_patterns']:
                print(f"   ❌ Hardcoded: {[(name, len(matches)) for name, matches in analysis['fallback_patterns']]}")

if __name__ == "__main__":
    main()
