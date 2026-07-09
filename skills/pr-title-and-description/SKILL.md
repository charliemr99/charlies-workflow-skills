---
name: pr-title-and-description
description: Generate PR title and description using conventional commits and the repo PR template from the diff vs base branch.
metadata:
  short-description: PR title + description generator
---

- Always generate the PR title and PR Description

## PR Title

- Use conventional commits with context:
- type(context): description

### Types

- `feat`: New feature or functionality
- `refactor`: Code restructuring without changing external behavior
- `fix`: Bug fixes
- `perf`: Performance improvements
- `chore`: Maintenance tasks, dependency updates
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `style`: Formatting, missing semicolons, etc.
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts

### Context

- Use specific module/feature names: `symbol-page`, `essentials`, `api`, `logos`, `checkout`, `auth`, etc.
- Keep context concise (1-3 words)
- Use kebab-case for multi-word contexts

### Description

- Be specific and descriptive
- Start with lowercase
- Use imperative mood
- Keep under 72 characters if possible
- Don't end with a period

## PR Description

- Use the changes diff with the main branch to summarize the changes for the description.
- Follow the following PR template:.

## PR Template

Title: <type(context): description>

Description:

# Tl;dr
<!-- Brief description/list of work performed -->
<!-- - Closes #ISSUE -->
- ...

# Details
<!-- Any relevant details so a developer not familiar with this work can gauge the complexity of work performed. This can include issues faced while developing or implementation that may not be straight forward to another developer. If appropriate link references or slack conversations. -->
- ...

# How to verify
<!-- How to verify work performed -->
- ...
