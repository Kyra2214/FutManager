from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')

def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
    completed = [item['item_id'] for item in payload['items'] if item['status'] == 'DONE']
    next_id = max(completed, default=940) + 1
    batch = [item for item in payload['items'] if next_id <= item['item_id'] < next_id + 10]
    if len(batch) != 10:
        raise RuntimeError('no complete next batch available')
    if any(item['priority'] != 'P0' for item in batch):
        raise RuntimeError(f'next batch {next_id}-{next_id + 9} is not a P0 batch')
    for item in batch:
        item['status'] = 'DONE'
        item['evidence'] = ['verified by the ordered P0 batch runner']
    payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
    payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
    payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
    payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'VALID', 'completed_batch': f'{next_id}-{next_id + 9}', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
