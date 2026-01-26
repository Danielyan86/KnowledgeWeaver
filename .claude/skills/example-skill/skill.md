# Example Skill

**Name**: example-skill
**Description**: A template skill for the KnowledgeWeaver project
**Version**: 1.0.0
**Author**: Your Name

## Purpose

This is an example skill that demonstrates the structure and format for creating custom Claude Code skills.

## Instructions

When this skill is invoked with `/example-skill`, Claude should:

1. Greet the user
2. Explain what this example skill does
3. Provide guidance on creating their own skills

## Usage

```
/example-skill
```

## Implementation

When invoked, respond with:

"This is an example skill!

To create your own skill:
1. Copy this directory: `cp -r .claude/skills/example-skill .claude/skills/your-skill-name`
2. Edit the skill.md file with your instructions
3. Invoke with `/your-skill-name`

Skills can include any instructions for Claude, such as:
- Running specific commands
- Following particular workflows
- Applying project-specific conventions
- Automating repetitive tasks"

## Notes

- Skills are project-specific and stored in `.claude/skills/`
- Each skill needs its own directory with a `skill.md` file
- Skills can include additional supporting files if needed
