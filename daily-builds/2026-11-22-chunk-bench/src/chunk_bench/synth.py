"""Synthesize evaluation questions from corpus."""

import random
import hashlib
from .models import Document, Question
from .tokenize import split_by_sentences


def generate_questions(
    documents: list[Document],
    n: int = 30,
    seed: int = 1
) -> list[Question]:
    """Generate synthetic questions from corpus."""
    rng = random.Random(seed)
    questions = []
    
    all_sentences = []
    for doc in documents:
        sentences = split_by_sentences(doc.text)
        for sentence in sentences:
            if len(sentence.split()) >= 5:
                all_sentences.append((doc.doc_id, sentence, doc.text))
    
    if not all_sentences:
        return questions
    
    sample_size = min(n, len(all_sentences))
    
    seed_bytes = str(seed).encode()
    for i, (doc_id, sentence, full_text) in enumerate(all_sentences):
        hash_input = seed_bytes + sentence.encode() + str(i).encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest(), 16)
        rng.seed(hash_val)
    
    rng.seed(seed)
    sampled = rng.sample(all_sentences, sample_size)
    
    for doc_id, sentence, full_text in sampled:
        question_text = generate_question_from_sentence(sentence, rng)
        
        gold_substring = sentence[:min(50, len(sentence))]
        
        questions.append(Question(
            question=question_text,
            gold_doc=doc_id,
            gold_substring=gold_substring,
        ))
    
    return questions


def generate_question_from_sentence(sentence: str, rng: random.Random) -> str:
    """Generate a question from a sentence."""
    words = sentence.split()
    
    if len(words) < 5:
        return f"What information is provided about {words[0]}?"
    
    templates = [
        f"What does the document say about {words[rng.randint(0, min(3, len(words)-1))]}?",
        f"Where can I find information about {words[rng.randint(0, min(3, len(words)-1))]}?",
        f"Tell me about {words[rng.randint(0, min(2, len(words)-1))]}",
        f"Explain {words[rng.randint(0, min(2, len(words)-1))]}",
    ]
    
    return rng.choice(templates)
