from pathlib import Path
import re

hp = Path('prevody.html')
tp = Path('tests/prevody.test.mjs')
html = hp.read_text(encoding='utf-8')
test = tp.read_text(encoding='utf-8')

# 1) UI + style for SŠ compound-unit behavior.
html = html.replace(
    '.settingField > input{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}',
    '.settingField > input,.settingField > select{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px;background:white;color:var(--ink)}',
    1
)
needle = '''      <label class="check">\n        <input id="niceInputRuleInput" type="checkbox">\n        <span>Podle směru převodu volit hezčí zadání: z menší jednotky číslo větší než 10, z větší jednotky číslo menší než 1.</span>\n      </label>'''
insert = needle + '''\n      <div class="settingField" id="compoundConversionSetting" style="margin-top:12px">\n        <label for="compoundConversionInput">SŠ – u složených jednotek měnit</label>\n        <select id="compoundConversionInput">\n          <option value="both">obě části jednotky</option>\n          <option value="one">jen jednu část jednotky</option>\n        </select>\n        <span class="small">Platí pro veličiny jako rychlost, hustota a zrychlení. Např. m/s → km/h mění obě části, m/s → m/h jen jednu.</span>\n      </div>'''
if needle not in html:
    raise SystemExit('nice input UI anchor missing')
html = html.replace(needle, insert, 1)

# 2) Defaults.
needle = "  ensureAllQuantitiesByMode:{zs:true, ss:true},\n  exponentialQuantitiesByMode:{ss:['delka','hmotnost','sila','energie']},"
repl = "  ensureAllQuantitiesByMode:{zs:true, ss:true},\n  compoundConversionByMode:{ss:'both'},\n  exponentialQuantitiesByMode:{ss:['delka','hmotnost','sila','energie']},"
if needle not in html:
    raise SystemExit('defaults anchor missing')
html = html.replace(needle, repl, 1)

# 3) Unit metadata.
old = """function unit(unitName, factor, order, prefixId = null){\n  return {unit:unitName, factor, order, prefixId};\n}\n"""
new = """function unit(unitName, factor, order, prefixId = null, parts = null){\n  return {unit:unitName, factor, order, prefixId, parts};\n}\n\nfunction compoundUnit(unitName, factor, order, numerator, denominator, prefixId = null){\n  return unit(unitName, factor, order, prefixId, {numerator, denominator});\n}\n"""
if old not in html:
    raise SystemExit('unit helper missing')
html = html.replace(old, new, 1)

# 4) Speed only ordinary road/cycling physical values; units support one/both component changes without km/s.
html = re.sub(
    r"function buildSpeedUnits\(mode\)\{[\s\S]*?\n\}\n\nfunction buildDensityUnits",
    """function buildSpeedUnits(){\n  return filterUnits([\n    compoundUnit('m/s', 1, 0, 'm', 's', ''),\n    compoundUnit('km/h', 1 / 3.6, .55, 'km', 'h', 'k'),\n    compoundUnit('m/h', 1 / 3600, Math.log10(1 / 3600), 'm', 'h', '')\n  ]);\n}\n\nfunction buildDensityUnits""",
    html,
    count=1
)

# 5) Density component metadata.
html = re.sub(
    r"function buildDensityUnits\(mode\)\{[\s\S]*?\n\}\n\nfunction buildPressureUnits",
    """function buildDensityUnits(mode){\n  if(mode === 'zs'){\n    return filterUnits([\n      compoundUnit('kg/m³', 1, 0, 'kg', 'm³', 'k'),\n      compoundUnit('g/cm³', 1000, 3, 'g', 'cm³', 'c')\n    ]);\n  }\n  return filterUnits([\n    compoundUnit('kg/m³', 1, 0, 'kg', 'm³', 'k'),\n    compoundUnit('g/cm³', 1000, 3, 'g', 'cm³', 'c'),\n    compoundUnit('mg/mm³', 1000, 3.1, 'mg', 'mm³', 'm'),\n    compoundUnit('kg/dm³', 1000, 3.2, 'kg', 'dm³', 'd'),\n    compoundUnit('g/dm³', 1, .1, 'g', 'dm³', 'd'),\n    compoundUnit('kg/l', 1000, 3.3, 'kg', 'l', 'k'),\n    compoundUnit('g/l', 1, .2, 'g', 'l', null)\n  ]);\n}\n\nfunction buildPressureUnits""",
    html,
    count=1
)

