# Shadow Utils Tests

This folder contains comprehensive tests for the shadow_utils.py functions: `withdraw`, `rebalance`, and `track`.

## Test Files

### 1. `test_shadow_withdraw.py`

Tests the withdraw function including:

- UI interaction simulation (clicking buttons)
- Pool removal from JSON state
- Error handling scenarios
- State preservation

### 2. `test_shadow_rebalance.py`

Tests the rebalance function including:

- Navigation to trade page
- Token selection and input filling
- Special handling for SHADOW token
- Swap execution logic
- Error handling

### 3. `test_shadow_track.py`

Tests the track function including:

- Pool data retrieval from JSON state
- Settings loading and default values
- Price monitoring and threshold detection
- Automatic rebalancing workflow
- Continuous monitoring loop

### 4. `test_shadow_simple.py`

Simple test runner that doesn't require pytest installation:

- Basic functionality tests
- Can be run directly with Python
- Good for quick testing without dependencies

## Running Tests

### Option 1: With pytest (Recommended)

1. Install test dependencies:

```bash
pip install -r tests/requirements-test.txt
```

2. Run all tests:

```bash
pytest tests/test_shadow_*.py -v
```

3. Run specific test file:

```bash
pytest tests/test_shadow_withdraw.py -v
```

4. Run with coverage:

```bash
pytest tests/test_shadow_*.py --cov=utils.shadow_utils --cov-report=html
```

### Option 2: Simple Python runner

Run the simple test suite without installing pytest:

```bash
python tests/test_shadow_simple.py
```

## Test Structure

Each test file follows this pattern:

1. **Setup**: Mock browser, pages, and UI elements
2. **Execution**: Call the function under test
3. **Verification**: Assert expected behavior occurred
4. **Cleanup**: Handle temporary files and state

## Mock Objects

The tests use extensive mocking to simulate:

- Browser automation (Playwright)
- UI elements and interactions
- File system operations
- Async operations and timing

## Test Coverage

The tests cover:

- ✅ Normal operation flows
- ✅ Error handling scenarios
- ✅ Edge cases (empty data, missing files)
- ✅ State management (JSON loading/saving)
- ✅ UI interaction sequences
- ✅ Async timing and loops

## Adding New Tests

When adding new tests:

1. Follow the existing pattern of fixtures and mocks
2. Test both success and failure scenarios
3. Verify state changes and side effects
4. Include proper cleanup for temporary files
5. Add docstrings explaining what each test does

## Common Issues

- **Import errors**: Make sure the project root is in Python path
- **Async test failures**: Use `@pytest.mark.asyncio` for async tests
- **Mock not working**: Ensure you're patching the correct module path
- **State file conflicts**: Use temporary files for state testing
