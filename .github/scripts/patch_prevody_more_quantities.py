from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

old = '''    <div class="card">\n      <h3>Veličiny</h3>\n      <div id="quantityChecks" class="checks"></div>\n    </div>'''
new = '''    <div class="card">\n      <h3>Veličiny</h3>\n      <label class="check" style="margin-bottom:10px">\n        <input id="ensureAllQuantitiesInput" type="checkbox">\n        <span>Každá vybraná veličina se má v sadě objevit alespoň jednou.</span>\n      </label>\n      <p class="small" style="margin-top:0">Když je volba zapnutá a je vybráno více veličin než příkladů, počet příkladů se automaticky zvýší.</p>\n      <div id="quantityChecks" class="checks"></div>\n    </div>'''
assert old in text, 'quantity card not found'
text = text.replace(old, new, 1)

old = '''  resultLimitsByMode:{\n    zs:{enabled:true, maxIntegerDigits:7, maxDecimals:6},\n    ss:{enabled:false, maxIntegerDigits:7, maxDecimals:6}\n  },\n  prefixes:['n','µ','m','c','d','','da','h','k','M','G'],\n  quantitiesByMode:{\n    zs:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','napeti'],\n    ss:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','napeti','cas','vykon','naboj','kapacita','proud','odpor']\n  }'''
new = '''  resultLimitsByMode:{\n    zs:{enabled:true, maxIntegerDigits:7, maxDecimals:6},\n    ss:{enabled:false, maxIntegerDigits:7, maxDecimals:6}\n  },\n  ensureAllQuantitiesByMode:{zs:true, ss:true},\n  prefixes:['n','µ','m','c','d','','da','h','k','M','G'],\n  quantitiesByMode:{\n    zs:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','napeti'],\n    ss:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','napeti']\n  }'''
assert old in text, 'defaults block not found'
text = text.replace(old, new, 1)

old = '''  {id:'napeti', title:'Napětí', modes:['zs','ss'], build:buildVoltageUnits},\n  {id:'cas', title:'Čas', modes:['ss'], build:buildTimeUnits},\n  {id:'vykon', title:'Výkon', modes:['ss'], build:buildPowerUnits},\n  {id:'naboj', title:'Náboj', modes:['ss'], build:buildChargeUnits},\n  {id:'kapacita', title:'Kapacita', modes:['ss'], build:buildCapacitanceUnits},\n  {id:'proud', title:'Proud', modes:['ss'], build:buildCurrentUnits},\n  {id:'odpor', title:'Odpor', modes:['ss'], build:buildResistanceUnits}\n];'''
new = '''  {id:'napeti', title:'Napětí', modes:['zs','ss'], build:buildVoltageUnits},\n  {id:'cas', title:'Čas', modes:['zs','ss'], build:buildTimeUnits},\n  {id:'vykon', title:'Výkon', modes:['zs','ss'], build:buildPowerUnits},\n  {id:'proud', title:'Elektrický proud', modes:['zs','ss'], build:buildCurrentUnits},\n  {id:'odpor', title:'Elektrický odpor', modes:['zs','ss'], build:buildResistanceUnits},\n  {id:'zrychleni', title:'Zrychlení', modes:['zs','ss'], build:buildAccelerationUnits},\n  {id:'frekvence', title:'Frekvence', modes:['zs','ss'], build:buildFrequencyUnits},\n  {id:'uhel', title:'Úhel', modes:['zs','ss'], build:buildAngleUnits},\n  {id:'naboj', title:'Elektrický náboj', modes:['ss'], build:buildChargeUnits},\n  {id:'kapacita', title:'Kapacita', modes:['ss'], build:buildCapacitanceUnits},\n  {id:'vodivost', title:'Elektrická vodivost', modes:['ss'], build:buildConductanceUnits},\n  {id:'magindukce', title:'Magnetická indukce', modes:['ss'], build:buildMagneticInductionUnits},\n  {id:'magnetickytok', title:'Magnetický tok', modes:['ss'], build:buildMagneticFluxUnits},\n  {id:'indukcnost', title:'Indukčnost', modes:['ss'], build:buildInductanceUnits},\n  {id:'latkovemnozstvi', title:'Látkové množství', modes:['ss'], build:buildAmountUnits}\n];'''
assert old in text, 'quantity metadata block not found'
text = text.replace(old, new, 1)

