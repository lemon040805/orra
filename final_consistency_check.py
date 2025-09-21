#!/usr/bin/env python3
"""
Final verification that ALL Lambda functions use EXACTLY the same language configuration
"""

import os
import re

def extract_language_values(filepath):
    """Extract all language-related values from a Lambda function"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    
    # Extract all global config references
    global_refs = {
        'GLOBAL_NATIVE_LANGUAGE': re.findall(r"LANGUAGE_CONFIG\['GLOBAL_NATIVE_LANGUAGE'\]", content),
        'GLOBAL_TARGET_LANGUAGE': re.findall(r"LANGUAGE_CONFIG\['GLOBAL_TARGET_LANGUAGE'\]", content),
        'GLOBAL_NATIVE_LANGUAGE_NAME': re.findall(r"LANGUAGE_CONFIG\['GLOBAL_NATIVE_LANGUAGE_NAME'\]", content),
        'GLOBAL_TARGET_LANGUAGE_NAME': re.findall(r"LANGUAGE_CONFIG\['GLOBAL_TARGET_LANGUAGE_NAME'\]", content),
    }
    
    # Check for any hardcoded language values
    hardcoded = []
    hardcoded_patterns = [
        (r"'Spanish'|\"Spanish\"", "Spanish"),
        (r"'English'|\"English\"", "English"), 
        (r"'Malay'|\"Malay\"", "Malay"),
        (r"'en'|\"en\"", "en"),
        (r"'ms'|\"ms\"", "ms"),
        (r"'es'|\"es\"", "es"),
    ]
    
    for pattern, name in hardcoded_patterns:
        matches = re.findall(pattern, content)
        if matches:
            # Filter out comments and language_config.py references
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.search(pattern, line) and not line.strip().startswith('#') and 'LANGUAGE_CONFIG' not in line:
                    hardcoded.append(f"{name} on line {i+1}: {line.strip()}")
    
    return {
        'filename': filename,
        'global_refs': {k: len(v) for k, v in global_refs.items() if v},
        'hardcoded': hardcoded,
        'has_import': 'from language_config import' in content
    }

def main():
    lambda_dir = '/Users/syuen/language-learning-app/infrastructure/lambda'
    
    print("🔍 FINAL LANGUAGE CONSISTENCY VERIFICATION")
    print("=" * 60)
    
    all_functions = []
    issues_found = False
    
    for filename in sorted(os.listdir(lambda_dir)):
        if filename.endswith('.py') and filename != 'language_config.py':
            filepath = os.path.join(lambda_dir, filename)
            analysis = extract_language_values(filepath)
            all_functions.append(analysis)
            
            print(f"\n📁 {analysis['filename']}")
            
            if not analysis['has_import']:
                print(f"   ❌ Missing language_config import")
                issues_found = True
            else:
                print(f"   ✅ Has language_config import")
            
            if analysis['global_refs']:
                print(f"   📊 Global refs: {analysis['global_refs']}")
            
            if analysis['hardcoded']:
                print(f"   ❌ Hardcoded values found:")
                for hardcoded in analysis['hardcoded']:
                    print(f"      • {hardcoded}")
                issues_found = True
            else:
                print(f"   ✅ No hardcoded values")
    
    print("\n" + "=" * 60)
    
    if not issues_found:
        print("✅ ALL LAMBDA FUNCTIONS ARE PERFECTLY CONSISTENT!")
        print("🎯 All functions use LANGUAGE_CONFIG global constants")
        print("🎯 No hardcoded language values found")
        print("🎯 All functions import language_config properly")
        
        # Show what each function uses
        print("\n📊 GLOBAL CONFIG USAGE SUMMARY:")
        for func in all_functions:
            if func['global_refs']:
                print(f"   {func['filename']}: {func['global_refs']}")
        
        return True
    else:
        print("❌ INCONSISTENCIES STILL FOUND!")
        print("🔧 Fix the issues above to achieve perfect consistency")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