# 6) Charge sensible units; acceleration component-aware.
old = "function buildChargeUnits(){\n  return prefixedUnits('C', ['f','p','n','µ','m','','k','M','G','T','P']);\n}"
new = "function buildChargeUnits(){\n  return prefixedUnits('C', ['p','n','µ','m','']);\n}"
if old not in html:
    raise SystemExit('charge builder missing')
html = html.replace(old, new, 1)
old = "function buildAccelerationUnits(){\n  return prefixedUnits('m/s²', ['n','µ','m','c','d','','k']);\n}"
new = """function buildAccelerationUnits(){\n  return filterUnits([\n    compoundUnit('mm/s²', 1e-3, -3, 'mm', 's²', 'm'),\n    compoundUnit('cm/s²', 1e-2, -2, 'cm', 's²', 'c'),\n    compoundUnit('m/s²', 1, 0, 'm', 's²', ''),\n    compoundUnit('km/s²', 1e3, 3, 'km', 's²', 'k'),\n    compoundUnit('m/min²', 1 / 3600, Math.log10(1 / 3600), 'm', 'min²', ''),\n    compoundUnit('km/min²', 1000 / 3600, Math.log10(1000 / 3600), 'km', 'min²', 'k')\n  ]);\n}"""
if old not in html:
    raise SystemExit('acceleration builder missing')
html = html.replace(old, new, 1)

# 7) Physical SI profiles for every quantity.
anchor = "function ensureAllQuantitiesForMode(mode = settings.mode){"
if anchor not in html:
    raise SystemExit('profile insertion anchor missing')
profiles = r'''const physicalProfiles = {
  delka:{zs:[{min:1e-3,max:1e4}],ss:[{min:1e-9,max:1e6}]},
  plocha:{zs:[{min:1e-4,max:1e6}],ss:[{min:1e-10,max:1e8}]},
  objem:{zs:[{min:1e-6,max:1e3}],ss:[{min:1e-12,max:1e5}]},
  hmotnost:{zs:[{min:1e-3,max:1e5}],ss:[{min:1e-9,max:1e6}]},
  sila:{zs:[{min:1e-1,max:1e5}],ss:[{min:1e-6,max:1e7}]},
  rychlost:{zs:[{min:3,max:45,scale:'linear'}],ss:[{min:3,max:45,scale:'linear'}]},
  hustota:{
    zs:[{min:.5,max:10,weight:.1},{min:500,max:1500,weight:.5,scale:'linear'},{min:1500,max:23000,weight:.4}],
    ss:[{min:.5,max:10,weight:.1},{min:500,max:1500,weight:.5,scale:'linear'},{min:1500,max:23000,weight:.4}]
  },
  tlak:{zs:[{min:1e3,max:5e6}],ss:[{min:1,max:1e9}]},
  energie:{zs:[{min:1e-3,max:1e9}],ss:[{min:1e-19,max:1e12}]},
  energieplus:{zs:[{min:1e-3,max:1e9}],ss:[{min:1e-19,max:1e12}]},
  napeti:{zs:[{min:.1,max:2e4}],ss:[{min:1e-6,max:1e6}]},
  cas:{zs:[{min:1e-3,max:1e6}],ss:[{min:1e-12,max:1e7}]},
  vykon:{zs:[{min:1,max:1e7}],ss:[{min:1e-6,max:1e9}]},
  proud:{zs:[{min:1e-3,max:100}],ss:[{min:1e-9,max:1e4}]},
  odpor:{zs:[{min:1,max:1e7}],ss:[{min:1e-3,max:1e9}]},
  zrychleni:{zs:[{min:.1,max:30,scale:'linear'}],ss:[{min:1e-3,max:1e3}]},
  frekvence:{zs:[{min:.1,max:2e4}],ss:[{min:1e-3,max:1e10}]},
  uhel:{zs:[{min:Math.PI/180,max:2*Math.PI,scale:'linear'}],ss:[{min:1e-6,max:2*Math.PI}]},
  naboj:{ss:[
    {min:1e-12,max:1e-9,weight:.1},
    {min:1e-9,max:1e-6,weight:.45},
    {min:1e-6,max:1e-3,weight:.4},
    {min:1e-3,max:1e-2,weight:.05}
  ]},
  kapacita:{ss:[{min:1e-12,max:1e-2}]},
  vodivost:{ss:[{min:1e-6,max:10}]},
  magindukce:{ss:[{min:1e-9,max:10}]},
  magnetickytok:{ss:[{min:1e-12,max:10}]},
  indukcnost:{ss:[{min:1e-9,max:10}]},
  latkovemnozstvi:{ss:[{min:1e-6,max:1e4}]}
};

function physicalProfileBands(quantityId, mode = settings.mode){
  const profile = physicalProfiles[quantityId];
  return profile ? (profile[mode] || profile.ss || profile.zs || []) : [];
}

function chooseWeightedBand(bands){
  if(!bands.length) return null;
  const total = bands.reduce((sum, band) => sum + (band.weight ?? 1), 0);
  let r = Math.random() * total;
  for(const band of bands){
    r -= band.weight ?? 1;
    if(r <= 0) return band;
  }
  return bands[bands.length - 1];
}

function samplePhysicalSiValue(quantityId, mode = settings.mode){
  const band = chooseWeightedBand(physicalProfileBands(quantityId, mode));
  if(!band) return null;
  if(band.scale === 'linear') return randomFloat(band.min, band.max);
  return Math.pow(10, randomFloat(Math.log10(band.min), Math.log10(band.max)));
}

function physicalValueFitsProfile(quantityId, value, mode = settings.mode){
  if(!Number.isFinite(value) || value <= 0) return false;
  const bands = physicalProfileBands(quantityId, mode);
  if(!bands.length) return true;
  return bands.some(b => value >= b.min * (1 - 1e-12) && value <= b.max * (1 + 1e-12));
}

function compoundConversionMode(mode = settings.mode){
  if(mode !== 'ss') return null;
  if(!settings.compoundConversionByMode) settings.compoundConversionByMode = structuredClone(defaultSettings.compoundConversionByMode);
  return settings.compoundConversionByMode.ss === 'one' ? 'one' : 'both';
}

function compoundDifferenceCount(from, to){
  if(!from?.parts || !to?.parts) return null;
  const keys = ['numerator','denominator'];
  return keys.reduce((n, key) => n + (from.parts[key] !== to.parts[key] ? 1 : 0), 0);
}

'''
html = html.replace(anchor, profiles + anchor, 1)

