# Claude Skills

This directory contains custom skills for Claude Code in the KnowledgeWeaver project.

## Structure

Each skill should be in its own subdirectory with a `skill.md` file:

```
skills/
  skill-name/
    skill.md          # Main skill definition (required)
    config.json       # Optional configuration
    other-files/      # Optional supporting files
```

## Skill Definition Format

The `skill.md` file should contain:

1. **Metadata** (optional):
   - Name
   - Description
   - Version
   - Author

2. **Instructions**: Clear instructions for Claude on what this skill does

3. **Examples** (optional): Usage examples

## Example Skill

See `example-skill/` for a template you can copy and modify.

## Creating a New Skill

1. Create a new directory: `mkdir .claude/skills/my-skill`
2. Create `skill.md`: `touch .claude/skills/my-skill/skill.md`
3. Edit `skill.md` with your skill instructions
4. Invoke with: `/my-skill` in Claude Code

## Available Skills

- `example-skill/` - Template for creating new skills
- `code-review/` - 深度代码审查，基于Clean Code、Clean Architecture、SOLID等原则，自动运行单元测试
