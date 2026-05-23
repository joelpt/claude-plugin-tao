# tao plugin — development recipes

# Validate all Python scripts parse without errors
test:
    python3 -m py_compile scripts/llm_call.py
    python3 -m py_compile scripts/models.py
    python3 -c "import json; json.load(open('config/models.json'))"
    python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
    @echo "All checks passed."

# Smoke test: call llm_call.py with --help (no API needed)
smoke:
    python3 scripts/llm_call.py --help

# Show current plugin version
version:
    @python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])"

# Validate all command and agent markdown files have frontmatter
lint:
    #!/usr/bin/env python3
    import os, sys
    errors = []
    for d in ("commands", "agents"):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".md"):
                continue
            path = os.path.join(d, f)
            content = open(path).read()
            if not content.startswith("---"):
                errors.append(f"{path}: missing frontmatter")
            if not content.endswith("\n"):
                errors.append(f"{path}: missing trailing newline")
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(os.listdir('commands')) + len(os.listdir('agents'))} files checked.")
