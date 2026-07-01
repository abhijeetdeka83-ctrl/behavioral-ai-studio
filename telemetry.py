# telemetry.py
import re
import math

def calculate_prose_telemetry(draft_text, final_text, initial_violations, checking_function):
    """
    Parses draft and finalized manuscript text states to calculate 
    real-time algorithmic telemetry for dashboard visualization.
    """
    # 1. Calculate Forbidden Phrase Suppression Efficiency
    initial_count = len(initial_violations)
    final_violations = checking_function(final_text)
    final_count = len(final_violations)
    
    if initial_count == 0:
        suppression_efficiency = 100.0  # Perfect score if no rules were broken initially
    else:
        # Percentage of caught errors successfully cleaned up by the loop
        suppression_efficiency = max(0.0, min(100.0, ((initial_count - final_count) / initial_count) * 100.0))

    # 2. Calculate Dialogue Diversity Score (Type-Token Ratio inside quotes)
    dialogue_blocks = re.findall(r'"([^"]*)"', final_text)
    if not dialogue_blocks:
        # Fallback to general prose analysis if the scene has zero spoken lines
        dialogue_blocks = [final_text]
        
    dialogue_words = []
    for block in dialogue_blocks:
        words = re.findall(r'\b\w+\b', block.lower())
        dialogue_words.extend(words)
        
    if not dialogue_words:
        dialogue_diversity = 0.0
    else:
        unique_words = set(dialogue_words)
        # Classic TTR metric scaled up to a baseline target percentage
        raw_ttr = len(unique_words) / len(dialogue_words)
        dialogue_diversity = max(0.0, min(100.0, raw_ttr * 130.0)) # Scaled for natural language margins

    # 3. Catch Lexical Echo Phrases (Repetitive word pairs or close loops)
    # This flags when a writer uses the same word within a 3-word proximity window
    all_words = re.findall(r'\b\w{4,}\b', final_text.lower()) # Only check words 4+ letters long
    echo_count = 0
    for i in range(len(all_words) - 3):
        window = all_words[i+1 : i+4]
        if all_words[i] in window:
            echo_count += 1

    # 4. Calculate Pacing Dynamic Range (Standard Deviation of Sentence Word Lengths)
    # Great prose varies sentence lengths dramatically. Monotonous prose keeps them identical.
    sentences = re.split(r'[.!?]+', final_text)
    sentence_lengths = []
    
    for sentence in sentences:
        words = re.findall(r'\b\w+\b', sentence)
        if len(words) > 1: # Ignore empty fragments or stray punctuation artifacts
            sentence_lengths.append(len(words))
            
    if len(sentence_lengths) < 2:
        pacing_range = 0.0
    else:
        # Calculate standard deviation manually to prevent needing hefty numpy dependencies in the container
        mean_length = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        pacing_range = round(math.sqrt(variance), 2)

    return {
        "suppression_efficiency_pct": round(suppression_efficiency, 1),
        "dialogue_diversity_pct": round(dialogue_diversity, 1),
        "lexical_echo_phrases": echo_count,
        "pacing_dynamic_range": pacing_range
    }
    