# 8) Replace unit-pair chooser to honor one/both components on SŠ and reject same-factor conversions.
html = re.sub(
    r"function chooseUnitPair\(units\)\{[\s\S]*?\n\}\n\nfunction shuffle",
    r'''function chooseUnitPair(units){
  if(units.length < 2) return null;
  let best = null;
  const compoundMode = compoundConversionMode();
  for(let i=0; i<600; i++){
    const from = randomChoice(units);
    const to = randomChoice(units);
    if(from.unit === to.unit) continue;
    if(Math.abs(from.factor - to.factor) <= Math.max(Math.abs(from.factor), Math.abs(to.factor), 1) * 1e-15) continue;

    const diffCount = compoundDifferenceCount(from, to);
    if(compoundMode && diffCount !== null){
      if(compoundMode === 'one' && diffCount !== 1) continue;
      if(compoundMode === 'both' && diffCount !== 2) continue;
    }

    const jump = Math.abs((from.order ?? Math.log10(from.factor)) - (to.order ?? Math.log10(to.factor)));
    if(jump < settings.minJump && units.length > 2) {
      best = best || {from, to};
      continue;
    }
    return {from, to};
  }
  return best;
}

function shuffle''',
    html,
    count=1
)

# 9) Add formatting from a physical SI value, then makeExample uses it.
anchor = "function randomValueInRange(min, max){"
helper = r'''function visibleNumberFromPhysicalSi(siValue, pair, useExponential = false){
  const raw = siValue / pair.from.factor;
  if(!Number.isFinite(raw) || raw <= 0) return null;

  if(useExponential){
    const rounded = roundToSignificant(raw, 2);
    if(!Number.isFinite(rounded) || rounded <= 0) return null;
    const exponent = Math.floor(Math.log10(rounded));
    if(exponent < -10 || exponent > 10) return null;
    if(pair.from.factor < pair.to.factor && exponent <= 0) return null;
    if(pair.from.factor > pair.to.factor && exponent >= 0) return null;
    const mantissa = rounded / Math.pow(10, exponent);
    const visible = formatExponentialText(trimCz(formatCz(mantissa, 0, 1)), exponent);
    return {visible, value:rounded, exponential:true};
  }

  const range = numberRange(pair, false);
  const rounded = roundToSignificant(raw, 2);
  const decimals = decimalPlacesFor(rounded);
  const visible = formatCz(rounded, decimals, decimals);
  const parsed = parseCzNumber(visible);
  if(!Number.isFinite(parsed) || parsed <= 0 || parsed < range.min || parsed > range.max) return null;
  return {visible, value:parsed, exponential:false};
}

'''
if anchor not in html:
    raise SystemExit('visible physical helper anchor missing')
