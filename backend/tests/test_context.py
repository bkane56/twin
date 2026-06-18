"""Tests for context.py - Prompt generation."""
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest


def test_prompt_contains_name():
    """Test that prompt includes the person's name."""
    with patch('context.facts', {"full_name": "Brian Kane", "name": "Brian"}):
        with patch('context.linkedin', "LinkedIn profile"):
            with patch('context.summary', "Summary"):
                with patch('context.style', "Style guide"):
                    with patch('context.resume', "Resume"):
                        with patch('context.fun_facts', ["Fact 1"]):
                            from context import prompt
                            p = prompt()
                            assert "Brian Kane" in p
                            assert "Brian" in p


def test_prompt_contains_context_sections():
    """Test that prompt includes all context sections."""
    with patch('context.facts', {"full_name": "Brian Kane", "name": "Brian"}):
        with patch('context.linkedin', "LinkedIn data"):
            with patch('context.summary', "Summary data"):
                with patch('context.style', "Style data"):
                    with patch('context.resume', "Resume data"):
                        with patch('context.fun_facts', ["Fact 1", "Fact 2"]):
                            from context import prompt
                            p = prompt()
                            assert "LinkedIn" in p or "linkedin" in p
                            assert "resume" in p.lower()
                            assert "Your Role" in p


def test_prompt_contains_timestamp():
    """Test that prompt includes current timestamp."""
    with patch('context.facts', {"full_name": "Test", "name": "Test"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Should contain year, month, day format
                            assert datetime.now().strftime("%Y") in p


def test_prompt_contains_instructions():
    """Test that prompt contains key instructions."""
    with patch('context.facts', {"full_name": "Brian", "name": "Brian"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Check for critical rules
                            assert "hallucinate" in p.lower() or "invent" in p.lower()
                            assert "professional" in p.lower()


def test_prompt_contains_critical_rules():
    """Test that prompt includes all 4 critical rules."""
    with patch('context.facts', {"full_name": "Brian", "name": "Brian"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Should mention rules for safety
                            assert "rule" in p.lower() or "must" in p.lower()


def test_prompt_tone():
    """Test that prompt sets professional but engaging tone."""
    with patch('context.facts', {"full_name": "Brian", "name": "Brian"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Should emphasize professionalism
                            assert "professional" in p.lower()


def test_prompt_no_emojis_required():
    """Test that prompt disallows emojis."""
    with patch('context.facts', {"full_name": "Brian", "name": "Brian"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Should mention no emojis
                            assert "emoji" in p.lower()


def test_prompt_conversation_direction():
    """Test that prompt directs conversation toward professional topics."""
    with patch('context.facts', {"full_name": "Brian", "name": "Brian"}):
        with patch('context.linkedin', ""):
            with patch('context.summary', ""):
                with patch('context.style', ""):
                    with patch('context.resume', ""):
                        with patch('context.fun_facts', []):
                            from context import prompt
                            p = prompt()
                            # Should mention career or professional focus
                            assert any(word in p.lower() for word in ["career", "professional", "skill", "experience"])

