"""
RegEx Pattern Generator Module for the OARC package.

This module uses Ollama models to automatically analyze content examples
and generate appropriate regex patterns to extract similar content.

Author: OARC Contributors
Date: 4/11/2025
"""

import re
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

# Import regex pattern factory from main module
from regex_pattern_extractor import RegExPatternFactory

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaPatternGenerator:
    """
    Uses Ollama models to generate regex patterns from example content.
    Can analyze content examples and create patterns to add to the RegExPatternFactory.
    """
    
    def __init__(self, model_name="llama3", pattern_factory=None):
        """
        Initialize the pattern generator with specified model and pattern factory.
        
        Args:
            model_name: Name of the Ollama model to use
            pattern_factory: Optional RegExPatternFactory instance
        """
        self.model_name = model_name
        self.pattern_factory = pattern_factory or RegExPatternFactory()
        
        # Import ollama here to avoid dependency if not using this module
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            logger.error("Ollama package not installed. Please install with 'pip install ollama'")
            self.ollama = None
    
    def generate_pattern_from_examples(self, 
                                      examples: List[str], 
                                      pattern_id: str,
                                      name: str = None,
                                      description: str = None) -> Dict[str, Any]:
        """
        Generate a regex pattern from a list of content examples.
        
        Args:
            examples: List of example strings to generate a pattern for
            pattern_id: ID for the new pattern
            name: Optional name for the pattern
            description: Optional description for the pattern
            
        Returns:
            Dictionary with the generated pattern information
        """
        if not self.ollama:
            raise ImportError("Ollama package is required for pattern generation")
        
        # Set default name and description if not provided
        name = name or f"{pattern_id.capitalize()} Pattern"
        description = description or f"Extract {pattern_id} content from text"
        
        # Create a prompt for the pattern generation
        prompt = self._create_pattern_generation_prompt(examples, pattern_id)
        
        # Call the Ollama model
        response = self.ollama.generate(
            model=self.model_name,
            prompt=prompt
        )
        
        # Extract pattern information from response
        pattern_info = self._extract_pattern_info(response["response"])
        
        # Create the full pattern data
        pattern_data = {
            "pattern_id": pattern_id,
            "name": name,
            "description": description,
            "pattern": pattern_info.get("pattern", ""),
            "fallback_patterns": pattern_info.get("fallback_patterns", []),
            "parser": pattern_info.get("parser", "text")
        }
        
        return pattern_data
    
    def add_pattern_from_examples(self, 
                                 examples: List[str], 
                                 pattern_id: str,
                                 name: str = None,
                                 description: str = None,
                                 save_to_storage: bool = True) -> bool:
        """
        Generate a pattern from examples and add it to the pattern factory.
        
        Args:
            examples: List of example strings to generate a pattern for
            pattern_id: ID for the new pattern
            name: Optional name for the pattern
            description: Optional description for the pattern
            save_to_storage: Whether to save the pattern to storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate the pattern
            pattern_data = self.generate_pattern_from_examples(
                examples=examples,
                pattern_id=pattern_id,
                name=name,
                description=description
            )
            
            # Add to pattern factory
            success = self.pattern_factory.add_pattern(
                pattern_id=pattern_data["pattern_id"],
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern=pattern_data["pattern"],
                fallback_patterns=pattern_data["fallback_patterns"],
                parser=pattern_data["parser"]
            )
            
            if success:
                logger.info(f"Successfully added pattern '{pattern_id}' to factory")
            
            return success
        except Exception as e:
            logger.error(f"Error adding pattern from examples: {e}")
            return False
    
    def analyze_content_and_generate_pattern(self, 
                                           content: str,
                                           target_extract: str,
                                           pattern_id: str,
                                           name: str = None,
                                           description: str = None) -> Dict[str, Any]:
        """
        Analyze full content and a specific extraction target to generate a pattern.
        This is useful when you have a larger document and want to extract specific parts.
        
        Args:
            content: The full content to analyze
            target_extract: The specific part you want to extract
            pattern_id: ID for the new pattern
            name: Optional name for the pattern
            description: Optional description for the pattern
            
        Returns:
            Dictionary with the generated pattern information
        """
        if not self.ollama:
            raise ImportError("Ollama package is required for pattern generation")
        
        # Create a prompt for the pattern generation
        prompt = self._create_content_analysis_prompt(content, target_extract, pattern_id)
        
        # Call the Ollama model
        response = self.ollama.generate(
            model=self.model_name,
            prompt=prompt
        )
        
        # Extract pattern information from response
        pattern_info = self._extract_pattern_info(response["response"])
        
        # Set default name and description if not provided
        name = name or f"{pattern_id.capitalize()} Pattern"
        description = description or f"Extract {pattern_id} content from text"
        
        # Create the full pattern data
        pattern_data = {
            "pattern_id": pattern_id,
            "name": name,
            "description": description,
            "pattern": pattern_info.get("pattern", ""),
            "fallback_patterns": pattern_info.get("fallback_patterns", []),
            "parser": pattern_info.get("parser", "text")
        }
        
        return pattern_data
    
    def test_pattern_on_examples(self, pattern: str, examples: List[str], fallback_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Test a pattern on a list of examples to see how well it performs.
        
        Args:
            pattern: Regex pattern to test
            examples: List of example strings to test the pattern on
            fallback_patterns: Optional list of fallback patterns to test
            
        Returns:
            Dictionary with test results
        """
        results = {
            "matches": 0,
            "misses": 0,
            "match_percentage": 0,
            "matched_examples": [],
            "missed_examples": [],
            "fallback_matches": 0,
            "total_examples": len(examples)
        }
        
        # Test the main pattern
        for example in examples:
            try:
                matches = re.findall(pattern, example, re.DOTALL)
                if matches:
                    results["matches"] += 1
                    results["matched_examples"].append(example)
                else:
                    # Try fallback patterns if provided
                    fallback_matched = False
                    if fallback_patterns:
                        for fallback in fallback_patterns:
                            fallback_matches = re.findall(fallback, example, re.DOTALL)
                            if fallback_matches:
                                results["matches"] += 1
                                results["fallback_matches"] += 1
                                results["matched_examples"].append(example)
                                fallback_matched = True
                                break
                    
                    if not fallback_matched:
                        results["misses"] += 1
                        results["missed_examples"].append(example)
            except Exception as e:
                logger.error(f"Error testing pattern '{pattern}' on example: {e}")
                results["misses"] += 1
                results["missed_examples"].append(example)
        
        # Calculate match percentage
        if results["total_examples"] > 0:
            results["match_percentage"] = (results["matches"] / results["total_examples"]) * 100
        
        return results
    
    def optimize_pattern(self, initial_pattern: str, examples: List[str]) -> Dict[str, Any]:
        """
        Use Ollama to optimize an existing pattern for better performance.
        
        Args:
            initial_pattern: Initial regex pattern to optimize
            examples: List of example strings the pattern should match
            
        Returns:
            Dictionary with optimized pattern information
        """
        if not self.ollama:
            raise ImportError("Ollama package is required for pattern optimization")
        
        # Test the initial pattern
        test_results = self.test_pattern_on_examples(initial_pattern, examples)
        
        # If it's already perfect, return the original
        if test_results["match_percentage"] == 100:
            return {
                "pattern": initial_pattern,
                "fallback_patterns": [],
                "test_results": test_results,
                "optimized": False
            }
        
        # Create a prompt for optimization
        prompt = self._create_pattern_optimization_prompt(
            initial_pattern=initial_pattern,
            examples=examples,
            test_results=test_results
        )
        
        # Call the Ollama model
        response = self.ollama.generate(
            model=self.model_name,
            prompt=prompt
        )
        
        # Extract pattern information from response
        pattern_info = self._extract_pattern_info(response["response"])
        
        # Test the optimized pattern
        optimized_pattern = pattern_info.get("pattern", initial_pattern)
        fallback_patterns = pattern_info.get("fallback_patterns", [])
        
        optimized_results = self.test_pattern_on_examples(
            optimized_pattern, 
            examples,
            fallback_patterns
        )
        
        return {
            "pattern": optimized_pattern,
            "fallback_patterns": fallback_patterns,
            "test_results": optimized_results,
            "optimized": True,
            "improvement": optimized_results["match_percentage"] - test_results["match_percentage"]
        }
    
    def _create_pattern_generation_prompt(self, examples: List[str], pattern_id: str) -> str:
        """Create a prompt for pattern generation from examples"""
        formatted_examples = "\n\n".join([f"Example {i+1}:\n```\n{example}\n```" for i, example in enumerate(examples)])
        
        prompt = f"""
        # RegEx Pattern Generation Task
        
        I need you to create a robust regular expression pattern that can extract content similar to these examples. 
        The pattern will be used to identify and extract {pattern_id} content from text.
        
        ## Examples to Match
        
        {formatted_examples}
        
        ## Requirements
        
        1. Create a main regex pattern that will match all or most of these examples
        2. Provide 1-3 fallback patterns for cases where the main pattern might fail
        3. Recommend a parser type ("text" or "json")
        4. The patterns should work with Python's re.findall() with re.DOTALL flag
        5. Use capture groups to extract just the relevant content
        
        ## Output Format
        
        Provide your response ONLY in this JSON format:
        
        ```json
        {{
          "pattern": "your main regex pattern",
          "fallback_patterns": [
            "fallback pattern 1",
            "fallback pattern 2",
            "fallback pattern 3"
          ],
          "parser": "text",
          "explanation": "explanation of how the patterns work"
        }}
        ```
        
        Do not include any other text outside the JSON block.
        """
        
        return prompt
    
    def _create_content_analysis_prompt(self, content: str, target_extract: str, pattern_id: str) -> str:
        """Create a prompt for analyzing content and generating a pattern"""
        prompt = f"""
        # RegEx Pattern Generation from Content Analysis
        
        I need you to analyze a piece of content and create a robust regular expression pattern 
        that can extract similar content to the target extract provided.
        
        ## Full Content
        
        ```
        {content}
        ```
        
        ## Target to Extract
        
        ```
        {target_extract}
        ```
        
        ## Requirements
        
        1. Analyze how the target extract appears within the full content
        2. Create a main regex pattern that will extract similar content from text following this format
        3. Provide 1-3 fallback patterns for cases where the main pattern might fail
        4. Recommend a parser type ("text" or "json")
        5. The patterns should work with Python's re.findall() with re.DOTALL flag
        6. Use capture groups to extract just the relevant content
        
        ## Output Format
        
        Provide your response ONLY in this JSON format:
        
        ```json
        {{
          "pattern": "your main regex pattern",
          "fallback_patterns": [
            "fallback pattern 1",
            "fallback pattern 2"
          ],
          "parser": "text",
          "explanation": "explanation of how the patterns work and what they're designed to capture"
        }}
        ```
        
        Do not include any other text outside the JSON block.
        """
        
        return prompt
    
    def _create_pattern_optimization_prompt(self, initial_pattern: str, examples: List[str], test_results: Dict[str, Any]) -> str:
        """Create a prompt for optimizing an existing pattern"""
        formatted_examples = "\n\n".join([f"Example {i+1}:\n```\n{example}\n```" for i, example in enumerate(examples)])
        matched_examples = "\n\n".join([f"Matched {i+1}:\n```\n{example}\n```" for i, example in enumerate(test_results["matched_examples"])])
        missed_examples = "\n\n".join([f"Missed {i+1}:\n```\n{example}\n```" for i, example in enumerate(test_results["missed_examples"])])
        
        prompt = f"""
        # RegEx Pattern Optimization Task
        
        I need you to optimize an existing regular expression pattern that currently matches {test_results["match_percentage"]:.1f}% of examples.
        Your goal is to improve the pattern to match as many examples as possible.
        
        ## Current Pattern
        
        ```
        {initial_pattern}
        ```
        
        ## Examples That Should Match
        
        {formatted_examples}
        
        ## Current Results
        
        - Matches: {test_results["matches"]} out of {test_results["total_examples"]}
        - Match percentage: {test_results["match_percentage"]:.1f}%
        
        ### Currently Matched Examples
        
        {matched_examples if matched_examples else "None"}
        
        ### Currently Missed Examples
        
        {missed_examples if missed_examples else "None"}
        
        ## Requirements
        
        1. Analyze why the current pattern fails on some examples
        2. Create an improved main pattern that matches more examples
        3. Provide 1-3 fallback patterns for cases where the main pattern might fail
        4. The patterns should work with Python's re.findall() with re.DOTALL flag
        5. Use capture groups to extract just the relevant content
        
        ## Output Format
        
        Provide your response ONLY in this JSON format:
        
        ```json
        {{
          "pattern": "your optimized main regex pattern",
          "fallback_patterns": [
            "fallback pattern 1",
            "fallback pattern 2"
          ],
          "explanation": "explanation of the improvements made"
        }}
        ```
        
        Do not include any other text outside the JSON block.
        """
        
        return prompt
    
    def _extract_pattern_info(self, response: str) -> Dict[str, Any]:
        """Extract pattern information from the model's response"""
        try:
            # Try to find a JSON block in the response
            json_match = re.search(r'```(?:json)?\s*({\s*"pattern"[\s\S]*?})\s*```', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Fallback: Try to parse the entire response as JSON
            try:
                return json.loads(response.strip())
            except:
                pass
            
            # Extreme fallback: Try to extract pattern directly
            pattern_match = re.search(r'"pattern"\s*:\s*"([^"]+)"', response)
            fallback_matches = re.findall(r'"fallback_patterns"\s*:\s*\[\s*"([^"]+)"', response)
            
            if pattern_match:
                return {
                    "pattern": pattern_match.group(1),
                    "fallback_patterns": fallback_matches,
                    "parser": "text"
                }
            
            logger.warning("Could not parse pattern information from response")
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting pattern info: {e}")
            return {}


class PatternDiscovery:
    """
    Analyze content to discover and suggest pattern types that could be extracted.
    This helps identify what kinds of pattern extractors would be valuable to add.
    """
    
    def __init__(self, model_name="llama3"):
        """Initialize the pattern discovery with specified model"""
        self.model_name = model_name
        
        # Import ollama here to avoid dependency if not using this module
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            logger.error("Ollama package not installed. Please install with 'pip install ollama'")
            self.ollama = None
    
    def discover_patterns(self, content: str) -> List[Dict[str, Any]]:
        """
        Analyze content to discover potential pattern types that could be extracted.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of dictionaries with pattern suggestions
        """
        if not self.ollama:
            raise ImportError("Ollama package is required for pattern discovery")
        
        # Create a prompt for pattern discovery
        prompt = self._create_pattern_discovery_prompt(content)
        
        # Call the Ollama model
        response = self.ollama.generate(
            model=self.model_name,
            prompt=prompt
        )
        
        # Extract pattern suggestions from response
        return self._extract_pattern_suggestions(response["response"])
    
    def _create_pattern_discovery_prompt(self, content: str) -> str:
        """Create a prompt for pattern discovery"""
        # Limit content length to avoid token limits
        if len(content) > 8000:
            content_sample = content[:8000] + "\n...[content truncated]..."
        else:
            content_sample = content
            
        prompt = f"""
        # Pattern Discovery Analysis
        
        Analyze the following content and identify potential pattern types that could be extracted with regular expressions.
        Look for structured data, code blocks, formatting patterns, or any other consistent structures.
        
        ## Content to Analyze
        
        ```
        {content_sample}
        ```
        
        ## Task
        
        1. Identify different types of content that follow consistent patterns
        2. For each pattern type, provide a suggested pattern ID, name, and example of what would be extracted
        3. Provide a brief justification for why this pattern would be useful
        
        ## Output Format
        
        Provide your response ONLY in this JSON format:
        
        ```json
        [
          {{
            "pattern_id": "suggested_pattern_id",
            "name": "Human-readable pattern name",
            "description": "Brief description of what this pattern extracts",
            "example": "Example of content that would be extracted",
            "justification": "Why this pattern would be useful"
          }},
          {{
            "pattern_id": "another_pattern",
            "name": "Another Pattern Type",
            "description": "Description of what this pattern extracts",
            "example": "Example content",
            "justification": "Usefulness explanation"
          }}
        ]
        ```
        
        Provide at least 2 and at most 5 pattern suggestions. Do not include any other text outside the JSON block.
        """
        
        return prompt
    
    def _extract_pattern_suggestions(self, response: str) -> List[Dict[str, Any]]:
        """Extract pattern suggestions from the model's response"""
        try:
            # Try to find a JSON block in the response
            json_match = re.search(r'```(?:json)?\s*(\[\s*{\s*"pattern_id"[\s\S]*?}\s*\])\s*```', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Fallback: Try to parse the entire response as JSON
            try:
                return json.loads(response.strip())
            except:
                pass
            
            logger.warning("Could not parse pattern suggestions from response")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting pattern suggestions: {e}")
            return []


class ContentAnalysisUtils:
    """
    Utility functions for analyzing content to help with pattern generation.
    """
    
    @staticmethod
    def find_common_delimiters(examples: List[str]) -> Dict[str, int]:
        """Find common delimiters across a set of examples"""
        common_delimiters = {}
        potential_delimiters = ['```', '###', '---', '===', '***', '<<<', '>>>', '<tag>', '</tag>']
        
        for delimiter in potential_delimiters:
            count = sum(1 for example in examples if delimiter in example)
            if count > 0:
                common_delimiters[delimiter] = count
        
        return common_delimiters
    
    @staticmethod
    def detect_code_blocks(content: str) -> List[Dict[str, Any]]:
        """Detect code blocks and their languages in content"""
        code_blocks = []
        
        # Look for markdown code blocks with language specifier
        markdown_blocks = re.findall(r'```([a-zA-Z0-9+#]*)\s*([\s\S]*?)```', content, re.DOTALL)
        
        for lang, code in markdown_blocks:
            code_blocks.append({
                "type": "markdown",
                "language": lang.strip() if lang.strip() else "unknown",
                "content": code.strip()
            })
        
        # Look for HTML code blocks
        html_blocks = re.findall(r'<pre(?:\s+class="[^"]*(?:language-|lang-)([^"\s]+)[^"]*")?[^>]*>([\s\S]*?)</pre>', content, re.DOTALL)
        
        for lang, code in html_blocks:
            code_blocks.append({
                "type": "html",
                "language": lang.strip() if lang.strip() else "unknown",
                "content": code.strip()
            })
        
        return code_blocks
    
    @staticmethod
    def detect_data_structures(content: str) -> Dict[str, List[str]]:
        """Detect common data structures in content"""
        data_structures = {
            "json": [],
            "yaml": [],
            "csv": [],
            "table": []
        }
        
        # Detect potential JSON objects or arrays
        json_matches = re.findall(r'({[\s\S]*?}|\[[\s\S]*?\])', content)
        for match in json_matches:
            try:
                json.loads(match)
                data_structures["json"].append(match)
            except:
                pass
        
        # Detect potential YAML
        yaml_matches = re.findall(r'(?:^|\n)([a-zA-Z0-9_-]+:\s*(?:.*\n+(?:\s+.*\n+)*)+)', content)
        data_structures["yaml"] = yaml_matches
        
        # Detect potential CSV
        csv_lines = re.findall(r'(?:^|\n)([^,\n]+(?:,[^,\n]+){2,}\n+(?:[^,\n]+(?:,[^,\n]+){2,}\n+)+)', content)
        data_structures["csv"] = csv_lines
        
        # Detect markdown tables
        table_matches = re.findall(r'\|(.+)\|\n\|(?:[-:]+\|)+(?:\n\|.+\|)+', content)
        data_structures["table"] = table_matches
        
        return data_structures
    
    @staticmethod
    def suggest_parser_type(examples: List[str]) -> str:
        """Suggest an appropriate parser type based on content examples"""
        # Check if examples look like JSON
        json_count = 0
        for example in examples:
            example = example.strip()
            if (example.startswith('{') and example.endswith('}')) or (example.startswith('[') and example.endswith(']')):
                try:
                    json.loads(example)
                    json_count += 1
                except:
                    pass
        
        # If most examples are JSON, suggest JSON parser
        if json_count > len(examples) / 2:
            return "json"
        
        return "text"
