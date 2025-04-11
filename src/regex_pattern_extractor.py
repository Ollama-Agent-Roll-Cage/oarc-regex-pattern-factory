"""
RegEx Pattern Factory for extracting formatted code blocks from LLM responses,
with persistent storage in Parquet format.

Author: Based on example from ollama-pyqt-json-formatting.md
Date: 4/11/2025
"""

import re
import json
import logging
import os
from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd

# Import the ParquetStorage class
from parquet_storage import ParquetStorage

class RegExPatternFactory:
    """Factory class for managing, creating and applying RegEx patterns for code block extraction"""
    
    DEFAULT_PATTERNS = {
        "json": {
            "name": "JSON Pattern",
            "description": "Extract JSON from markdown code blocks",
            "pattern": r'```json\s*([\s\S]*?)\s*```',
            "fallback_patterns": [
                r'```\s*([\s\S]*?)\s*```',  # Any code block
                r'{[\s\S]*?}'  # Raw JSON-like content
            ],
            "parser": "json"
        },
        "python": {
            "name": "Python Pattern",
            "description": "Extract Python code from markdown code blocks",
            "pattern": r'```python\s*([\s\S]*?)\s*```',
            "fallback_patterns": [
                r'```py\s*([\s\S]*?)\s*```',
                r'```\s*([\s\S]*?)\s*```'  # Any code block
            ],
            "parser": "text"
        },
        "mermaid": {
            "name": "Mermaid Pattern",
            "description": "Extract Mermaid diagrams from markdown code blocks",
            "pattern": r'```mermaid\s*([\s\S]*?)\s*```',
            "fallback_patterns": [
                r'```\s*([\s\S]*?)\s*```'  # Any code block
            ],
            "parser": "text"
        },
        "html": {
            "name": "HTML Pattern",
            "description": "Extract HTML from markdown code blocks",
            "pattern": r'```html\s*([\s\S]*?)\s*```',
            "fallback_patterns": [
                r'```\s*([\s\S]*?)\s*```',  # Any code block
                r'<html>[\s\S]*?</html>'  # Raw HTML content
            ],
            "parser": "text"
        },
        "css": {
            "name": "CSS Pattern",
            "description": "Extract CSS from markdown code blocks",
            "pattern": r'```css\s*([\s\S]*?)\s*```',
            "fallback_patterns": [
                r'```\s*([\s\S]*?)\s*```'  # Any code block
            ],
            "parser": "text"
        }
    }
    
    def __init__(self, storage_path: str = "regex_patterns.parquet"):
        """Initialize the RegEx Pattern Factory with storage path"""
        self.storage_path = storage_path
        self.patterns = {}
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load patterns from Parquet file or initialize with defaults"""
        patterns_df = ParquetStorage.load_from_parquet(self.storage_path)
        
        if patterns_df is None:
            # Initialize with default patterns if storage doesn't exist
            self.patterns = self.DEFAULT_PATTERNS.copy()
            self._save_patterns()
        else:
            # Convert DataFrame to dictionary
            self.patterns = {}
            for _, row in patterns_df.iterrows():
                pattern_id = row['pattern_id']
                self.patterns[pattern_id] = {
                    'name': row['name'],
                    'description': row['description'],
                    'pattern': row['pattern'],
                    'fallback_patterns': json.loads(row['fallback_patterns']),
                    'parser': row['parser']
                }
    
    def _save_patterns(self) -> bool:
        """Save patterns to Parquet file"""
        patterns_list = []
        for pattern_id, pattern_data in self.patterns.items():
            patterns_list.append({
                'pattern_id': pattern_id,
                'name': pattern_data['name'],
                'description': pattern_data['description'],
                'pattern': pattern_data['pattern'],
                'fallback_patterns': json.dumps(pattern_data['fallback_patterns']),
                'parser': pattern_data['parser']
            })
        
        return ParquetStorage.save_to_parquet(patterns_list, self.storage_path)
    
    def add_pattern(self, 
                   pattern_id: str, 
                   name: str, 
                   description: str, 
                   pattern: str, 
                   fallback_patterns: List[str] = None,
                   parser: str = "text") -> bool:
        """Add a new pattern or update an existing one"""
        self.patterns[pattern_id] = {
            'name': name,
            'description': description,
            'pattern': pattern,
            'fallback_patterns': fallback_patterns or [],
            'parser': parser
        }
        return self._save_patterns()
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove a pattern by its ID"""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            return self._save_patterns()
        return False
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Get a pattern by its ID"""
        return self.patterns.get(pattern_id)
    
    def list_patterns(self) -> List[Dict]:
        """List all available patterns"""
        return [{"id": k, **v} for k, v in self.patterns.items()]
    
    def extract_content(self, 
                       content: str, 
                       pattern_id: str,
                       parse: bool = True) -> Union[Any, List[str], None]:
        """Extract content using the specified pattern"""
        pattern_info = self.get_pattern(pattern_id)
        if not pattern_info:
            logging.error(f"Pattern '{pattern_id}' not found")
            return None
        
        # Try the main pattern first
        matches = re.findall(pattern_info['pattern'], content, re.DOTALL)
        
        # If no matches, try fallback patterns
        if not matches and pattern_info['fallback_patterns']:
            for fallback in pattern_info['fallback_patterns']:
                matches = re.findall(fallback, content, re.DOTALL)
                if matches:
                    break
        
        if not matches:
            return None
        
        # Parse the content if requested
        if parse:
            parser_type = pattern_info['parser']
            if parser_type == "json":
                # Try to parse each match as JSON
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except json.JSONDecodeError:
                        continue
                return None
            else:
                # Return as text
                return [match.strip() for match in matches]
        
        # Return raw matches
        return matches


class ContentExtractor:
    """Utility class for extracting different types of content from LLM responses"""
    
    def __init__(self, patterns_storage_path: str = "regex_patterns.parquet"):
        """Initialize the ContentExtractor with RegExPatternFactory"""
        self.pattern_factory = RegExPatternFactory(patterns_storage_path)
    
    def extract_json(self, content: str) -> Optional[Dict]:
        """Extract and parse JSON from markdown-formatted content"""
        return self.pattern_factory.extract_content(content, "json", parse=True)
    
    def extract_python(self, content: str) -> Optional[List[str]]:
        """Extract Python code from markdown-formatted content"""
        return self.pattern_factory.extract_content(content, "python", parse=False)
    
    def extract_mermaid(self, content: str) -> Optional[List[str]]:
        """Extract Mermaid diagrams from markdown-formatted content"""
        return self.pattern_factory.extract_content(content, "mermaid", parse=False)
    
    def extract_all(self, content: str) -> Dict[str, Any]:
        """Extract all types of content from a response"""
        results = {}
        for pattern_id in self.pattern_factory.patterns:
            extracted = self.pattern_factory.extract_content(content, pattern_id, parse=True)
            if extracted:
                results[pattern_id] = extracted
        return results
    
    def extract_custom(self, content: str, pattern_id: str, parse: bool = True) -> Any:
        """Extract content using a custom pattern"""
        return self.pattern_factory.extract_content(content, pattern_id, parse=parse)


# Example usage
if __name__ == "__main__":
    # Example LLM response
    llm_response = """
    Here's some JSON data:
    
    ```json
    {
      "status": "success",
      "data": {
        "name": "John Doe",
        "age": 30,
        "interests": ["coding", "hiking"]
      }
    }
    ```
    
    And here's a Python example:
    
    ```python
    def hello_world():
        print("Hello, world!")
        return 42
    ```
    
    Also, here's a Mermaid diagram:
    
    ```mermaid
    graph TD;
        A-->B;
        A-->C;
        B-->D;
        C-->D;
    ```
    """
    
    # Create extractor
    extractor = ContentExtractor()
    
    # Extract different types of content
    json_data = extractor.extract_json(llm_response)
    python_code = extractor.extract_python(llm_response)
    mermaid_diagram = extractor.extract_mermaid(llm_response)
    
    print("JSON Data:", json_data)
    print("Python Code:", python_code)
    print("Mermaid Diagram:", mermaid_diagram)
    
    # Add a custom pattern
    extractor.pattern_factory.add_pattern(
        pattern_id="sql",
        name="SQL Pattern",
        description="Extract SQL queries from markdown code blocks",
        pattern=r'```sql\s*([\s\S]*?)\s*```',
        fallback_patterns=[r'```\s*([\s\S]*?)\s*```'],
        parser="text"
    )
    
    # Extract all content types
    all_content = extractor.extract_all(llm_response)
    print("All Content:", all_content)
