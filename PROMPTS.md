# PROMPTS.md

## Architecture Planning Prompt

You are a senior software architect.

Project:
mycompress

Tech Stack:
React + FastAPI.

Requirements:
[paste requirements]

Tasks:

1. Analyze requirements.
2. Suggest project architecture.
3. Create folder structure.
4. Identify risks.
5. Create implementation roadmap.
6. Suggest testing strategy.

Output in markdown.

## Feature Implementation Prompt

You are a senior Python engineer.

Context:
Read AGENTS.md and PROJECT_SPEC.md first.

Task:
Implement Image LSB Steganography module.

Requirements:

* Encode message
* Decode message
* Handle UTF-8
* Error handling
* Type hints
* Unit tests

Provide:

1. Design explanation
2. Folder structure
3. Implementation code
4. Tests

## Code Review Prompt

Review this code.

Tasks:

1. Find bugs
2. Find security issues
3. Find performance issues
4. Suggest improvements
5. Refactor if necessary

Return detailed findings.

## Bug Fix Prompt

Analyze this error.

Context:
[paste stacktrace]

Tasks:

1. Root cause analysis
2. Fix proposal
3. Correct implementation
4. Regression test
