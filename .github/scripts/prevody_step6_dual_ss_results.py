from pathlib import Path

html_path = Path('prevody.html')
test_path = Path('tests/prevody.test.mjs')
text = html_path.read_text(encoding='utf-8')
test = test_path.read_text(encoding='utf-8')

# Add light styling for two SŠ result forms.
old = '''.task{font-size:22px;font-weight:780;line-height:1.3}\n.unit{white-space:nowrap}\n.answer{display:none;background:#fffdf9;border:1px dashed var(--line);border-radius:8px;padding:10px 12px;font-size:19px}'''
new = '''.task{font-size:22px;font-weight:780;line-height:1.3}\n.unit{white-space:nowrap}\n.ssResults{display:inline-flex;flex-direction:column;gap:2px;vertical-align:middle;margin-left:4px}\n.ssResultLine{display:inline-flex;align-items:baseline;gap:6px}\n.ssResultLabel{font-size:12px;font-weight:650;color:var(--muted);min-width:44px}\n.answer{display:none;background:#fffdf9;border:1px dashed var(--line);border-radius:8px;padding:10px 12px;font-size:19px}'''
if old not in text:
    raise SystemExit('CSS anchor not found')
text = text.replace(old, new, 1)

# Checkbox now controls only assignment formatting; SŠ answers always show both forms.
text = text.replace(
    'title="Exponenciální tvar v zadání i výsledku"',
    'title="Exponenciální tvar v zadání"'
)

# Add one helper so render/copy share the exact same result logic.
anchor = '''function renderExamples(){\n  const failureNames = [...new Set(generationFailures)];'''
insert = '''function resultTextsForExample(ex, mode = settings.mode){\n  if(mode === 'ss'){\n    return {plain:ex.resultPlain, exponential:ex.resultExp};\n  }\n  return {plain:ex.resultPlain, exponential:null};\n}\n\nfunction renderExamples(){\n  const failureNames = [...new Set(generationFailures)];'''
if anchor not in text:
    raise SystemExit('renderExamples anchor not found')
text = text.replace(anchor, insert, 1)

old = '''  $('examples').innerHTML = warningHtml + examples.map(ex => {\n    const resultText = settings.mode === 'ss' && ex.exponentialFormat ? ex.resultExp : ex.resultPlain;\n    const taskResult = answersVisible\n      ? `${resultText} <span class="unit">${ex.to}</span>`\n      : `<span class="unit">${ex.to}</span>`;\n    return `'''
new = '''  $('examples').innerHTML = warningHtml + examples.map(ex => {\n    const resultTexts = resultTextsForExample(ex);\n    const taskResult = answersVisible\n      ? (settings.mode === 'ss'\n          ? `<span class="ssResults"><span class="ssResultLine"><span class="ssResultLabel">běžně:</span><span>${resultTexts.plain} <span class="unit">${ex.to}</span></span></span><span class="ssResultLine"><span class="ssResultLabel">exp.:</span><span>${resultTexts.exponential} <span class="unit">${ex.to}</span></span></span></span>`\n          : `${resultTexts.plain} <span class="unit">${ex.to}</span>`)\n      : `<span class="unit">${ex.to}</span>`;\n    return `'''
if old not in text:
    raise SystemExit('render result anchor not found')
text = text.replace(old, new, 1)

text = text.replace(
    ": 'SŠ režim: exponenciální tvar zadání i výsledku se nastavuje samostatně u každé veličiny. V zadání je při převodu z menší jednotky na větší exponent kladný, opačným směrem záporný.';",
    ": 'SŠ režim: exponenciální tvar zadání se nastavuje samostatně u každé veličiny. Výsledek se vždy zobrazí dvakrát – běžně i v exponenciálním tvaru. V zadání je při převodu z menší jednotky na větší exponent kladný, opačným směrem záporný.';"
)

old = '''function copyText(kind){\n  const lines = examples.map(ex => {\n    if(kind === 'tasks') return `${ex.value} ${ex.from} =\\t${ex.to}`;\n    if(settings.mode === 'ss' && ex.exponentialFormat) return `${ex.value} ${ex.from} =\\t${ex.resultExp} ${ex.to}`;\n    return `${ex.value} ${ex.from} =\\t${ex.resultPlain} ${ex.to}`;\n  }).join('\\n');'''
new = '''function copyText(kind){\n  const lines = examples.map(ex => {\n    if(kind === 'tasks') return `${ex.value} ${ex.from} =\\t${ex.to}`;\n    const resultTexts = resultTextsForExample(ex);\n    if(settings.mode === 'ss') return `${ex.value} ${ex.from} =\\t${resultTexts.plain} ${ex.to}\\t${resultTexts.exponential} ${ex.to}`;\n    return `${ex.value} ${ex.from} =\\t${resultTexts.plain} ${ex.to}`;\n  }).join('\\n');'''
if old not in text:
    raise SystemExit('copyText anchor not found')
text = text.replace(old, new, 1)

# Expose helper and assert that SŠ always yields both forms, irrespective of exp input setting.
old = '''  formatExponentialText,\n  numberRange\n};`;'''
new = '''  formatExponentialText,\n  numberRange,\n  resultTextsForExample\n};`;'''
if old not in test:
    raise SystemExit('test API anchor not found')
test = test.replace(old, new, 1)

anchor = '''const expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];'''
insert = '''const dualResultProbe = {resultPlain:'12 000', resultExp:'1,2·10⁴'};\nassert.deepEqual(\n  JSON.parse(JSON.stringify(api.resultTextsForExample(dualResultProbe, 'ss'))),\n  {plain:'12 000', exponential:'1,2·10⁴'},\n  'Na SŠ musí být dostupný běžný i exponenciální výsledek.'\n);\nassert.deepEqual(\n  JSON.parse(JSON.stringify(api.resultTextsForExample(dualResultProbe, 'zs'))),\n  {plain:'12 000', exponential:null},\n  'Na ZŠ se má zobrazovat jen běžný výsledek.'\n);\n\nconst expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];'''
if anchor not in test:
    raise SystemExit('expectedDefaults anchor not found')
test = test.replace(anchor, insert, 1)

test = test.replace(
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách, znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');",
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');"
)

html_path.write_text(text, encoding='utf-8')
test_path.write_text(test, encoding='utf-8')