old = '''function buildResistanceUnits(){\n  return prefixedUnits('Ω', ['f','p','n','µ','m','','k','M','G','T','P']);\n}\n\nfunction availableQuantities(){'''
new = '''function buildResistanceUnits(){\n  return prefixedUnits('Ω', ['f','p','n','µ','m','','k','M','G','T','P']);\n}\n\nfunction buildAccelerationUnits(){\n  return prefixedUnits('m/s²', ['n','µ','m','c','d','','k']);\n}\n\nfunction buildFrequencyUnits(){\n  return prefixedUnits('Hz', ['f','p','n','µ','m','','k','M','G','T']);\n}\n\nfunction buildAngleUnits(){\n  return filterUnits([\n    unit('°', Math.PI / 180, -1.76, null),\n    unit('rad', 1, 0, ''),\n    unit('mrad', 1e-3, -3, 'm'),\n    unit('µrad', 1e-6, -6, 'µ')\n  ]);\n}\n\nfunction buildConductanceUnits(){\n  return prefixedUnits('S', ['f','p','n','µ','m','','k','M','G']);\n}\n\nfunction buildMagneticInductionUnits(){\n  return prefixedUnits('T', ['p','n','µ','m','','k','M']);\n}\n\nfunction buildMagneticFluxUnits(){\n  return prefixedUnits('Wb', ['f','p','n','µ','m','','k','M']);\n}\n\nfunction buildInductanceUnits(){\n  return prefixedUnits('H', ['f','p','n','µ','m','','k','M']);\n}\n\nfunction buildAmountUnits(){\n  return prefixedUnits('mol', ['n','µ','m','','k','M']);\n}\n\nfunction ensureAllQuantitiesForMode(mode = settings.mode){\n  if(!settings.ensureAllQuantitiesByMode) settings.ensureAllQuantitiesByMode = structuredClone(defaultSettings.ensureAllQuantitiesByMode);\n  if(typeof settings.ensureAllQuantitiesByMode[mode] !== 'boolean'){\n    settings.ensureAllQuantitiesByMode[mode] = Boolean(defaultSettings.ensureAllQuantitiesByMode[mode]);\n  }\n  return settings.ensureAllQuantitiesByMode[mode];\n}\n\nfunction availableQuantities(){'''
assert old in text, 'resistance/available anchor not found'
text = text.replace(old, new, 1)

old = '''function generateExamples(){\n  const count = clampInt(settings.count, 1, 60);\n  const quantities = selectedQuantities();\n  let cycle = shuffle(quantities);'''
new = '''function generateExamples(){\n  const quantities = selectedQuantities();\n  let count = clampInt(settings.count, 1, 60);\n  if(ensureAllQuantitiesForMode() && quantities.length > count){\n    count = Math.min(60, quantities.length);\n    settings.count = count;\n  }\n  let cycle = shuffle(quantities);'''
assert old in text, 'generateExamples header not found'
text = text.replace(old, new, 1)

old = '''    <span class="pill">${qCount} veličin</span>\n    <span class="pill">${formatPlainNumber(numberSettings.minNumber)} až ${formatPlainNumber(numberSettings.maxNumber)}</span>'''
new = '''    <span class="pill">${qCount} veličin</span>\n    <span class="pill">${ensureAllQuantitiesForMode() ? 'všechny vybrané veličiny v sadě' : 'veličiny náhodně'}</span>\n    <span class="pill">${formatPlainNumber(numberSettings.minNumber)} až ${formatPlainNumber(numberSettings.maxNumber)}</span>'''
assert old in text, 'summary quantity line not found'
text = text.replace(old, new, 1)

old = '''  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);\n\n  const selectedQ = new Set(settings.quantitiesByMode[settings.mode] || []);'''
new = '''  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);\n  $('ensureAllQuantitiesInput').checked = ensureAllQuantitiesForMode();\n\n  const selectedQ = new Set(settings.quantitiesByMode[settings.mode] || []);'''
assert old in text, 'fillSettings anchor not found'
text = text.replace(old, new, 1)

old = '''  const quantities = [...$('quantityChecks').querySelectorAll('input:checked')].map(i => i.value);\n  settings.quantitiesByMode[settings.mode] = quantities;\n  const chosenPrefixes = [...$('prefixChecks').querySelectorAll('input:checked')].map(i => i.value);'''
new = '''  const quantities = [...$('quantityChecks').querySelectorAll('input:checked')].map(i => i.value);\n  settings.quantitiesByMode[settings.mode] = quantities;\n  settings.ensureAllQuantitiesByMode[settings.mode] = $('ensureAllQuantitiesInput').checked;\n  if(settings.ensureAllQuantitiesByMode[settings.mode] && quantities.length > settings.count){\n    settings.count = Math.min(60, quantities.length);\n  }\n  const chosenPrefixes = [...$('prefixChecks').querySelectorAll('input:checked')].map(i => i.value);'''
assert old in text, 'apply quantity block not found'
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
