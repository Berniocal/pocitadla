from pathlib import Path

p = Path('prevody.html')
text = p.read_text(encoding='utf-8')

repls = {
    '.settingField input{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}': '.settingField > input{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}\n.settingField .check input{width:auto}',
    'ss:{minNumber:0.01, maxNumber:9999, niceInputByUnitSize:false}': 'ss:{minNumber:0.01, maxNumber:9999, niceInputByUnitSize:true}',
    'ss:{enabled:false, maxIntegerDigits:7, maxDecimals:6}': 'ss:{enabled:true, maxIntegerDigits:7, maxDecimals:6}',
}

for old, new in repls.items():
    if old not in text:
        raise SystemExit(f'Expected text not found: {old}')
    text = text.replace(old, new, 1)

p.write_text(text, encoding='utf-8')
