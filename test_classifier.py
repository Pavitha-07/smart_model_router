# test_classifier.py
from app.router.classifier import PromptClassifier

classifier = PromptClassifier()

test_prompts = [
    "What is the capital of France?",
    "Write a complete REST API with authentication",
    "Summarize this in 3 sentences",
    "Explain quantum computing vs classical computing",
]

for prompt in test_prompts:
    result = classifier.classify(prompt)
    print(f"\nPrompt: {prompt}")
    print(f"→ Difficulty: {result.difficulty}")
    print(f"→ Confidence: {result.confidence:.2f}")
    print(f"→ Reasoning: {result.reasoning}")