html = html.replace(anchor, helper + anchor, 1)

html = re.sub(
    r"function makeExample\(index, preferredQuantity, useExponentialInput = false\)\{[\s\S]*?\n\}\n\nfunction generateExamples",
    r'''function makeExample(index, preferredQuantity, useExponentialInput = false){
  const quantities = preferredQuantity ? [preferredQuantity] : selectedQuantities();
  if(!quantities.length) return null;
  for(let guard=0; guard<900; guard++){
    const q = preferredQuantity || randomChoice(quantities);
    const units = q.build(settings.mode).filter(u => Number.isFinite(u.factor) && u.factor !== 0);
    const pair = chooseUnitPair(units);
    if(!pair) continue;

    const sampledSi = samplePhysicalSiValue(q.id, settings.mode);
    if(!sampledSi) continue;
    const x = visibleNumberFromPhysicalSi(sampledSi, pair, useExponentialInput);
    if(!x) continue;

    const displayedSi = x.value * pair.from.factor;
    if(!physicalValueFitsProfile(q.id, displayedSi, settings.mode)) continue;
    const result = displayedSi / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    const significantFigures = countVisibleSignificantFigures(x.visible);
    const resultLimits = resultLimitsForMode();
    if(resultLimits.enabled && !resultFitsLimits(result, significantFigures, resultLimits)) continue;
    return {
      index,
      quantity:q.title,
      quantityId:q.id,
      value:x.visible,
      exponentialInput:x.exponential,
      exponentialFormat:Boolean(useExponentialInput),
      from:pair.from.unit,
      to:pair.to.unit,
      result,
      siValue:displayedSi,
      significantFigures,
      resultPlain:formatSignificantPlain(result, significantFigures),
      resultExp:formatExpNumber(result, significantFigures)
    };
  }
  return null;
}

function generateExamples''',
    html,
    count=1
)

# 10) Fill/apply/summary compound setting.
needle = "  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);\n  $('ensureAllQuantitiesInput').checked = ensureAllQuantitiesForMode();"
repl = "  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);\n  $('compoundConversionSetting').style.display = settings.mode === 'ss' ? 'flex' : 'none';\n  $('compoundConversionInput').value = compoundConversionMode() || 'both';\n  $('ensureAllQuantitiesInput').checked = ensureAllQuantitiesForMode();"
if needle not in html:
    raise SystemExit('fill settings anchor missing')
html = html.replace(needle, repl, 1)

needle = "  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;\n\n  const quantities ="
repl = "  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;\n  if(settings.mode === 'ss') settings.compoundConversionByMode.ss = $('compoundConversionInput').value === 'one' ? 'one' : 'both';\n\n  const quantities ="
if needle not in html:
    raise SystemExit('apply settings anchor missing')
html = html.replace(needle, repl, 1)

needle = "    <span class=\"pill\">${settings.mode === 'ss' ? `exp. tvar: ${expCount} veličin` : 'bez exp. tvaru'}</span>"
repl = needle + "\n    ${settings.mode === 'ss' ? `<span class=\"pill\">složené jednotky: ${compoundConversionMode() === 'one' ? 'měnit jednu část' : 'měnit obě části'}</span>` : ''}"
if needle not in html:
    raise SystemExit('summary anchor missing')
html = html.replace(needle, repl, 1)

