#!/usr/bin/env python3
"""
Text Cleaner Utility
Cleans and merges transcription text, removing repetition and fixing common errors.
"""

import re
from typing import List, Tuple


def clean_text(text: str) -> str:
    """
    Clean transcription text by:
    - Removing excessive repetition
    - Fixing common grammar errors
    - Improving sentence flow
    - Fixing punctuation
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common errors
    text = re.sub(r'\bMore more\b', 'more', text, flags=re.IGNORECASE)
    text = re.sub(r'\bJesus\b', 'Jesus', text)  # Standardize name
    
    # Fix sentence breaks
    text = re.sub(r'\.\s+([A-Z])', r'. \1', text)
    
    # Fix incomplete sentences (trailing "to" or "and")
    text = re.sub(r'\s+(to|and)\s*$', '', text, flags=re.IGNORECASE)
    
    # Remove duplicate phrases (simple approach)
    sentences = text.split('.')
    seen = set()
    cleaned_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Create a key for comparison (lowercase, no punctuation)
        key = re.sub(r'[^\w\s]', '', sentence.lower()).strip()
        
        # Skip if very similar to something we've seen
        if key and key not in seen:
            seen.add(key)
            cleaned_sentences.append(sentence)
    
    # Join sentences back
    result = '. '.join(cleaned_sentences)
    
    # Ensure proper sentence endings
    if result and not result.endswith(('.', '!', '?')):
        result += '.'
    
    return result


def merge_texts(version1: str, version2: str) -> str:
    """
    Merge two versions of text, taking the best parts from each.
    """
    # Clean both versions
    cleaned1 = clean_text(version1)
    cleaned2 = clean_text(version2)
    
    # Split into sentences
    sentences1 = [s.strip() for s in cleaned1.split('.') if s.strip()]
    sentences2 = [s.strip() for s in cleaned2.split('.') if s.strip()]
    
    # Combine unique sentences
    all_sentences = sentences1 + sentences2
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sentences = []
    for sentence in all_sentences:
        key = re.sub(r'[^\w\s]', '', sentence.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique_sentences.append(sentence)
    
    # Join with proper formatting
    result = '. '.join(unique_sentences)
    if result and not result.endswith(('.', '!', '?')):
        result += '.'
    
    return result


def compare_versions(text1: str, text2: str) -> dict:
    """
    Compare two text versions and return differences.
    """
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    only_in_1 = words1 - words2
    only_in_2 = words2 - words1
    common = words1 & words2
    
    return {
        'only_in_version1': sorted(only_in_1),
        'only_in_version2': sorted(only_in_2),
        'common_words': len(common),
        'unique_to_v1': len(only_in_1),
        'unique_to_v2': len(only_in_2)
    }


if __name__ == '__main__':
    # Example usage
    version1 = """He'd done a lot. For the Kingdom of God, yet still in his heart. I want to press on. I want to keep going. I want to still be used. Not finished yet? You know, I don't think if the apostle Paul was here, he'd encourage us to do the same. No matter how long you've been walking with God, no matter what you've seen God do through your life, he'd say, come on. Don't stop. Keep making this available, keep being open, because there's still more. But notice specifically what the apostle Paul says in this verse. He says. I press on to take hold of that. Jesus took hold of me. The question is, what is that?"""
    
    version2 = """He'd done a lot. For the Kingdom of God, yet still in his heart. I want to press on. I want to keep going. I want to still be used. Not finished yet? You know, I don't think if the apostle Paul was here, he'd encourage us to do the same. No matter how long you've been walking with God, no matter what you've seen God do through your life, he'd say, come on. Don't stop. Keep making this available, keep being open, because there's still more. But notice specifically what the apostle Paul says in this verse. He says. I press on to take hold of that. Jesus took hold of me. The question is, what is that? I press on to take hold of that. For which Christ Jesus took hold of me? What is that that Christ Jesus took hold of him for? And what is that that he takes hold of us for? More more like Jesus and outwork his mission in the earth. I press on to"""
    
    print("=== TEXT COMPARISON TOOL ===\n")
    
    # Compare
    diff = compare_versions(version1, version2)
    print(f"Words only in Version 1: {diff['unique_to_v1']}")
    print(f"Words only in Version 2: {diff['unique_to_v2']}")
    print(f"Common words: {diff['common_words']}\n")
    
    # Merge
    print("=== MERGED & CLEANED VERSION ===\n")
    merged = merge_texts(version1, version2)
    print(merged)







