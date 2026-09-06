from pathlib import Path

html_path = Path('prevody.html')
test_path = Path('tests/prevody.test.mjs')
text = html_path.read_text(encoding='utf-8')
test = test_path.read_text(encoding='utf-8')

# UI styles for a quantity row with its SŠ exponential checkbox.
old = ".checks{display:grid;grid-template-columns:1fr 1fr;gap:7px 10px}\n.check,.prefixCheck{display:flex;align-items:center;gap:8px;background:white;border:1px solid var(--line);border-radius:8px;padding:8px;line-height:1.2}\n.check input,.prefixCheck input{accent-color:var(--accent2);margin:0;flex:0 0 auto}"
new = ".checks{display:grid;grid-template-columns:1fr 1fr;gap:7px 10px}\n.quantityRow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;align-items:stretch}\n.quantityRow>.check{min-width:0}\n.expCheck{display:flex;align-items:center;gap:5px;background:#f8fffc;border:1px solid #aee1d1;border-radius:8px;padding:8px;font-size:12px;font-weight:700;white-space:nowrap}\n.expCheck input{accent-color:var(--accent2);margin:0}\n.expCheck.disabled{opacity:.42;background:#f4f4f4;border-color:#ddd}\n.check,.prefixCheck{display:flex;align-items:center;gap:8px;background:white;border:1px solid var(--line);border-radius:8px;padding:8px;line-height:1.2}\n.check input,.prefixCheck input{accent-color:var(--accent2);margin:0;flex:0 0 auto}"
if old not in text: raise SystemExit('CSS anchor not found')
text = text.replace(old, new, 1)

# SŠ mode description is no longer globally exponential.
text = text.replace("{id:'ss', name:'2) Převody pro SŠ', note:'výsledek povinně v exponenciálním tvaru'}", "{id:'ss', name:'2) Převody pro SŠ', note:'exponenciální tvar podle zvolené veličiny'}", 1)

# Default exponential quantities: only length, mass, force and ordinary energy.
old = "  ensureAllQuantitiesByMode:{zs:true, ss:true},\n  prefixes:['n','µ','m','c','d','','da','h','k','M','G'],"
new = "  ensureAllQuantitiesByMode:{zs:true, ss:true},\n  exponentialQuantitiesByMode:{ss:['delka','hmotnost','sila','energie']},\n  prefixes:['n','µ','m','c','d','','da','h','k','M','G'],"
if old not in text: raise SystemExit('default exp anchor not found')
text = text.replace(old, new, 1)

# Helper that centralizes the per-quantity exponential decision.
old = "function availableQuantities(){\n  return quantityMeta.filter(q => q.modes.includes(settings.mode));\n}"
new = "function exponentialQuantitiesForMode(mode = settings.mode){\n  if(!settings.exponentialQuantitiesByMode) settings.exponentialQuantitiesByMode = structuredClone(defaultSettings.exponentialQuantitiesByMode);\n  if(!Array.isArray(settings.exponentialQuantitiesByMode[mode])){\n    settings.exponentialQuantitiesByMode[mode] = structuredClone(defaultSettings.exponentialQuantitiesByMode[mode] || []);\n  }\n  return settings.exponentialQuantitiesByMode[mode];\n}\n\nfunction usesExponentialForQuantity(quantityId, mode = settings.mode){\n  return mode === 'ss' && exponentialQuantitiesForMode(mode).includes(quantityId);\n}\n\nfunction availableQuantities(){\n  return quantityMeta.filter(q => q.modes.includes(settings.mode));\n}"
if old not in text: raise SystemExit('helper anchor not found')
text = text.replace(old, new, 1)

# Remove the old 50/50 random SŠ slots. Each quantity now decides its own format.
old = "  let cycle = shuffle(quantities);\n  let previousId = null;\n  const expInputSlots = new Set();\n  if(settings.mode === 'ss'){\n    const target = Math.round(count / 2);\n    const slots = shuffle(Array.from({length:count}, (_, i) => i + 1));\n    slots.slice(0, target).forEach(i => expInputSlots.add(i));\n  }\n  examples = [];"
new = "  let cycle = shuffle(quantities);\n  let previousId = null;\n  examples = [];"
if old not in text: raise SystemExit('exp slots anchor not found')
text = text.replace(old, new, 1)