# 11) Tests: expose physical/compound helpers and verify defaults, profiles and pair mode.
needle = "  resultTextsForExample\n};`"
repl = "  resultTextsForExample,\n  physicalValueFitsProfile,\n  compoundDifferenceCount\n};`"
if needle not in test:
    raise SystemExit('test API anchor missing')
test = test.replace(needle, repl, 1)

needle = "assert.equal(JSON.stringify(defaults.exponentialQuantitiesByMode.ss), JSON.stringify(['delka','hmotnost','sila','energie']), 'Výchozí SŠ exp. veličiny se změnily.');"
repl = needle + "\nassert.equal(defaults.compoundConversionByMode.ss, 'both', 'Výchozí SŠ složené jednotky mají měnit obě části.');\nassert.equal(defaults.numberSettingsByMode.ss.niceInputByUnitSize, true, 'SŠ má mít výchozí hezčí zadání zapnuté.');\nassert.equal(defaults.resultLimitsByMode.ss.enabled, true, 'SŠ má mít výchozí omezení délky výsledku zapnuté.');"
if needle not in test:
    raise SystemExit('default test anchor missing')
test = test.replace(needle, repl, 1)

# Add profile assertion in main stress loop after input is parsed.
needle = "      assert(Number.isFinite(input) && input > 0, `Neplatné číslo v zadání: ${ex.value}`);\n      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Zadání má více než dvě platné číslice: ${ex.value}.`);"
repl = "      assert(Number.isFinite(input) && input > 0, `Neplatné číslo v zadání: ${ex.value}`);\n      const fromFactorPhysical = unitFactor(q, mode, ex.from);\n      const siValue = input * fromFactorPhysical;\n      assert(api.physicalValueFitsProfile(quantityId, siValue, mode), `Fyzikální hodnota mimo profil: ${ex.value} ${ex.from} (${quantityId}, ${mode}).`);\n      if(quantityId === 'rychlost') assert(siValue >= 3 - 1e-12 && siValue <= 45 + 1e-12, `Rychlost není cyklistická/automobilní: ${siValue} m/s.`);\n      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Zadání má více než dvě platné číslice: ${ex.value}.`);"
if needle not in test:
    raise SystemExit('stress input anchor missing')
test = test.replace(needle, repl, 1)

# Add explicit compound-mode stress before final console logs.
anchor = "console.log(`OK: ${generated} náhodně vygenerovaných příkladů prošlo kontrolami.`);"
block = r'''// SŠ: u složených jednotek musí jít vynutit změnu obou částí i jen jedné části.
for(const compoundMode of ['both','one']){
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.compoundConversionByMode.ss = compoundMode;
  cfg.resultLimitsByMode.ss.enabled = false;
  cfg.minJump = 1;
  api.setSettings(cfg);
  for(const quantityId of ['rychlost','hustota','zrychleni']){
    const q = quantityById(quantityId);
    for(let i=0; i<120; i++){
      const ex = api.makeExample(i + 1, q, false);
      assert(ex, `${quantityId}: nelze vytvořit SŠ složený převod v režimu ${compoundMode}.`);
      const fromUnit = q.build('ss').find(u => u.unit === ex.from);
      const toUnit = q.build('ss').find(u => u.unit === ex.to);
      const diff = api.compoundDifferenceCount(fromUnit, toUnit);
      assert.equal(diff, compoundMode === 'one' ? 1 : 2, `${quantityId}: režim ${compoundMode} změnil ${diff} částí (${ex.from} → ${ex.to}).`);
      generated++;
    }
  }
}

// Elektrický náboj nesmí používat absurdně velké předpony.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  api.setSettings(cfg);
  const chargeUnits = quantityById('naboj').build('ss').map(u => u.unit);
  for(const forbidden of ['kC','MC','GC','TC','PC']) assert(!chargeUnits.includes(forbidden), `Náboj nesmí obsahovat ${forbidden}.`);
}

'''
if anchor not in test:
    raise SystemExit('final test anchor missing')
test = test.replace(anchor, block + anchor, 1)
test = test.replace(
    "Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.",
    "Kontrolováno: povinná veličina, realistické SI profily, rychlost 3–45 m/s, max. 2 platné číslice, SŠ složené jednotky jedna/obě části, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku, rozumné jednotky náboje a Energie* bez kalorií."
)

hp.write_text(html, encoding='utf-8')
tp.write_text(test, encoding='utf-8')
