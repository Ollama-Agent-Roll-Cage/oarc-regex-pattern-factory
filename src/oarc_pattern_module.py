"""
OARC Pattern Module - Unified API for pattern extraction and generation

This module brings together the RegEx Pattern Factory and 
Pattern Generator to provide a unified API for the OARC package.

Author: OARC Contributors
Date: 4/11/2025
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

# Import components
from regex_pattern_extractor import RegExPatternFactory, ContentExtractor
from regex_pattern_generator import OllamaPatternGenerator, PatternDiscovery, ContentAnalysisUtils

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OARCPatternModule:
    """
    Unified API for the OARC Pattern Module.
    Provides pattern extraction, generation, and management capabilities.
    """
    
    def __init__(self, 
                storage_path: str = "oarc_patterns.parquet",
                model_name: str = "llama3",
                auto_init: bool = True):
        """
        Initialize the OARC Pattern Module.
        
        Args:
            storage_path: Path to store patterns
            model_name: Ollama model to use for pattern generation
            auto_init: Whether to automatically initialize with default patterns
        """
        self.storage_path = storage_path
        self.model_name = model_name
        
        # Initialize components
        self.pattern_factory = RegExPatternFactory(storage_path=storage_path)
        self.content_extractor = ContentExtractor(patterns_storage_path=storage_path)
        
        try:
            import ollama
            self.ollama_available = True
            
            # Initialize Ollama-based components
            self.pattern_generator = OllamaPatternGenerator(
                model_name=model_name,
                pattern_factory=self.pattern_factory
            )
            self.pattern_discovery = PatternDiscovery(model_name=model_name)
            
        except ImportError:
            logger.warning("Ollama package not available. Pattern generation features disabled.")
            self.ollama_available = False
            self.pattern_generator = None
            self.pattern_discovery = None
        
        # Content analysis utilities
        self.content_analysis = ContentAnalysisUtils()
        
        # Initialize with patterns if needed
        if auto_init and len(self.pattern_factory.list_patterns()) == 0:
            logger.info("No patterns found. Initializing with default patterns.")
            self._initialize_default_patterns()
    
    def _initialize_default_patterns(self):
        """Initialize with default patterns if storage is empty"""
        for pattern_id, pattern_data in RegExPatternFactory.DEFAULT_PATTERNS.items():
            self.pattern_factory.add_pattern(
                pattern_id=pattern_id,
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern=pattern_data["pattern"],
                fallback_patterns=pattern_data["fallback_patterns"],
                parser=pattern_data["parser"]
            )
    
    #-------------------------------------------------------------------------
    # Extraction Methods
    #-------------------------------------------------------------------------
    
    def extract_content(self, content: str, pattern_id: str, parse: bool = True) -> Any:
        """
        Extract content using a specific pattern.
        
        Args:
            content: Text to extract from
            pattern_id: ID of the pattern to use
            parse: Whether to parse the extracted content
            
        Returns:
            Extracted content
        """
        return self.content_extractor.extract_custom(content, pattern_id, parse)
    
    def extract_all(self, content: str) -> Dict[str, Any]:
        """
        Extract all recognized patterns from content.
        
        Args:
            content: Text to extract from
            
        Returns:
            Dictionary mapping pattern IDs to extracted content
        """
        return self.content_extractor.extract_all(content)
    
    def extract_json(self, content: str) -> Optional[Dict]:
        """
        Extract and parse JSON from content.
        
        Args:
            content: Text to extract from
            
        Returns:
            Extracted JSON as a dictionary
        """
        return self.content_extractor.extract_json(content)
    
    def extract_code(self, content: str, language: str = None) -> List[str]:
        """
        Extract code blocks from content, optionally filtering by language.
        
        Args:
            content: Text to extract from
            language: Optional language to filter by
            
        Returns:
            List of extracted code blocks
        """
        code_blocks = []
        
        # Try to extract using language-specific pattern if provided
        if language:
            lang_pattern_id = language.lower()
            extracted = self.extract_content(content, lang_pattern_id, parse=False)
            if extracted:
                return extracted if isinstance(extracted, list) else [extracted]
        
        # Fall back to generic code extraction
        extracted = self.extract_content(content, "code", parse=False)
        if extracted:
            # Filter by language if specified
            if language and isinstance(extracted, list):
                code_blocks = [block for block in extracted 
                            if isinstance(block, dict) and 
                            block.get("language", "").lower() == language.lower()]
            else:
                code_blocks = extracted if isinstance(extracted, list) else [extracted]
        
        return code_blocks
    
    #-------------------------------------------------------------------------
    # Pattern Management Methods
    #-------------------------------------------------------------------------
    
    def list_patterns(self) -> List[Dict]:
        """
        List all available patterns.
        
        Returns:
            List of pattern information dictionaries
        """
        return self.pattern_factory.list_patterns()
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """
        Get information about a specific pattern.
        
        Args:
            pattern_id: ID of the pattern
            
        Returns:
            Pattern information dictionary
        """
        return self.pattern_factory.get_pattern(pattern_id)
    
    def add_pattern(self, 
                   pattern_id: str, 
                   pattern: str, 
                   name: str = None, 
                   description: str = None,
                   fallback_patterns: List[str] = None,
                   parser: str = "text") -> bool:
        """
        Add a new pattern or update an existing one.
        
        Args:
            pattern_id: ID of the pattern
            pattern: RegEx pattern string
            name: Human-readable name
            description: Pattern description
            fallback_patterns: List of fallback patterns
            parser: Parser type ("text" or "json")
            
        Returns:
            True if successful
        """
        name = name or f"{pattern_id.capitalize()} Pattern"
        description = description or f"Extract {pattern_id} content from text"
        
        return self.pattern_factory.add_pattern(
            pattern_id=pattern_id,
            name=name,
            description=description,
            pattern=pattern,
            fallback_patterns=fallback_patterns or [],
            parser=parser
        )
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """
        Remove a pattern.
        
        Args:
            pattern_id: ID of the pattern to remove
            
        Returns:
            True if successful
        """
        return self.pattern_factory.remove_pattern(pattern_id)
    
    def export_patterns(self, export_path: str) -> bool:
        """
        Export patterns to a JSON file.
        
        Args:
            export_path: Path to export to
            
        Returns:
            True if successful
        """
        try:
            patterns = self.pattern_factory.list_patterns()
            
            with open(export_path, 'w') as f:
                json.dump(patterns, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting patterns: {e}")
            return False
    
    def import_patterns(self, import_path: str, overwrite: bool = False) -> bool:
        """
        Import patterns from a JSON file.
        
        Args:
            import_path: Path to import from
            overwrite: Whether to overwrite existing patterns
            
        Returns:
            True if successful
        """
        try:
            with open(import_path, 'r') as f:
                patterns = json.load(f)
            
            success = True
            for pattern in patterns:
                pattern_id = pattern.get("id")
                
                # Skip if pattern exists and overwrite is False
                if not overwrite and self.pattern_factory.get_pattern(pattern_id):
                    continue
                
                # Add the pattern
                result = self.pattern_factory.add_pattern(
                    pattern_id=pattern_id,
                    name=pattern.get("name"),
                    description=pattern.get("description"),
                    pattern=pattern.get("pattern"),
                    fallback_patterns=pattern.get("fallback_patterns", []),
                    parser=pattern.get("parser", "text")
                )
                
                success = success and result
            
            return success
        except Exception as e:
            logger.error(f"Error importing patterns: {e}")
            return False
    
    #-------------------------------------------------------------------------
    # Pattern Generation Methods
    #-------------------------------------------------------------------------
    
    def generate_pattern(self, 
                        examples: List[str], 
                        pattern_id: str,
                        name: str = None,
                        description: str = None,
                        add_to_factory: bool = True) -> Dict[str, Any]:
        """
        Generate a new RegEx pattern from examples.
        
        Args:
            examples: List of example strings
            pattern_id: ID for the new pattern
            name: Optional name for the pattern
            description: Optional description
            add_to_factory: Whether to add the pattern to the factory
            
        Returns:
            Pattern information dictionary
        """
        if not self.ollama_available:
            raise ImportError("Ollama package is required for pattern generation")
        
        pattern_data = self.pattern_generator.generate_pattern_from_examples(
            examples=examples,
            pattern_id=pattern_id,
            name=name,
            description=description
        )
        
        if add_to_factory:
            self.pattern_factory.add_pattern(
                pattern_id=pattern_data["pattern_id"],
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern=pattern_data["pattern"],
                fallback_patterns=pattern_data["fallback_patterns"],
                parser=pattern_data["parser"]
            )
        
        return pattern_data
    
    def analyze_and_generate_pattern(self,
                                   content: str,
                                   target_extract: str,
                                   pattern_id: str,
                                   name: str = None,
                                   description: str = None,
                                   add_to_factory: bool = True) -> Dict[str, Any]:
        """
        Analyze content to generate a pattern that extracts specific content.
        
        Args:
            content: Full content to analyze
            target_extract: Target content to extract
            pattern_id: ID for the new pattern
            name: Optional name for the pattern
            description: Optional description
            add_to_factory: Whether to add the pattern to the factory
            
        Returns:
            Pattern information dictionary
        """
        if not self.ollama_available:
            raise ImportError("Ollama package is required for pattern generation")
        
        pattern_data = self.pattern_generator.analyze_content_and_generate_pattern(
            content=content,
            target_extract=target_extract,
            pattern_id=pattern_id,
            name=name,
            description=description
        )
        
        if add_to_factory:
            self.pattern_factory.add_pattern(
                pattern_id=pattern_data["pattern_id"],
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern=pattern_data["pattern"],
                fallback_patterns=pattern_data["fallback_patterns"],
                parser=pattern_data["parser"]
            )
        
        return pattern_data
    
    def optimize_pattern(self, 
                        pattern_id: str, 
                        examples: List[str],
                        update_factory: bool = True) -> Dict[str, Any]:
        """
        Optimize an existing pattern for better performance.
        
        Args:
            pattern_id: ID of the pattern to optimize
            examples: List of example strings
            update_factory: Whether to update the pattern in the factory
            
        Returns:
            Optimization results
        """
        if not self.ollama_available:
            raise ImportError("Ollama package is required for pattern optimization")
        
        # Get the existing pattern
        pattern_info = self.pattern_factory.get_pattern(pattern_id)
        if not pattern_info:
            raise ValueError(f"Pattern '{pattern_id}' not found")
        
        # Optimize the pattern
        optimization_results = self.pattern_generator.optimize_pattern(
            initial_pattern=pattern_info["pattern"],
            examples=examples
        )
        
        # Update the pattern in the factory if requested
        if update_factory and optimization_results["improvement"] > 0:
            self.pattern_factory.add_pattern(
                pattern_id=pattern_id,
                name=pattern_info["name"],
                description=pattern_info["description"],
                pattern=optimization_results["pattern"],
                fallback_patterns=optimization_results["fallback_patterns"],
                parser=pattern_info["parser"]
            )
        
        return optimization_results
    
    def discover_patterns_in_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Analyze content to discover potential pattern types.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of pattern suggestions
        """
        if not self.ollama_available:
            raise ImportError("Ollama package is required for pattern discovery")
        
        return self.pattern_discovery.discover_patterns(content)
    
    def learn_from_content(self, 
                          content: str, 
                          min_confidence: float = 70.0,
                          auto_add: bool = False) -> List[Dict[str, Any]]:
        """
        Analyze content, discover patterns, and optionally add them to the factory.
        
        Args:
            content: Content to learn from
            min_confidence: Minimum confidence score to auto-add patterns
            auto_add: Whether to automatically add patterns to the factory
            
        Returns:
            List of discovered patterns with generation results
        """
        if not self.ollama_available:
            raise ImportError("Ollama package is required for pattern learning")
        
        # Discover potential patterns
        pattern_suggestions = self.pattern_discovery.discover_patterns(content)
        
        results = []
        for suggestion in pattern_suggestions:
            pattern_id = suggestion["pattern_id"]
            
            # Skip if pattern already exists
            if self.pattern_factory.get_pattern(pattern_id):
                suggestion["status"] = "exists"
                results.append(suggestion)
                continue
            
            # Try to generate a pattern based on the example
            try:
                # Extract example content
                example = suggestion["example"]
                
                # Generate pattern
                pattern_data = self.pattern_generator.analyze_content_and_generate_pattern(
                    content=content,
                    target_extract=example,
                    pattern_id=pattern_id,
                    name=suggestion["name"],
                    description=suggestion["description"]
                )
                
                # Test the pattern
                test_results = self.pattern_generator.test_pattern_on_examples(
                    pattern=pattern_data["pattern"],
                    examples=[example],
                    fallback_patterns=pattern_data["fallback_patterns"]
                )
                
                pattern_data["test_results"] = test_results
                pattern_data["confidence"] = test_results["match_percentage"]
                
                # Add to factory if confidence is high enough and auto_add is True
                if auto_add and test_results["match_percentage"] >= min_confidence:
                    self.pattern_factory.add_pattern(
                        pattern_id=pattern_id,
                        name=suggestion["name"],
                        description=suggestion["description"],
                        pattern=pattern_data["pattern"],
                        fallback_patterns=pattern_data["fallback_patterns"],
                        parser=pattern_data["parser"]
                    )
                    pattern_data["status"] = "added"
                else:
                    pattern_data["status"] = "generated"
                
                results.append({**suggestion, **pattern_data})
                
            except Exception as e:
                logger.error(f"Error generating pattern for '{pattern_id}': {e}")
                results.append({**suggestion, "status": "error", "error": str(e)})
        
        return results


# Convenience function to create and initialize the module
def create_oarc_pattern_module(storage_path: str = "oarc_patterns.parquet",
                             model_name: str = "llama3",
                             auto_init: bool = True) -> OARCPatternModule:
    """
    Create and initialize the OARC Pattern Module.
    
    Args:
        storage_path: Path to store patterns
        model_name: Ollama model to use for pattern generation
        auto_init: Whether to automatically initialize with default patterns
        
    Returns:
        Initialized OARCPatternModule instance
    """
    return OARCPatternModule(
        storage_path=storage_path,
        model_name=model_name,
        auto_init=auto_init
    )
