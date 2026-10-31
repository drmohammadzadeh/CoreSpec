# Task 1 Brief: Create the 6 Dedicated File-Parsing Skills

## Role in Project
Establish the 6 foundational file-parsing skills in `.skills/` that provide exact operational heuristics, regex patterns, and translation rules for converting Apache Fineract files into standardized EARS requirements.

## Files to Create
1. `.skills/fineract-java-parser/SKILL.md`
2. `.skills/fineract-gradle-parser/SKILL.md`
3. `.skills/fineract-config-parser/SKILL.md`
4. `.skills/fineract-xml-parser/SKILL.md`
5. `.skills/fineract-doc-parser/SKILL.md`
6. `.skills/fineract-db-schema-parser/SKILL.md`

## Requirements
Each skill must:
1. Start with valid YAML frontmatter containing `name` and `description` (third-person, specifying what it does and when to activate).
2. Detail exact file extensions and locations in Fineract codebase.
3. Provide concrete code extraction patterns and examples mapping source constructs directly to the 6 EARS patterns (Ubiquitous, State-Driven, Event-Driven, Optional Feature, Unwanted Behavior, Complex).
4. Strictly enforce the normative modal verb `shall` in EARS output examples.
5. Emphasize the bilingual presentation (English EARS clause + Persian business explanation + code traceability).

## Report Contract
Implement the files, verify them with PowerShell (`Get-ChildItem -Path .skills -Recurse -Filter "SKILL.md"`), commit the files with `git add .skills/; git commit -m "feat(skills): add 6 dedicated file-parsing skills for Fineract reverse engineering"`, and write your full report to `docs/sdd/task-1-report.md`. Return status `DONE`, commits, and a one-line test summary.
