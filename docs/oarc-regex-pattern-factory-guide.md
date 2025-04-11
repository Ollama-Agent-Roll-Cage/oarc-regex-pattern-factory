# OARC Regex Pattern Factory Module Usage Guide

The OARC Regex Pattern Factory Module is a powerful system for extracting structured content from unstructured text, particularly from Large Language Model (LLM) responses. This guide explains how to use the four core files that make up the module:

1. **regex_pattern_extractor.py** - Core extraction functionality
2. **regex_pattern_generator.py** - AI-powered pattern generation
3. **oarc_pattern_module.py** - Unified API that ties everything together
4. **parquet_storage.py** - Persistent storage for patterns

## Installation Requirements

Before using OARC, ensure you have the following dependencies:

```bash
pip install pandas pyarrow
pip install ollama  # Optional but required for pattern generation features
```

## Basic Usage

### 1. Initializing the Module

Start by importing and initializing the OARC Pattern Module:

```python
from oarc_pattern_module import create_oarc_pattern_module

# Create with default settings (patterns stored in "oarc_patterns.parquet")
oarc = create_oarc_pattern_module()

# Or with custom settings
oarc = create_oarc_pattern_module(
    storage_path="custom_patterns.parquet",
    model_name="llama3",  # Ollama model to use for generation
    auto_init=True  # Initialize with default patterns
)
```

### 2. Extracting Content

Extract content using built-in patterns:

```python
# Example LLM response with different content types
llm_response = """
Here's some JSON data:

```json
{
  "name": "John Doe",
  "age": 30,
  "interests": ["coding", "hiking"]
}
```

And here's a Python example:

```python
def hello_world():
    print("Hello, world!")
    return 42
```
"""

# Extract JSON
json_data = oarc.extract_json(llm_response)
print("JSON Data:", json_data)
# Output: {'name': 'John Doe', 'age': 30, 'interests': ['coding', 'hiking']}

# Extract Python code
python_code = oarc.extract_code(llm_response, language="python")
print("Python Code:", python_code)
# Output: ["def hello_world():\n    print(\"Hello, world!\")\n    return 42"]

# Extract all recognized patterns
all_content = oarc.extract_all(llm_response)
print("All Content Types:", list(all_content.keys()))
```

### 3. Managing Patterns

Add, remove, and manage regex patterns:

```python
# Add a custom pattern
oarc.add_pattern(
    pattern_id="email",  # Unique identifier
    pattern=r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Regex pattern
    name="Email Pattern",  # Human-readable name
    description="Extract email addresses from text",
    fallback_patterns=[],  # Alternative patterns if main one fails
    parser="text"  # How to process matches ("text" or "json")
)

# List available patterns
patterns = oarc.list_patterns()
for pattern in patterns:
    print(f"- {pattern['id']}: {pattern['name']}")

# Get pattern details
email_pattern = oarc.get_pattern("email")
print(email_pattern["pattern"])

# Remove a pattern
oarc.remove_pattern("email")

# Export patterns to JSON
oarc.export_patterns("my_patterns.json")

# Import patterns from JSON
oarc.import_patterns("my_patterns.json")
```

## Advanced Features with Ollama

The OARC module can use Ollama to automatically generate and optimize regex patterns.

### 1. Generating Patterns from Examples

```python
# Generate a pattern from examples
custom_tag_examples = [
    "<custom>This is example 1</custom>",
    "<custom>Another example</custom>",
    "<custom>Yet another example with different content</custom>"
]

pattern_data = oarc.generate_pattern(
    examples=custom_tag_examples,
    pattern_id="custom_tag",
    name="Custom Tag Pattern",
    description="Extract content between custom tags"
)

print("Generated pattern:", pattern_data["pattern"])
# Output might be: r'<custom>([\s\S]*?)</custom>'

# Test the generated pattern
test_text = "Here's a <custom>new example</custom> to extract"
extracted = oarc.extract_content(test_text, "custom_tag")
print("Extracted:", extracted)
```

### 2. Analyzing Content to Generate Patterns

```python
# Extract content by analyzing full text and a target
full_text = """
This is a document with special blocks.

<METRICS>
Revenue: $1.2M
Growth: 15%
</METRICS>

Other content here...
"""

target = """
<METRICS>
Revenue: $1.2M
Growth: 15%
</METRICS>
"""

metrics_pattern = oarc.analyze_and_generate_pattern(
    content=full_text,
    target_extract=target,
    pattern_id="metrics_block"
)

print("Generated metrics pattern:", metrics_pattern["pattern"])
```

### 3. Discovering Patterns in Content

```python
# Analyze content to discover potential patterns
pattern_suggestions = oarc.discover_patterns_in_content(complex_document)

for suggestion in pattern_suggestions:
    print(f"Discovered pattern: {suggestion['name']}")
    print(f"  ID: {suggestion['pattern_id']}")
    print(f"  Description: {suggestion['description']}")
    print(f"  Example: {suggestion['example'][:50]}...")
```

