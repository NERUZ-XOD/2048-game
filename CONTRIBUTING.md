# Contributing to Retro 2048

Thank you for considering contributing to Retro 2048! This document provides guidelines and instructions for contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your operating system and Python version

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:

- A clear, descriptive title
- Detailed description of the proposed feature
- Any relevant mockups or examples

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add comments for complex logic

### Game Mechanics

- Maintain the core 2048 game mechanics
- Ensure animations are smooth and responsive
- Test on different screen sizes and resolutions

### Tile Positioning

The game uses precise tile positioning to fit within the grid background:

- Tile size: 72x72 pixels
- Grid positions are manually defined with exact pixel coordinates:
  - Row 1: (25, 25), (117, 25), (209, 25), (301, 25)
  - Row 2: (25, 117), (117, 117), (209, 117), (301, 117)
  - Row 3: (25, 209), (117, 209), (209, 209), (301, 209)
  - Row 4: (25, 301), (117, 301), (209, 301), (301, 301)

Please maintain these positions when making changes to ensure proper alignment.

### Testing

- Test your changes thoroughly before submitting a pull request
- Ensure the game works on different operating systems
- Check that high scores and game saves function correctly

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
