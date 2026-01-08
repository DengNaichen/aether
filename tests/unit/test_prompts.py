"""
Tests for prompt completeness and template formatting.

This module tests:
1. Prompt Completeness: All required prompts exist and are non-empty
2. Template Formatting: Prompts with placeholders can be correctly formatted
"""

import json

import pytest

from app.core import prompts


class TestPromptCompleteness:
    """Test that all required prompts exist and are properly structured."""

    def test_graph_generation_prompts_exist(self):
        """Test that all graph generation prompts are defined and non-empty."""
        assert hasattr(prompts, "GRAPH_GEN_SYSTEM_PROMPT")
        assert hasattr(prompts, "GRAPH_GEN_FEW_SHOT_EXAMPLES")
        assert hasattr(prompts, "GRAPH_FIX_SYSTEM_PROMPT")
        assert hasattr(prompts, "GRAPH_FIX_USER_TEMPLATE")

        assert isinstance(prompts.GRAPH_GEN_SYSTEM_PROMPT, str)
        assert isinstance(prompts.GRAPH_GEN_FEW_SHOT_EXAMPLES, str)
        assert isinstance(prompts.GRAPH_FIX_SYSTEM_PROMPT, str)
        assert isinstance(prompts.GRAPH_FIX_USER_TEMPLATE, str)

        assert len(prompts.GRAPH_GEN_SYSTEM_PROMPT) > 0
        assert len(prompts.GRAPH_GEN_FEW_SHOT_EXAMPLES) > 0
        assert len(prompts.GRAPH_FIX_SYSTEM_PROMPT) > 0
        assert len(prompts.GRAPH_FIX_USER_TEMPLATE) > 0

    def test_pdf_extraction_prompts_exist(self):
        """Test that all PDF extraction prompts are defined and non-empty."""
        assert hasattr(prompts, "PDF_ACADEMIC_OCR_PROMPT")
        assert hasattr(prompts, "PDF_HANDWRITING_PROMPT")

        assert isinstance(prompts.PDF_ACADEMIC_OCR_PROMPT, str)
        assert isinstance(prompts.PDF_HANDWRITING_PROMPT, str)

        assert len(prompts.PDF_ACADEMIC_OCR_PROMPT) > 0
        assert len(prompts.PDF_HANDWRITING_PROMPT) > 0

    def test_question_generation_prompts_exist(self):
        """Test that all question generation prompts are defined and non-empty."""
        assert hasattr(prompts, "QUESTION_GEN_SYSTEM_PROMPT")
        assert hasattr(prompts, "QUESTION_GEN_FEW_SHOT_EXAMPLES")

        assert isinstance(prompts.QUESTION_GEN_SYSTEM_PROMPT, str)
        assert isinstance(prompts.QUESTION_GEN_FEW_SHOT_EXAMPLES, list)

        assert len(prompts.QUESTION_GEN_SYSTEM_PROMPT) > 0
        assert len(prompts.QUESTION_GEN_FEW_SHOT_EXAMPLES) > 0

    def test_question_gen_few_shot_structure(self):
        """Test that QUESTION_GEN_FEW_SHOT_EXAMPLES has the correct structure."""
        examples = prompts.QUESTION_GEN_FEW_SHOT_EXAMPLES

        # Should be a list of tuples
        assert isinstance(examples, list)
        assert len(examples) > 0

        # Each example should be a tuple of (role, content)
        for example in examples:
            assert isinstance(example, tuple)
            assert len(example) == 2
            role, content = example
            assert role in ["human", "ai"]
            assert isinstance(content, str)
            assert len(content) > 0

        # Should have alternating human/ai messages
        for i, (role, _) in enumerate(examples):
            if i % 2 == 0:
                assert role == "human", f"Expected 'human' at index {i}, got '{role}'"
            else:
                assert role == "ai", f"Expected 'ai' at index {i}, got '{role}'"


