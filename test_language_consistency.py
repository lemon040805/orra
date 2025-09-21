#!/usr/bin/env python3
"""
Test script to verify all Lambda functions use consistent language configuration
"""

import os
import re
import sys

def check_file_for_hardcoded_languages(filepath):
    """Check a file for hardcoded language references"""
    issues = []
    
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Patterns to look for
    hardcoded_patterns = [
        (r"'Spanish'", "Hardcoded 'Spanish' found"),
        (r'"Spanish"', 'Hardcoded "Spanish" found'),
        (r"'English'", "Hardcoded 'English' found (should use GLOBAL_NATIVE_LANGUAGE_NAME)"),
        (r'"English"', 'Hardcoded "English" found (should use GLOBAL_NATIVE_LANGUAGE_NAME)'),
        (r"'Malay'", "Hardcoded 'Malay' found (should use GLOBAL_TARGET_LANGUAGE_NAME)"),
        (r'"Malay"', 'Hardcoded "Malay" found (should use GLOBAL_TARGET_LANGUAGE_NAME)'),
        (r"'es'", "Hardcoded language code 'es' found"),
        (r'"es"', 'Hardcoded language code "es" found'),
        (r"'en'", "Hardcoded language code 'en' found (should use GLOBAL_NATIVE_LANGUAGE)"),
        (r'"en"', 'Hardcoded language code "en" found (should use GLOBAL_NATIVE_LANGUAGE)'),
    ]
    
    # Check if file imports language_config
    has_language_config_import = 'from language_config import' in content or 'import language_config' in content
    
    if not has_language_config_import and filepath.endswith('.py'):
        issues.append("Missing language_config import")
    
    # Check for hardcoded patterns
    for line_num, line in enumerate(lines, 1):
        for pattern, message in hardcoded_patterns:
            if re.search(pattern, line):
                # Skip comments and certain contexts
                if not line.strip().startswith('#') and 'language_names' not in line.lower():
                    issues.append(f"Line {line_num}: {message} - '{line.strip()}'")
    
    return issues

def main():
    """Main test function"""
    lambda_dir = '/Users/syuen/language-learning-app/infrastructure/lambda'
    
    if not os.path.exists(lambda_dir):
        print(f"❌ Lambda directory not found: {lambda_dir}")
        return False
    
    print("🔍 Testing Lambda functions for language consistency...")
    print("=" * 60)
    
    all_good = True
    
    # Test each Python file in lambda directory
    for filename in os.listdir(lambda_dir):
        if filename.endswith('.py') and filename != 'language_config.py':
            filepath = os.path.join(lambda_dir, filename)
            print(f"\n📁 Checking {filename}...")
            
            issues = check_file_for_hardcoded_languages(filepath)
            
            if issues:
                all_good = False
                print(f"❌ Issues found in {filename}:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print(f"✅ {filename} - No issues found")
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("✅ ALL LAMBDA FUNCTIONS USE CONSISTENT LANGUAGE CONFIGURATION!")
        print("🎯 Global native language: English (en)")
        print("🎯 Global target language: Malay (ms)")
        print("🎯 All functions properly import and use language_config")
        return True
    else:
        print("❌ ISSUES FOUND - Some Lambda functions have inconsistent language usage")
        print("🔧 Fix required: Update functions to use language_config imports")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