old = "    const preferred = cycle.shift();\n    const ex = makeExample(i, preferred, expInputSlots.has(i));"
new = "    const preferred = cycle.shift();\n    const useExponential = Boolean(preferred && usesExponentialForQuantity(preferred.id));\n    const ex = makeExample(i, preferred, useExponential);"
if old not in text: raise SystemExit('generate useExp anchor not found')
text = text.replace(old, new, 1)

# Store the requested result format explicitly in the generated example.
old = "      value:x.visible,\n      exponentialInput:x.exponential,\n      from:pair.from.unit,"
new = "      value:x.visible,\n      exponentialInput:x.exponential,\n      exponentialFormat:Boolean(useExponentialInput),\n      from:pair.from.unit,"
if old not in text: raise SystemExit('example format anchor not found')
text = text.replace(old, new, 1)

# Results on SŠ follow the same per-quantity checkbox as the assignment.
old = "    const resultText = settings.mode === 'ss' ? ex.resultExp : ex.resultPlain;"
new = "    const resultText = settings.mode === 'ss' && ex.exponentialFormat ? ex.resultExp : ex.resultPlain;"
if old not in text: raise SystemExit('render result anchor not found')
text = text.replace(old, new, 1)

# Summary and status describe the mixed SŠ mode accurately.
old = "  const resultLimits = resultLimitsForMode();\n  $('summary').innerHTML = `"
new = "  const resultLimits = resultLimitsForMode();\n  const expCount = settings.mode === 'ss' ? selectedQuantities().filter(q => usesExponentialForQuantity(q.id)).length : 0;\n  $('summary').innerHTML = `"
if old not in text: raise SystemExit('summary exp count anchor not found')
text = text.replace(old, new, 1)
text = text.replace("    <span class=\"pill\">${settings.mode === 'ss' ? 'exp. tvar' : 'bez exp. tvaru'}</span>", "    <span class=\"pill\">${settings.mode === 'ss' ? `exp. tvar: ${expCount} veličin` : 'bez exp. tvaru'}</span>", 1)
text = text.replace("    : 'SŠ režim: po zobrazení výsledků je hlavní výsledek v exponenciálním tvaru.';", "    : 'SŠ režim: exponenciální tvar zadání i výsledku se nastavuje samostatně u každé veličiny.';", 1)

# SŠ quantity list gets an exp. checkbox; ZŠ stays unchanged.
old = "  const selectedQ = new Set(settings.quantitiesByMode[settings.mode] || []);\n  $('quantityChecks').innerHTML = availableQuantities().map(q => `\n    <label class=\"check\">\n      <input type=\"checkbox\" value=\"${q.id}\" ${selectedQ.has(q.id) ? 'checked' : ''}>\n      <span>${q.title}</span>\n    </label>\n  `).join('');"
new = "  const selectedQ = new Set(settings.quantitiesByMode[settings.mode] || []);\n  const selectedExp = new Set(exponentialQuantitiesForMode());\n  $('quantityChecks').innerHTML = availableQuantities().map(q => {\n    const checked = selectedQ.has(q.id);\n    if(settings.mode !== 'ss'){\n      return `\n        <label class=\"check\">\n          <input type=\"checkbox\" data-role=\"quantity\" value=\"${q.id}\" ${checked ? 'checked' : ''}>\n          <span>${q.title}</span>\n        </label>`;\n    }\n    return `\n      <div class=\"quantityRow\">\n        <label class=\"check\">\n          <input type=\"checkbox\" data-role=\"quantity\" value=\"${q.id}\" ${checked ? 'checked' : ''}>\n          <span>${q.title}</span>\n        </label>\n        <label class=\"expCheck ${checked ? '' : 'disabled'}\" title=\"Exponenciální tvar v zadání i výsledku\">\n          <input type=\"checkbox\" data-role=\"exp\" data-qid=\"${q.id}\" ${selectedExp.has(q.id) ? 'checked' : ''} ${checked ? '' : 'disabled'}>\n          <span>exp.</span>\n        </label>\n      </div>`;\n  }).join('');\n\n  if(settings.mode === 'ss'){\n    $('quantityChecks').querySelectorAll('input[data-role=\"quantity\"]').forEach(input => {\n      input.addEventListener('change', () => {\n        const exp = $('quantityChecks').querySelector(`input[data-role=\"exp\"][data-qid=\"${input.value}\"]`);\n        if(!exp) return;\n        exp.disabled = !input.checked;\n        exp.closest('.expCheck')?.classList.toggle('disabled', !input.checked);\n      });\n    });\n  }"
if old not in text: raise SystemExit('quantity UI anchor not found')
text = text.replace(old, new, 1)

