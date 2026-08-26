from __future__ import annotations

import ast
import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PACKAGE = ENGINE / 'engine'

modules: dict[str, set[str]] = {}
for path in PACKAGE.rglob('*.py'):
    module = '.'.join(path.relative_to(ENGINE).with_suffix('').parts)
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError as exc:
        raise SystemExit(f'SYNTAX_ERROR:{path}:{exc.lineno}')
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module if node.level == 0 else module.rsplit('.', node.level)[0] + '.' + node.module)
    modules[module] = {name for name in imports if name == 'engine' or name.startswith('engine.')}

cycles: list[list[str]] = []
stack: list[str] = []
active: set[str] = set()
seen: set[tuple[str, ...]] = set()

def visit(node: str) -> None:
    if node in active:
        start = stack.index(node)
        cycle = stack[start:] + [node]
        key = min(tuple(cycle[i:] + cycle[:i]) for i in range(len(cycle)))
        if key not in seen:
            seen.add(key)
            cycles.append(cycle)
        return
    if node in {item for item in stack}:
        return
    active.add(node)
    stack.append(node)
    for dependency in sorted(modules.get(node, ())):
        if dependency in modules:
            visit(dependency)
    stack.pop()
    active.remove(node)

for module in sorted(modules):
    visit(module)

report = {
    'root': str(PACKAGE),
    'modules': len(modules),
    'internal_edges': sum(len(deps & modules.keys()) for deps in modules.values()),
    'cycles': cycles,
    'status': 'VALID' if not cycles else 'CYCLES_FOUND',
}
output = ENGINE / 'docs' / 'engine_dependency_cycles.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(report)
if cycles:
    raise SystemExit(1)
