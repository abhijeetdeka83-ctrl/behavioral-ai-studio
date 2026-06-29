# telemetry.py
# Layer 4 Narrative Telemetry Engine for Stratagem Workspace
import re
import math
import collections

def calculate_prose_telemetry(draft_text: str, final_text: str, initial_violations: list, checking_function) -> dict:
    """
    LAYER 4: TELEMETRY COMPILER
    Compares the raw AI draft against the audited manuscript to generate hard quality metrics.
    """
    def get_words(text):
        return re.findall(r'\b\w+\b', text.lower())

    def get_sentences(text):
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    draft_words = get_words(draft_text)
    final_words = get_words(final_text)
    final_sentences = get_sentences(final_text)

    # 1. Anti-Pattern Suppression Efficiency Rate
    # Calls your engine's existing violation check function dynamically
    final_violations = checking_function(final_text)
    violations_removed = len(initial_violations) - len(final_violations)
    suppression_rate = (violations_removed / len(initial_violations) * 100) if initial_violations else 100.0

    # 2. Dialogue Diversity Score (Type-Token Ratio for Spoken Lines)
    dialogue_lines = re.findall(r'"([^"]*)"', final_text)
    dialogue_words = get_words(" ".join(dialogue_lines))
    if dialogue_words:
        dialogue_diversity = (len(set(dialogue_words)) / len(dialogue_words)) * 100
    else:
        dialogue_diversity = 100.0

    # 3. Repeated Phrase Frequency (Lexical Echo Tracker)
    bigrams = [(final_words[i], final_words[i+1]) for i in range(len(final_words)-1)]
    bigram_counts = collections.Counter(bigrams)
    duplicate_echoes = sum(1 for count in bigram_counts.values() if count > 2)

    # 4. Pacing Dynamic Range (Sentence Length Standard Deviation)
    sentence_lengths = [len(get_words(s)) for s in final_sentences]
    if len(sentence_lengths) > 1:
        mean_length = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        pacing_standard_dev = math.sqrt(variance)
    else:
        pacing_standard_dev = 0.0

    return {
        "anti_patterns_removed": violations_removed,
        "suppression_efficiency_pct": round(suppression_rate, 1),
        "dialogue_diversity_pct": round(dialogue_diversity, 1),
        "lexical_echo_phrases": duplicate_echoes,
        "pacing_dynamic_range": round(pacing_standard_dev, 2),
        "word_count_delta": len(final_words) - len(draft_words)
    }
    