### 4. Optimizing Patterns

```python
# Add a simple initial pattern
oarc.add_pattern(
    pattern_id="email",
    pattern=r'[\w\.-]+@[\w\.-]+',  # Basic pattern
    name="Simple Email Pattern"
)

# Optimize with examples
test_examples = [
    "Contact us at support@example.com for assistance.",
    "My email is john.doe@company-name.co.uk.",
    "Send your resume to careers@tech.org by Friday."
]

optimization_results = oarc.optimize_pattern(
    pattern_id="email",
    examples=test_examples,
    update_factory=True  # Update the pattern in storage
)

print("Improved pattern:", optimization_results["pattern"])
print("Match improvement:", optimization_results["improvement"], "%")
```

### 5. Automatic Pattern Learning

```python
# Automatically discover and create patterns from content
learned_patterns = oarc.learn_from_content(
    content=complex_document,
    min_confidence=70.0,  # Minimum confidence score (0-100)
    auto_add=True  # Add patterns to factory automatically
)

for pattern in learned_patterns:
    print(f"Learned pattern: {pattern['name']} ({pattern['status']})")
    if pattern['status'] == 'added':
        print(f"  Confidence: {pattern['confidence']:.1f}%")
```

## Working Without Ollama

If Ollama is not available, the module will still work for basic pattern extraction but without AI-powered generation features:

```python
# Check if Ollama features are available
if oarc.ollama_available:
    # Use pattern generation
    pattern = oarc.generate_pattern(examples, "pattern_id")
else:
    # Fall back to manual pattern creation
    oarc.add_pattern(
        pattern_id="pattern_id",
        pattern=r'your_manual_regex_pattern',
        name="Manual Pattern"
    )
```

## Using the Core Components Directly

While the unified API is recommended, you can also use the core components directly:

### Using RegExPatternFactory Directly

```python
from regex_pattern_extractor import RegExPatternFactory

# Create a pattern factory
factory = RegExPatternFactory(storage_path="patterns.parquet")

# Add a pattern
factory.add_pattern(
    pattern_id="date",
    name="Date Pattern",
    description="Extract dates in YYYY-MM-DD format",
    pattern=r'(\d{4}-\d{2}-\d{2})',
    fallback_patterns=[r'(\d{2}/\d{2}/\d{4})'],
    parser="text"
)

# Extract content
content = "Meeting scheduled for 2025-04-15"
dates = factory.extract_content(content, "date", parse=True)
```

### Using ContentExtractor Directly

```python
from regex_pattern_extractor import ContentExtractor

# Create an extractor
extractor = ContentExtractor(patterns_storage_path="patterns.parquet")

# Extract different content types
json_data = extractor.extract_json(llm_response)
python_code = extractor.extract_python(llm_response)
all_content = extractor.extract_all(llm_response)
```

### Using OllamaPatternGenerator Directly

```python
from regex_pattern_generator import OllamaPatternGenerator

# Create a generator
generator = OllamaPatternGenerator(model_name="llama3")

# Generate a pattern
pattern_data = generator.generate_pattern_from_examples(
    examples=examples,
    pattern_id="custom_pattern"
)

# Test a pattern
test_results = generator.test_pattern_on_examples(
    pattern=pattern,
    examples=test_examples
)
```

## Best Practices

1. **Use Descriptive Pattern IDs**: Choose clear, descriptive pattern IDs that reflect what the pattern extracts.

2. **Include Fallback Patterns**: For more robust extraction, include fallback patterns that can match content when the primary pattern fails.

3. **Choose the Right Parser**: Use "text" for general content and "json" for JSON data that needs to be parsed.

4. **Test Thoroughly**: Always test patterns with varied examples to ensure they extract content correctly.

5. **Leverage the AI**: When possible, use the pattern generation and optimization features to create more robust patterns.

6. **Persistent Storage**: Let the module handle persistent storage through the ParquetStorage class.

7. **Export Important Patterns**: Export valuable pattern collections to JSON for sharing or backup.

## Troubleshooting

### Pattern Not Matching

If a pattern isn't matching as expected:

1. Test with simpler content first
2. Make sure you're using `re.DOTALL` flag (the module handles this automatically)
3. Check if you need capture groups `(...)` in your pattern
4. Try using fallback patterns for edge cases

### Ollama Integration Issues

If you encounter issues with Ollama:

1. Make sure Ollama is installed: `pip install ollama`
2. Verify you have a working Ollama model available (e.g., "llama3")
3. Check the model's capabilities for regex pattern generation
4. Try a different model if results are poor

### Data Storage Issues

If you have trouble with pattern storage:

1. Verify you have pandas and pyarrow installed
2. Check file permissions for the Parquet storage file
3. Try specifying an absolute path for the storage file
4. Export to JSON as a backup method
