# app/router/classifier.py
import re
from app.models import ClassificationResult

class PromptClassifier:
    """
    Classifies prompts into difficulty levels: simple, medium, complex
    Uses rule-based classification (fast, no API calls needed)
    """
    
    def __init__(self):
        # Keywords indicating complexity
        self.complex_keywords = [
            "write a", "create a", "build a", "develop",
            "analyze", "compare", "explain why", "reason",
            "architecture", "system design", "algorithm",
            "debug", "refactor", "optimize",
            "multi-step", "chain of thought", "reasoning",
            "creative writing", "story", "essay", "article"
        ]
        
        self.simple_keywords = [
            "summarize", "what is", "define", "list",
            "translate", "convert", "format",
            "yes or no", "true or false",
            "capital of", "when was", "who is"
        ]
    
    def classify(self, prompt: str) -> ClassificationResult:
        """Main classification method"""
        return self._classify_rule_based(prompt)
    
    def _classify_rule_based(self, prompt: str) -> ClassificationResult:
        """Fast rule-based classification"""
        prompt_lower = prompt.lower()
        
        # Calculate scores
        complexity_score = 0.0
        reasoning = []
        
        # 1. Length check
        word_count = len(prompt.split())
        if word_count < 10:
            complexity_score -= 0.3
            reasoning.append(f"short prompt ({word_count} words)")
        elif word_count > 50:
            complexity_score += 0.2
            reasoning.append(f"long prompt ({word_count} words)")
        
        # 2. Keyword matching
        complex_matches = sum(1 for kw in self.complex_keywords if kw in prompt_lower)
        simple_matches = sum(1 for kw in self.simple_keywords if kw in prompt_lower)
        
        if complex_matches > simple_matches:
            complexity_score += 0.4 * complex_matches
            reasoning.append(f"complex keywords: {complex_matches}")
        elif simple_matches > 0:
            complexity_score -= 0.3 * simple_matches
            reasoning.append(f"simple keywords: {simple_matches}")
        
        # 3. Code detection
        if self._contains_code(prompt):
            complexity_score += 0.3
            reasoning.append("contains code")
        
        # 4. Question complexity
        question_marks = prompt.count("?")
        if question_marks == 1 and word_count < 15:
            complexity_score -= 0.2
            reasoning.append("single simple question")
        elif question_marks > 2:
            complexity_score += 0.2
            reasoning.append("multiple questions")
        
        # 5. Request for reasoning/explanation
        reasoning_patterns = ["explain", "why", "how does", "reasoning", "analyze"]
        if any(pattern in prompt_lower for pattern in reasoning_patterns):
            complexity_score += 0.3
            reasoning.append("requires reasoning")
        
        # Determine final difficulty
        if complexity_score < -0.3:
            difficulty = "simple"
            confidence = min(0.9, 0.7 + abs(complexity_score))
        elif complexity_score > 0.5:
            difficulty = "complex"
            confidence = min(0.9, 0.65 + complexity_score * 0.3)
        else:
            difficulty = "medium"
            confidence = 0.6
        
        return ClassificationResult(
            difficulty=difficulty,
            confidence=confidence,
            reasoning=" | ".join(reasoning)
        )
    
    def _contains_code(self, text: str) -> bool:
        """Detect if prompt contains code"""
        code_indicators = [
            r'```',  # Code blocks
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+',  # Class definitions
            r'\bimport\s+\w+',  # Import statements
            r'<\w+>.*</\w+>',  # HTML tags
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, text):
                return True
        return False