from pathlib import Path
import javaobj.v2 as javaobj

for code in ('BRA', 'ITA', 'ESP', 'POR'):
    path = Path('/tmp/fut_cfg') / f'{code}.cfg'
    print(f'--- {code} ---')
    if not path.exists():
        print('missing')
        continue
    try:
        with path.open('rb') as stream:
            value = javaobj.load(stream)
        print(type(value).__name__)
        for classdesc, fields in value.field_data.items():
            print('class=', classdesc)
            for field, field_value in fields.items():
                field_name = getattr(field, 'name', None) or getattr(field, 'field_name', None) or str(getattr(field, '__dict__', field))
                if isinstance(field_value, list):
                    for item in field_value:
                        if hasattr(item, 'field_data'):
                            flat = {}
                            for item_class, item_fields in item.field_data.items():
                                for item_field, item_value in item_fields.items():
                                    item_name = getattr(item_field, 'name', None) or getattr(item_field, 'field_name', None) or str(getattr(item_field, '__dict__', item_field))
                                    flat[item_name] = item_value
                            print('division=', flat.get('divisao'), 'country=', flat.get('pais'), 'name=', flat.get('nomeDivisao'), 'teams=', flat.get('nTimes'), 'valid=', flat.get('valido'))
                        else:
                            print('item=', repr(item))
                else:
                    print('field=', field_name, 'value=', repr(field_value))
    except Exception as exc:
        print(type(exc).__name__, str(exc))