# Save quantity and exp settings separately; disabled exp preferences are preserved.
old = "  const quantities = [...$('quantityChecks').querySelectorAll('input:checked')].map(i => i.value);\n  settings.quantitiesByMode[settings.mode] = quantities;"
new = "  const quantities = [...$('quantityChecks').querySelectorAll('input[data-role=\"quantity\"]:checked')].map(i => i.value);\n  settings.quantitiesByMode[settings.mode] = quantities;\n  if(settings.mode === 'ss'){\n    settings.exponentialQuantitiesByMode.ss = [...$('quantityChecks').querySelectorAll('input[data-role=\"exp\"]:checked')].map(i => i.dataset.qid);\n  }"
if old not in text: raise SystemExit('apply quantities anchor not found')
text = text.replace(old, new, 1)

# Copying answers follows the same result representation shown on screen.
old = "    if(settings.mode === 'ss') return `${ex.value} ${ex.from} =\\t${ex.resultExp} ${ex.to}`;\n    return `${ex.value} ${ex.from} =\\t${ex.resultPlain} ${ex.to}`;"
new = "    if(settings.mode === 'ss' && ex.exponentialFormat) return `${ex.value} ${ex.from} =\\t${ex.resultExp} ${ex.to}`;\n    return `${ex.value} ${ex.from} =\\t${ex.resultPlain} ${ex.to}`;"
if old not in text: raise SystemExit('copy answer anchor not found')
text = text.replace(old, new, 1)

# Expose helper to regression tests.
old = "  resultFitsLimits\n};`;"
new = "  resultFitsLimits,\n  usesExponentialForQuantity\n};`;"
if old not in test: raise SystemExit('test API anchor not found')
test = test.replace(old, new, 1)

# Check exact SŠ defaults and per-quantity behavior.
anchor = "assert.equal(JSON.stringify(defaults.quantitiesByMode.ss), JSON.stringify(expectedDefaults), 'Výchozí SŠ veličiny se změnily.');\n"
addition = "assert.equal(JSON.stringify(defaults.exponentialQuantitiesByMode.ss), JSON.stringify(['delka','hmotnost','sila','energie']), 'Výchozí SŠ exp. veličiny se změnily.');\n"
if anchor not in test: raise SystemExit('default test anchor not found')
test = test.replace(anchor, anchor + addition, 1)

anchor = "let generated = 0;\n"
addition = "\n{\n  const cfg = structuredClone(defaults);\n  cfg.mode = 'ss';\n  api.setSettings(cfg);\n  for(const q of api.quantityMeta.filter(item => item.modes.includes('ss'))){\n    const shouldExp = ['delka','hmotnost','sila','energie'].includes(q.id);\n    assert.equal(api.usesExponentialForQuantity(q.id), shouldExp, `Chybné výchozí exp. nastavení pro ${q.id}.`);\n    const ex = api.makeExample(1, q, shouldExp);\n    assert(ex, `Nelze vytvořit kontrolní SŠ příklad pro ${q.id}.`);\n    assert.equal(ex.exponentialFormat, shouldExp, `Výsledek ${q.id} nemá správný exp. režim.`);\n    assert.equal(ex.exponentialInput, shouldExp, `Zadání ${q.id} nemá správný exp. režim.`);\n  }\n}\n\n"
if anchor not in test: raise SystemExit('generated test anchor not found')
test = test.replace(anchor, addition + anchor, 1)

test = test.replace(
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, min/max jen pro běžná zadání, exp. rozsah 10^-10 až 10^10, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');",
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách (default Délka/Hmotnost/Síla/Energie), min/max jen pro běžná zadání, exp. rozsah 10^-10 až 10^10, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');"
)

html_path.write_text(text, encoding='utf-8')
test_path.write_text(test, encoding='utf-8')