class TestTemplateFormatting:
    """Test that prompts with placeholders can be correctly formatted."""

    def test_graph_gen_system_prompt_formatting(self):
        """Test GRAPH_GEN_SYSTEM_PROMPT can be formatted with user_guidance."""
        user_guidance = "Focus on mathematical concepts only."

        formatted = prompts.GRAPH_GEN_SYSTEM_PROMPT.format(user_guidance=user_guidance)

        # Should not contain the placeholder anymore
        assert "{user_guidance}" not in formatted
        # Should contain the actual guidance
        assert user_guidance in formatted
        # Should still contain the core instructions
        assert "KnowledgeNode" in formatted
        assert "Do NOT include relationships" in formatted

    def test_graph_gen_system_prompt_empty_guidance(self):
        """Test GRAPH_GEN_SYSTEM_PROMPT works with empty user_guidance."""
        formatted = prompts.GRAPH_GEN_SYSTEM_PROMPT.format(user_guidance="")

        # Should not contain the placeholder
        assert "{user_guidance}" not in formatted
        # Should still be a valid prompt
        assert len(formatted) > 0
        assert "KnowledgeNode" in formatted

    def test_graph_fix_user_template_formatting(self):
        """Test GRAPH_FIX_USER_TEMPLATE can be formatted with violations."""
        violations = """
        Violation 1: Node A depends on Parent Topic B
        - Parent Topic B has children: B1, B2, B3
        """

        formatted = prompts.GRAPH_FIX_USER_TEMPLATE.format(violations=violations)

        # Should not contain the placeholder
        assert "{violations}" not in formatted
        # Should contain the violations
        assert "Violation 1" in formatted
        assert "Node A" in formatted

    def test_question_gen_system_prompt_formatting(self):
        """Test QUESTION_GEN_SYSTEM_PROMPT can be formatted with user_guidance."""
        user_guidance = "Generate questions suitable for high school students."

        formatted = prompts.QUESTION_GEN_SYSTEM_PROMPT.format(
            user_guidance=user_guidance
        )

        # Should not contain the placeholder
        assert "{user_guidance}" not in formatted
        # Should contain the guidance
        assert user_guidance in formatted
        # Should contain core instructions
        assert "multiple_choice" in formatted
        assert "fill_blank" in formatted
        assert "short_answer" in formatted

    def test_no_unformatted_placeholders_in_static_prompts(self):
        """Test that prompts without placeholders don't have leftover braces."""
        # These prompts should not have any template variables
        static_prompts = [
            prompts.GRAPH_GEN_FEW_SHOT_EXAMPLES,
            prompts.GRAPH_FIX_SYSTEM_PROMPT,
            prompts.PDF_ACADEMIC_OCR_PROMPT,
            prompts.PDF_HANDWRITING_PROMPT,
        ]

        for prompt in static_prompts:
            # Should not have unmatched curly braces (except in JSON examples and LaTeX)
            # We'll check that there are no {variable_name} patterns
            import re

            # Find all {word} patterns, but exclude those inside LaTeX formulas ($...$)
            # First, remove LaTeX formulas to avoid false positives
            prompt_without_latex = re.sub(r"\$[^$]+\$", "", prompt)

            # Find all {word} patterns
            placeholders = re.findall(r"\{(\w+)\}", prompt_without_latex)

            # Filter out JSON-like patterns (single letters or numbers)
            # Valid placeholders are multi-character words
            suspicious_placeholders = [
                p for p in placeholders if len(p) > 1 and p.isalpha()
            ]

            assert (
                len(suspicious_placeholders) == 0
            ), f"Found unformatted placeholders: {suspicious_placeholders}"


class TestPromptContentQuality:
    """Test that prompts contain expected key instructions and examples."""

    def test_graph_gen_prompt_contains_granularity_rules(self):
        """Test that GRAPH_GEN_SYSTEM_PROMPT contains granularity guidelines."""
        prompt = prompts.GRAPH_GEN_SYSTEM_PROMPT

        # Should contain DO and DO NOT sections
        assert "DO extract as nodes:" in prompt
        assert "DO NOT extract as separate nodes:" in prompt

        # Should contain quality check guidance
        assert "Quality Check:" in prompt or "quiz question" in prompt

    def test_graph_gen_few_shot_examples_are_valid_json(self):
        """Test that few-shot examples contain valid JSON structures."""
        examples_text = prompts.GRAPH_GEN_FEW_SHOT_EXAMPLES

        # Extract JSON blocks from the examples
        import re

        # The examples use {{ and }} for escaping in format strings
        # Replace them with single braces for JSON parsing
        examples_text_unescaped = examples_text.replace("{{", "{").replace("}}", "}")

        json_blocks = re.findall(r"\{[\s\S]*?\n\}", examples_text_unescaped)

        assert len(json_blocks) > 0, "No JSON examples found in few-shot examples"

        for json_block in json_blocks:
            try:
                parsed = json.loads(json_block)
                # Should have 'nodes' key only
                assert "nodes" in parsed
                assert isinstance(parsed["nodes"], list)
                assert "relationships" not in parsed
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in few-shot example: {e}\n{json_block}")

    def test_question_gen_few_shot_examples_contain_all_types(self):
        """Test that question generation examples cover different question types."""
        examples = prompts.QUESTION_GEN_FEW_SHOT_EXAMPLES

        # Combine all AI responses
        ai_responses = [content for role, content in examples if role == "ai"]
        all_ai_text = "\n".join(ai_responses)

        # Should contain examples of different question types
        assert "multiple_choice" in all_ai_text
        assert "fill_blank" in all_ai_text
        assert "short_answer" in all_ai_text

        # Should contain examples of different difficulties
        assert "easy" in all_ai_text
        assert "medium" in all_ai_text
        assert "hard" in all_ai_text

    def test_pdf_prompts_contain_key_instructions(self):
        """Test that PDF extraction prompts contain critical instructions."""
        academic_prompt = prompts.PDF_ACADEMIC_OCR_PROMPT
        handwriting_prompt = prompts.PDF_HANDWRITING_PROMPT

        # Academic OCR should mention LaTeX and References exclusion
        assert "LaTeX" in academic_prompt or "latex" in academic_prompt.lower()
        assert (
            "References" in academic_prompt or "Bibliography" in academic_prompt
        ), "Should instruct to exclude references"

        # Handwriting prompt should mention illegible text handling
        assert "[illegible]" in handwriting_prompt or "illegible" in handwriting_prompt

    def test_graph_gen_examples_match_schema_structure(self):
        """Test that graph generation examples match expected schema structure."""
        examples_text = prompts.GRAPH_GEN_FEW_SHOT_EXAMPLES

        # Extract JSON blocks
        import re

        # Handle escaped braces in format strings
        examples_text_unescaped = examples_text.replace("{{", "{").replace("}}", "}")

        json_blocks = re.findall(r"\{[\s\S]*?\n\}", examples_text_unescaped)

        for json_block in json_blocks:
            parsed = json.loads(json_block)

            # Check nodes structure
            for node in parsed["nodes"]:
                assert "name" in node, "Node should have 'name' field"
                assert "description" in node, "Node should have 'description' field"
            assert "relationships" not in parsed
