# Bulletin Project Guidelines

## Commands
- Run script: `python main.py [options] [parish_ids]`
- Common options: `-a` (all parishes), `-m` (mass times), `-c` (confession), `-e` (adoration), `-d` (dry run), `-v` (verbose)
- Example: `python main.py -a -m -c -v` (process all parishes, get mass and confession times, verbose output)
- Environment: Run `source .env` before executing scripts

## Testing
- Run all tests: `python -m pytest`
- Run tests with verbose output: `python -m pytest -v`
- Run specific test file: `python -m pytest tests/test_download_bulletins.py`
- Run specific test function: `python -m pytest tests/test_download_bulletins.py::test_download_bulletin_parishes_online_success`
- Skip integration tests: `python -m pytest -m "not integration"`
- Show print output during tests: `python -m pytest -s`
- Run tests without capturing output: `python -m pytest -xvs`

## Code Style
- **Imports**: Standard library first, third-party second, local modules last
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Type Hints**: Use typing module for function parameters and return values
- **Error Handling**: Use try/except blocks with specific exception types when possible
- **Documentation**: Add docstrings to functions and classes explaining purpose and parameters
- **Models**: Use Pydantic for data validation when appropriate

## Structure
- Main functionality in `main.py`
- PDF processing: `structured_output_extract.py` (OpenAI API)
- Parish data management: `notion_stuff.py` (Notion API)
- Bulletin downloading: `download_bulletins.py`
- Tests in `tests/` directory