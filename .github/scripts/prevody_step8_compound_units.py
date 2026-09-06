from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

repls = [
    (
        ".settingField > input{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}",
        ".settingField > input,.settingField > select{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}"
    ),
    (
        "  minJump:2,\n  resultLimitsByMode:{",
        "  minJump:2,\n  compoundUnitChangeByMode:{ss:'both'},\n  resultLimitsByMode:{"
    ),
    (
        '''        <div class="settingField">\n          <label for="jumpInput">Nejmenší skok mezi běžnými jednotkami</label>\n          <input id="jumpInput" type="number" min="1" max="8" step="1">\n        </div>''',
        '''        <div class="settingField">\n          <label for="jumpInput">Nejmenší skok mezi běžnými jednotkami</label>\n          <input id="jumpInput" type="number" min="1" max="8" step="1">\n        </div>\n        <div class="settingField" id="compoundUnitChangeField">\n          <label for="compoundUnitChangeInput">U složených jednotek na SŠ měnit</label>\n          <select id="compoundUnitChangeInput">\n            <option value="both">obě části jednotky</option>\n            <option value="one">jen jednu část jednotky</option>\n          </select>\n        </div>'''
    ),
]

for old, new in repls:
    if old not in text:
        raise SystemExit(f'Expected text not found: {old[:120]}')
    text = text.replace(old, new, 1)

old_choose = '''function chooseUnitPair(units){\n  if(units.length < 2) return null;\n  let best = null;\n  for(let i=0; i<400; i++){\n    const from = randomChoice(units);\n    const to = randomChoice(units);\n    if(from.unit === to.unit) continue;\n    const jump = Math.abs((from.order ?? Math.log10(from.factor)) - (to.order ?? Math.log10(to.factor)));\n    if(jump < settings.minJump && units.length > 2) {\n      best = best || {from, to};\n      continue;\n    }\n    return {from, to};\n  }\n  return best || {from:units[0], to:units[units.length - 1]};\n}'''

new_choose = '''function compoundUnitChangeModeForMode(mode = settings.mode){\n  if(!settings.compoundUnitChangeByMode) settings.compoundUnitChangeByMode = structuredClone(defaultSettings.compoundUnitChangeByMode);\n  const value = settings.compoundUnitChangeByMode[mode];\n  return value === 'one' ? 'one' : 'both';\n}\n\nfunction compoundUnitParts(unitName){\n  const parts = String(unitName).split('/');\n  if(parts.length !== 2 || !parts[0] || !parts[1]) return null;\n  return {first:parts[0], second:parts[1]};\n}\n\nfunction compoundUnitChangeCount(fromName, toName){\n  const from = compoundUnitParts(fromName);\n  const to = compoundUnitParts(toName);\n  if(!from || !to) return null;\n  return Number(from.first !== to.first) + Number(from.second !== to.second);\n}\n\nfunction chooseUnitPair(units){\n  if(units.length < 2) return null;\n\n  let pairs = [];\n  for(let i=0; i<units.length; i++){\n    for(let j=0; j<units.length; j++){\n      if(i === j || units[i].unit === units[j].unit) continue;\n      const from = units[i];\n      const to = units[j];\n      const jump = Math.abs((from.order ?? Math.log10(from.factor)) - (to.order ?? Math.log10(to.factor)));\n      pairs.push({from, to, jump, compoundChanges:compoundUnitChangeCount(from.unit, to.unit)});\n    }\n  }\n  if(!pairs.length) return null;\n\n  if(settings.mode === 'ss'){\n    const availableChangeCounts = new Set(pairs.map(pair => pair.compoundChanges).filter(value => value === 1 || value === 2));\n    // Omezení používáme jen tam, kde daná veličina skutečně nabízí obě smysluplné varianty.\n    // Např. rychlost a hustota ano; zrychlení má v nabídce proměnnou jen první část, takže se tímto přepínačem neblokuje.\n    if(availableChangeCounts.has(1) && availableChangeCounts.has(2)){\n      const wantedChanges = compoundUnitChangeModeForMode() === 'one' ? 1 : 2;\n      pairs = pairs.filter(pair => pair.compoundChanges === wantedChanges);\n    }\n  }\n\n  if(!pairs.length) return null;\n  const preferred = pairs.filter(pair => pair.jump >= settings.minJump || units.length <= 2);\n  const pool = preferred.length ? preferred : pairs;\n  const chosen = randomChoice(pool);\n  return {from:chosen.from, to:chosen.to};\n}'''

if old_choose not in text:
    raise SystemExit('chooseUnitPair block not found')
text = text.replace(old_choose, new_choose, 1)

