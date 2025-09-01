# CLAUDE.md - Specs Directory Organization Guide

This file provides guidance for maintaining and extending the specification-driven development process in this directory.

## Directory Structure

```
docs/specs/
├── CLAUDE.md (this file)
├── local-mode/
│   ├── phases-done/       # Completed implementation phases
│   ├── phases-pending/    # Specifications awaiting implementation
│   └── *.md              # Overview and context documents
└── [feature-name]/       # Future feature specifications
    ├── phases-done/
    └── phases-pending/
```

## Phase Specification Standards

### Required Sections
Every phase specification MUST include these sections in order:

1. **# Phase N: [Descriptive Title]**
2. **## Objective** - Single sentence stating what this phase accomplishes
3. **## Problem Summary** - Brief description of the issue being solved
4. **## Implementation Details** - Exact changes with file paths and line numbers
5. **## Agent Workflow** - Step-by-step instructions for implementation
6. **## Testing** - How to verify the implementation works
7. **## Success Criteria** - Checklist of completion requirements

### Implementation Details Format
```markdown
### File: `/absolute/path/to/file.py`

**Change N: [Description]**
**Location:** Line XXX
**Current Code:**
```python
[exact current code]
```

**New Code:**
```python
[exact new code]
```
```

### Key Principles

1. **Precision Over Ambiguity**
   - Use exact line numbers, not "around line X"
   - Show complete code snippets, not fragments
   - Specify absolute file paths

2. **Incremental Progress**
   - Each phase should be completable in 1-2 hours
   - Phases build on each other but remain independent
   - Critical fixes before enhancements

3. **Agent-Friendly Design**
   - Instructions should be executable without interpretation
   - Use numbered steps in workflows
   - Include verification steps

4. **Test-Driven Validation**
   - Every phase includes testing requirements
   - Prefer end-to-end tests over unit tests for phases
   - Include manual testing checklists

## Workflow Process

### Creating a New Phase Spec

1. **Identify the Problem**
   - Check existing ADRs for architectural guidance
   - Verify the issue hasn't been addressed
   - Determine criticality (blocking vs enhancement)

2. **Draft the Specification**
   - Use existing phase specs as templates
   - Verify line numbers by reading actual files
   - Include before/after code snippets

3. **Peer Review Process**
   - Use architect agent to draft
   - Use QA agent to review
   - Iterate until agreement reached
   - Save to `phases-pending/`

4. **Implementation**
   - Execute the agent workflow steps
   - Run specified tests
   - Check all success criteria
   - Move spec to `phases-done/` when complete

### Phase Naming Convention

```
phase-[N]-[descriptive-kebab-case].md
```

Examples:
- `phase-1-clientmanager-fix.md`
- `phase-2-port-configuration.md`
- `phase-5-recoverable-endpoint-implementation.md`

## Quality Standards

### DO:
- ✅ Include exact line numbers from actual code
- ✅ Show complete function signatures in changes
- ✅ Provide testable success criteria
- ✅ Reference relevant ADRs and policies
- ✅ Keep phases focused on single concerns

### DON'T:
- ❌ Use vague descriptions like "update the function"
- ❌ Omit testing requirements
- ❌ Combine unrelated changes in one phase
- ❌ Create phases larger than 2 hours of work
- ❌ Skip verification steps

## Integration with ADRs

Phase specifications implement Architecture Decision Records (ADRs):

- ADRs define the "why" and high-level "how"
- Phase specs define the exact "what" and detailed "how"
- Reference ADRs in phase objectives when applicable
- Create new ADRs for significant architectural changes

## Example Phase Spec Template

```markdown
# Phase N: [Title]

## Objective
[Single sentence goal]

## Problem Summary
[2-3 sentences describing the issue]

## Implementation Details

### File: `/path/to/file.py`

**Change 1: [What changes]**
**Location:** Line XXX
**Current Code:**
```python
[current code]
```

**New Code:**
```python
[new code]
```

## Agent Workflow

### Step 1: [Action]
1. [Specific instruction]
2. [Specific instruction]
3. [Specific instruction]

### Step 2: [Action]
1. [Specific instruction]
2. [Specific instruction]

## Testing

### Unit Tests
```bash
pytest tests/path/to/test.py -v
```

### Manual Testing
- [ ] [Test scenario 1]
- [ ] [Test scenario 2]
- [ ] [Verification step]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] All tests pass
- [ ] No regressions introduced
```

## Maintenance Guidelines

### Weekly Review
- Move completed specs from `phases-pending/` to `phases-done/`
- Archive obsolete specs with `OBSOLETE-` prefix
- Update phase numbers if reordering needed

### Documentation Updates
- Update main spec document when phases complete
- Keep running list of completed phases in README
- Document lessons learned in retrospectives

## Tips for Success

1. **Start Small**: First phases should be simple, confidence-building wins
2. **Verify First**: Always read the actual code before writing specs
3. **Test Early**: Run tests after each change, not at the end
4. **Document Surprises**: If reality differs from spec, update the spec
5. **Celebrate Progress**: Completed phases are victories worth noting

## Common Pitfalls to Avoid

1. **Stale Line Numbers**: Code changes, verify before implementation
2. **Missing Imports**: Always include necessary import statements
3. **Untested Edge Cases**: Consider error conditions in testing
4. **Scope Creep**: Keep phases focused, create new phases for new issues
5. **Skipping Verification**: Always run the success criteria checks

## Questions or Improvements?

This process is designed to evolve. If you identify improvements:
1. Create an ADR proposing the change
2. Update this CLAUDE.md file
3. Apply the new process to future phases

Remember: The goal is sustainable, incremental progress with high confidence in each change.