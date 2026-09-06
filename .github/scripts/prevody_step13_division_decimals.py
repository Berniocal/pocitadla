from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

old = '''function makeExample(index, preferredQuantity, useExponentialInput = false){\n  const quantities = preferredQuantity ? [preferredQuantity] : selectedQuantities();'''
new = '''function ratioNearlyEqual(a, b){\n  return Math.abs(a - b) <= Math.max(Math.abs(a), Math.abs(b), 1) * 1e-12;\n}\n\nfunction resultNeedsTenths(pair){\n  if(!pair?.from || !pair?.to) return false;\n  const ratio = pair.from.factor / pair.to.factor;\n  return ratioNearlyEqual(ratio, 1 / 3.6) || ratioNearlyEqual(ratio, 1 / 60);\n}\n\nfunction formattedResultForPair(result, significantFigures, pair){\n  if(resultNeedsTenths(pair)){\n    const rounded = Math.round((result + Number.EPSILON) * 10) / 10;\n    const plain = formatCz(rounded, 1, 1);\n    const displaySig = countVisibleSignificantFigures(plain);\n    return {\n      value:rounded,\n      significantFigures:displaySig,\n      plain,\n      exp:formatExpNumber(rounded, displaySig)\n    };\n  }\n  return {\n    value:result,\n    significantFigures,\n    plain:formatSignificantPlain(result, significantFigures),\n    exp:formatExpNumber(result, significantFigures)\n  };\n}\n\nfunction makeExample(index, preferredQuantity, useExponentialInput = false){\n  const quantities = preferredQuantity ? [preferredQuantity] : selectedQuantities();'''
if old not in text:
    raise SystemExit('makeExample anchor not found')
text = text.replace(old, new, 1)

old = '''    const significantFigures = countVisibleSignificantFigures(x.visible);\n    const resultLimits = resultLimitsForMode();\n    if(resultLimits.enabled && !resultFitsLimits(result, significantFigures, resultLimits)) continue;\n    return {'''
new = '''    const significantFigures = countVisibleSignificantFigures(x.visible);\n    const formattedResult = formattedResultForPair(result, significantFigures, pair);\n    const resultLimits = resultLimitsForMode();\n    if(resultLimits.enabled && !resultFitsLimits(formattedResult.value, formattedResult.significantFigures, resultLimits)) continue;\n    return {'''
if old not in text:
    raise SystemExit('result formatting block not found')
text = text.replace(old, new, 1)

old = '''      significantFigures,\n      resultPlain:formatSignificantPlain(result, significantFigures),\n      resultExp:formatExpNumber(result, significantFigures)'''
new = '''      significantFigures,\n      resultPlain:formattedResult.plain,\n      resultExp:formattedResult.exp'''
if old not in text:
    raise SystemExit('result return fields not found')
text = text.replace(old, new, 1)
html_path.write_text(text, encoding='utf-8')

# Test API + deterministic formatting checks.
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')
old = '''  compoundDifferenceCount,\n  chooseUnitPair\n};'''
new = '''  compoundDifferenceCount,\n  chooseUnitPair,\n  resultNeedsTenths,\n  formattedResultForPair\n};'''
if old not in test:
    raise SystemExit('test API anchor not found')
test = test.replace(old, new, 1)

anchor = '''// Elektrický náboj nesmí používat absurdně velké předpony.\n{'''
insert = '''// Při dělení 3,6 nebo 60 se běžný výsledek zaokrouhlí alespoň na desetiny.\n{\n  const speedUnits = quantityById('rychlost').build('ss');\n  const byName = name => speedUnits.find(u => u.unit === name);\n  const kmhToMs = {from:byName('km/h'), to:byName('m/s')};\n  const mminToMs = {from:byName('m/min'), to:byName('m/s')};\n  assert(api.resultNeedsTenths(kmhToMs), 'km/h → m/s musí používat desetiny (dělení 3,6).');\n  assert(api.resultNeedsTenths(mminToMs), 'm/min → m/s musí používat desetiny (dělení 60).');\n  assert.equal(api.formattedResultForPair(100 / 3.6, 1, kmhToMs).plain, '27,8', '100 km/h → m/s má být 27,8 m/s.');\n  assert.equal(api.formattedResultForPair(900 / 60, 1, mminToMs).plain, '15,0', '900 m/min → m/s má být 15,0 m/s.');\n}\n\n'''
if anchor not in test:
    raise SystemExit('test insertion anchor not found')
test = test.replace(anchor, insert + anchor, 1)
test_path.write_text(test, encoding='utf-8')