old_fill = "  $('jumpInput').value = settings.minJump;\n  $('resultLimitEnabledInput').checked = Boolean(resultLimits.enabled);"
new_fill = "  $('jumpInput').value = settings.minJump;\n  $('compoundUnitChangeInput').value = compoundUnitChangeModeForMode();\n  $('compoundUnitChangeField').style.display = settings.mode === 'ss' ? '' : 'none';\n  $('resultLimitEnabledInput').checked = Boolean(resultLimits.enabled);"
if old_fill not in text:
    raise SystemExit('fillSettingsForm insertion point not found')
text = text.replace(old_fill, new_fill, 1)

old_apply = "  settings.minJump = clampInt($('jumpInput').value, 1, 8);\n  const resultLimits = resultLimitsForMode();"
new_apply = "  settings.minJump = clampInt($('jumpInput').value, 1, 8);\n  if(settings.mode === 'ss'){\n    settings.compoundUnitChangeByMode.ss = $('compoundUnitChangeInput').value === 'one' ? 'one' : 'both';\n  }\n  const resultLimits = resultLimitsForMode();"
if old_apply not in text:
    raise SystemExit('applySettingsFromForm insertion point not found')
text = text.replace(old_apply, new_apply, 1)

old_summary = "    <span class=\"pill\">${settings.mode === 'ss' ? `exp. tvar: ${expCount} veličin` : 'bez exp. tvaru'}</span>\n    <span class=\"pill\">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>"
new_summary = "    <span class=\"pill\">${settings.mode === 'ss' ? `exp. tvar: ${expCount} veličin` : 'bez exp. tvaru'}</span>\n    ${settings.mode === 'ss' ? `<span class=\"pill\">složené jednotky: ${compoundUnitChangeModeForMode() === 'one' ? 'měnit jednu část' : 'měnit obě části'}</span>` : ''}\n    <span class=\"pill\">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>"
if old_summary not in text:
    raise SystemExit('renderSummary insertion point not found')
text = text.replace(old_summary, new_summary, 1)

html_path.write_text(text, encoding='utf-8')

# Extend stress tests.
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')

old_api = "  resultTextsForExample\n};"
new_api = "  resultTextsForExample,\n  compoundUnitChangeCount\n};"
if old_api not in test:
    raise SystemExit('test API insertion point not found')
test = test.replace(old_api, new_api, 1)

old_defaults = "assert.equal(JSON.stringify(defaults.exponentialQuantitiesByMode.ss), JSON.stringify(['delka','hmotnost','sila','energie']), 'Výchozí SŠ exp. veličiny se změnily.');"
new_defaults = old_defaults + "\nassert.equal(defaults.compoundUnitChangeByMode.ss, 'both', 'Výchozí SŠ složené jednotky mají měnit obě části.');"
if old_defaults not in test:
    raise SystemExit('default assertion insertion point not found')
test = test.replace(old_defaults, new_defaults, 1)

marker = "let generated = 0;\n"
addition = r'''// SŠ: u složených jednotek lze vynutit změnu obou částí nebo jen jedné.
for(const compoundMode of ['both','one']){
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.compoundUnitChangeByMode.ss = compoundMode;
  cfg.resultLimitsByMode.ss.enabled = false;
  cfg.minJump = 1;
  api.setSettings(cfg);

  for(const quantityId of ['rychlost','hustota']){
    const q = quantityById(quantityId);
    for(let i = 0; i < 200; i++){
      const ex = api.makeExample(i + 1, q, false);
      assert(ex, `Nepodařilo se vytvořit složenou jednotku ${quantityId} v režimu ${compoundMode}.`);
      const changed = api.compoundUnitChangeCount(ex.from, ex.to);
      assert.equal(changed, compoundMode === 'one' ? 1 : 2, `${quantityId}: ${ex.from} -> ${ex.to} neodpovídá režimu ${compoundMode}.`);
    }
  }
}

// Zrychlení má v současné nabídce proměnnou jen první část; volba "obě" ho proto nesmí zablokovat.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.compoundUnitChangeByMode.ss = 'both';
  cfg.resultLimitsByMode.ss.enabled = false;
  cfg.minJump = 1;
  api.setSettings(cfg);
  assert(api.makeExample(1, quantityById('zrychleni'), false), 'Volba obou částí nesmí zablokovat zrychlení, kde druhou část zatím neměníme.');
}

let generated = 0;
'''
if marker not in test:
    raise SystemExit('generated marker not found')
test = test.replace(marker, addition, 1)

test = test.replace(
    "Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.",
    "Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, volba změny jedné/obou částí složených jednotek, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií."
)

test_path.write_text(test, encoding='utf-8')
