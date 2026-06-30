# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enterprise-grade production hardening features
- Kubernetes deployment manifests with NetworkPolicy
- Health monitoring and metrics collection
- Plugin system architecture
- MCP server with rate limiting and threading support
- Coverage reporting and comprehensive test examples
- Documentation for architecture, setup, and deployment

### Changed
- Improved MCP server response handling with cross-platform threading
- Updated code structure for better readability and maintainability
- Refactored tests to use tmp_path for consistent temporary directories
- Enhanced backend storage directory handling in orchestrator

### Fixed
- MCP server compatibility issues across platforms
- CI pipeline errors and test reliability
- Documentation paths corrected from lithic_cli/ to src/lithic_cli/
- Plugin system integration and stability

### Security
- Added audit logging and security guidelines
- Implemented proper rate limiting for MCP endpoints
- Enhanced input validation and error handling

## [0.2.0] - 2024-12-30

### Added
- Initial release of Lithic-CLI
- Graph-based codebase indexing with graphify integration
- AI agent orchestration with compression and response policies
- Multi-provider LLM support (OpenAI, Anthropic, Ollama, OpenRouter)
- MCP (Model Context Protocol) server implementation
- Docker containerization with health checks
- Comprehensive documentation and examples

### Changed
- Project renamed from Lithic to Lithic-CLI for clarity
- Updated all references and links to use new naming convention

### Fixed
- Installation and setup procedures
- Cross-platform compatibility improvements

---

## Release Process

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated changelog generation. 

### Commit Types
- `feat:` - New features
- `fix:` - Bug fixes  
- `docs:` - Documentation changes
- `refactor:` - Code refactoring without functionality changes
- `test:` - Test additions or modifications
- `ci:` - CI/CD pipeline changes
- `chore:` - Maintenance tasks

### Generating Releases
Releases are automatically created from the main branch when version tags are pushed. The changelog is updated based on conventional commit messages since the last release.