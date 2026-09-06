from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

old_ui = '''        <div class="settingField">\n          <label for="jumpInput">Nejmenší skok mezi běžnými jednotkami</label>\n          <input id="jumpInput" type="number" min="1" max="8" step="1">\n        </div>'''
new_ui = '''        <div class="settingField">\n          <label for="jumpInput">Preferovaný minimální rozdíl velikosti jednotek</label>\n          <select id="jumpInput">\n            <option value="1">1 řád (alespoň 10×)</option>\n            <option value="2">2 řády (alespoň 100×)</option>\n            <option value="3">3 řády (alespoň 1 000×)</option>\n            <option value="4">4 řády (alespoň 10 000×)</option>\n            <option value="5">5 řádů (alespoň 100 000×)</option>\n            <option value="6">6 řádů (alespoň 1 000 000×)</option>\n          </select>\n          <span class="small">Počítá se podle převodního poměru, ne podle počtu sousedních předpon. Např. 2 řády znamenají rozdíl alespoň 100×. Pokud taková dvojice u dané veličiny neexistuje, použije se nejvzdálenější dostupná.</span>\n        </div>'''
if old_ui not in text:
    raise SystemExit('unit-gap UI block not found')
text = text.replace(old_ui, new_ui, 1)

old_choose = '''function chooseUnitPair(units){\n  if(units.length < 2) return null;\n  let best = null;\n  const compoundMode = compoundConversionMode();\n  for(let i=0; i<600; i++){\n    const from = randomChoice(units);\n    const to = randomChoice(units);\n    if(from.unit === to.unit) continue;\n    if(Math.abs(from.factor - to.factor) <= Math.max(Math.abs(from.factor), Math.abs(to.factor), 1) * 1e-15) continue;\n\n    const diffCount = compoundDifferenceCount(from, to);\n    if(compoundMode && diffCount !== null){\n      if(compoundMode === 'one' && diffCount !== 1) continue;\n      if(compoundMode === 'both' && diffCount !== 2) continue;\n    }\n\n    const jump = Math.abs((from.order ?? Math.log10(from.factor)) - (to.order ?? Math.log10(to.factor)));\n    if(jump < settings.minJump && units.length > 2) {\n      best = best || {from, to};\n      continue;\n    }\n    return {from, to};\n  }\n  return best;\n}'''
new_choose = '''function chooseUnitPair(units){\n  if(units.length < 2) return null;\n  const compoundMode = compoundConversionMode();\n  const candidates = [];\n\n  for(let i=0; i<units.length; i++){\n    for(let j=0; j<units.length; j++){\n      if(i === j) continue;\n      const from = units[i];\n      const to = units[j];\n      if(from.unit === to.unit) continue;\n      if(Math.abs(from.factor - to.factor) <= Math.max(Math.abs(from.factor), Math.abs(to.factor), 1) * 1e-15) continue;\n\n      const diffCount = compoundDifferenceCount(from, to);\n      if(compoundMode && diffCount !== null){\n        if(compoundMode === 'one' && diffCount !== 1) continue;\n        if(compoundMode === 'both' && diffCount !== 2) continue;\n      }\n\n      const jump = Math.abs((from.order ?? Math.log10(Math.abs(from.factor))) - (to.order ?? Math.log10(Math.abs(to.factor))));\n      candidates.push({from, to, jump});\n    }\n  }\n\n  if(!candidates.length) return null;\n  const minJump = clampInt(settings.minJump, 1, 6);\n  const preferred = candidates.filter(pair => pair.jump + 1e-12 >= minJump);\n  const pool = preferred.length\n    ? preferred\n    : (() => {\n        const maxJump = Math.max(...candidates.map(pair => pair.jump));\n        return candidates.filter(pair => Math.abs(pair.jump - maxJump) <= 1e-12);\n      })();\n  const chosen = randomChoice(pool);\n  return chosen ? {from:chosen.from, to:chosen.to} : null;\n}'''
if old_choose not in text:
    raise SystemExit('chooseUnitPair block not found')
text = text.replace(old_choose, new_choose, 1)

old_apply = "  settings.minJump = clampInt($('jumpInput').value, 1, 8);"
new_apply = "  settings.minJump = clampInt($('jumpInput').value, 1, 6);"
if old_apply not in text:
    raise SystemExit('minJump apply line not found')
text = text.replace(old_apply, new_apply, 1)

old_summary = '''    <span class="pill">${qCount} veličin</span>\n    <span class="pill">${ensureAllQuantitiesForMode() ? 'všechny vybrané veličiny v sadě' : 'veličiny náhodně'}</span>'''
new_summary = '''    <span class="pill">${qCount} veličin</span>\n    <span class="pill">preferovaný odstup jednotek: ≥ ${formatPlainNumber(Math.pow(10, settings.minJump))}×</span>\n    <span class="pill">${ensureAllQuantitiesForMode() ? 'všechny vybrané veličiny v sadě' : 'veličiny náhodně'}</span>'''
if old_summary not in text:
    raise SystemExit('summary insertion point not found')
text = text.replace(old_summary, new_summary, 1)

html_path.write_text(text, encoding='utf-8')

# Tests
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')

old_api = "  physicalValueFitsProfile,\n  compoundDifferenceCount\n};"
new_api = "  physicalValueFitsProfile,\n  compoundDifferenceCount,\n  chooseUnitPair\n};"
if old_api not in test:
    raise SystemExit('test API insertion point not found')
test = test.replace(old_api, new_api, 1)

marker = "let generated = 0;\n"
addition = r'''// Ovladač odstupu znamená řády převodního poměru: 2 = alespoň 100×, ne dvě sousední předpony.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 2;
  cfg.compoundConversionByMode.ss = 'both';
  api.setSettings(cfg);
  const synthetic = [
    {unit:'u0', factor:1, order:0, parts:null},
    {unit:'u1', factor:10, order:1, parts:null},
    {unit:'u2', factor:100, order:2, parts:null},
    {unit:'u3', factor:1000, order:3, parts:null}
  ];
  for(let i=0; i<100; i++){
    const pair = api.chooseUnitPair(synthetic);
    assert(pair, 'Nelze vybrat kontrolní dvojici jednotek.');
    const ratio = Math.max(pair.from.factor, pair.to.factor) / Math.min(pair.from.factor, pair.to.factor);
    assert(ratio >= 100 - 1e-12, `Při minJump=2 musí být preferovaná dvojice alespoň 100× od sebe, ale je ${ratio}×.`);
  }
}

// Když požadovaný odstup v nabídce neexistuje, musí se použít opravdu nejvzdálenější dostupná dvojice.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 6;
  api.setSettings(cfg);
  const synthetic = [
    {unit:'u0', factor:1, order:0, parts:null},
    {unit:'u1', factor:10, order:1, parts:null},
    {unit:'u2', factor:100, order:2, parts:null}
  ];
  for(let i=0; i<50; i++){
    const pair = api.chooseUnitPair(synthetic);
    const ratio = Math.max(pair.from.factor, pair.to.factor) / Math.min(pair.from.factor, pair.to.factor);
    assert.equal(ratio, 100, 'Fallback má použít nejvzdálenější dostupnou dvojici.');
  }
}

let generated = 0;
'''
if marker not in test:
    raise SystemExit('generated marker not found')
test = test.replace(marker, addition, 1)

test_path.write_text(test, encoding='utf-8')
