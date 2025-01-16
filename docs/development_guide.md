# eBoekhoudRobot Development Guide

## Getting Started

### Prerequisites

1. Python Environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

2. Dependencies
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Environment Setup
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### Project Structure

```
eBoekhoudRobot/
├── src/                    # Core source code
│   ├── eboekhouden.py     # E-boekhouden automation
│   ├── logging_config.py  # Logging setup
│   ├── database.py       # Database operations
│   ├── container.py      # Dependency injection
│   └── config.py         # Configuration system
├── tests/                 # Test suite
│   ├── test_eboekhouden.py
│   ├── test_logging.py
│   ├── test_database.py
│   └── test_config.py
├── docs/                  # Documentation
├── schemas/              # JSON schemas
├── output/              # Generated files
├── temp/                # Temporary files
├── logs/               # Log files
└── main.py            # Entry point
```

## Development Workflow

### 1. Code Style

Follow these guidelines:
- Use type hints
- Write docstrings (Google style)
- Follow PEP 8
- Maximum line length: 100 characters

Example:
```python
def process_data(data: list[dict]) -> dict:
    """Process raw data into structured format.
    
    Args:
        data: List of raw data dictionaries
        
    Returns:
        Processed data dictionary
        
    Raises:
        ValidationError: If data validation fails
    """
    # Implementation
```

### 2. Error Handling

Follow this pattern:
```python
try:
    # Operation that might fail
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    self._save_error_state()
    raise OperationError(f"Failed to perform operation: {e}")
```

### 3. Logging

Use component-specific loggers:
```python
from src.logging_config import get_logger

logger = get_logger("component_name")
logger.info("Operation started")
logger.error("Operation failed", exc_info=True)
```

### 4. Testing

#### Unit Tests
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_name(input_data)
    
    # Assert
    assert result == expected_output
```

#### Integration Tests
```python
@pytest.mark.integration
def test_component_integration(mock_dependency):
    """Test component integration."""
    # Setup
    component = Component(mock_dependency)
    
    # Execute
    result = component.operation()
    
    # Verify
    assert result.status == "success"
```

### 5. Documentation

#### Function Documentation
```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.
    
    Longer description explaining the function's purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ErrorType: Description of error conditions
    """
```

#### Class Documentation
```python
class ClassName:
    """Short description.
    
    Detailed description of the class, its purpose,
    and any important implementation details.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
```

## Common Tasks

### 1. Adding New Features

1. Create feature branch
   ```bash
   git checkout -b feature/feature-name
   ```

2. Implement feature
   - Add tests first
   - Implement feature
   - Update documentation

3. Run tests
   ```bash
   pytest tests/
   ```

### 2. Debugging

1. Enable debug logging
   ```python
   logger.setLevel(logging.DEBUG)
   ```

2. Use screenshot capture
   ```python
   self._page.screenshot(path="debug.png")
   ```

3. Save page content
   ```python
   self._save_page_content("debug")
   ```

### 3. Configuration Changes

1. Update schema
   ```python
   class NewConfig(BaseModel):
       new_field: str = Field(...)
   ```

2. Update environment
   ```bash
   echo "NEW_CONFIG_VALUE=value" >> .env
   ```

3. Update documentation
   ```markdown
   ## Configuration
   - `NEW_CONFIG_VALUE`: Description
   ```

## Best Practices

### 1. Code Quality

- Write self-documenting code
- Keep functions small and focused
- Use meaningful variable names
- Add comments for complex logic

### 2. Testing

- Write tests before code
- Mock external dependencies
- Test edge cases
- Maintain high coverage

### 3. Error Handling

- Use specific exceptions
- Provide context in errors
- Log with appropriate levels
- Clean up resources

### 4. Performance

- Batch operations when possible
- Use efficient selectors
- Implement caching
- Monitor resource usage

## Troubleshooting

### 1. Browser Automation

Common issues and solutions:
- Selector not found
- Page load timeout
- Network errors
- Resource cleanup

### 2. Data Processing

Common issues and solutions:
- Invalid data format
- Schema validation
- Memory usage
- Performance

### 3. Configuration

Common issues and solutions:
- Missing values
- Invalid types
- Environment setup
- Validation errors

## Contributing

1. Fork repository
2. Create feature branch
3. Write tests
4. Implement changes
5. Update documentation
6. Submit pull request

## Resources

- [Python Documentation](https://docs.python.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [pytest Documentation](https://docs.pytest.org/) 