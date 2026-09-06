from pathlib import Path

html_path = Path('prevody.html')
test_path = Path('tests/prevody.test.mjs')
text = html_path.read_text(encoding='utf-8')
test = test_path.read_text(encoding='utf-8')

old = '''    const value = mantissa * Math.pow(10, exponent);\n    if(value >= range.min && value <= range.max){\n      const visible = `${trimCz(formatCz(mantissa, 0, 1))}·10${toSuperscript(exponent)}`;\n      return {visible, value, exponential:true};\n    }'''
new = '''    const value = mantissa * Math.pow(10, exponent);\n    if(value >= range.min && value <= range.max){\n      const visible = formatExponentialText(trimCz(formatCz(mantissa, 0, 1)), exponent);\n      return {visible, value, exponential:true};\n    }'''
if old not in text:
    raise SystemExit('randomExponentialNumber anchor not found')
text = text.replace(old, new, 1)

old = '''function formatExpNumber(value, significantFigures = 3){\n  if(value === 0) return '0';\n  const {mantissa, exponent} = significantExponentialParts(value, significantFigures);\n  return `${mantissa.replace('.', ',')}·10${toSuperscript(exponent)}`;\n}\n'''
new = '''function formatExponentialText(mantissaText, exponent){\n  const mantissa = String(mantissaText).replace('.', ',');\n  return exponent === 0 ? mantissa : `${mantissa}·10${toSuperscript(exponent)}`;\n}\n\nfunction formatExpNumber(value, significantFigures = 3){\n  if(value === 0) return '0';\n  const {mantissa, exponent} = significantExponentialParts(value, significantFigures);\n  return formatExponentialText(mantissa, exponent);\n}\n'''
if old not in text:
    raise SystemExit('formatExpNumber anchor not found')
text = text.replace(old, new, 1)

old = '''  resultFitsLimits,\n  usesExponentialForQuantity\n};`;'''
new = '''  resultFitsLimits,\n  usesExponentialForQuantity,\n  formatExponentialText,\n  numberRange\n};`;'''
if old not in test:
    raise SystemExit('test API anchor not found')
test = test.replace(old, new, 1)

anchor = '''const defaults = api.getDefaultSettings();\nconst expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];'''
insert = '''const defaults = api.getDefaultSettings();\n\n// Exponent 0 se nesmí zobrazovat jako zbytečné ·10⁰.\nassert.equal(api.formatExponentialText('3,5', 0), '3,5', 'Exponent 0 se má zobrazit běžně.');\nassert.equal(api.formatExponentialText('3.5', 0), '3,5', 'Exponent 0 musí používat desetinnou čárku.');\nassert.equal(api.formatExponentialText('3.5', -10), '3,5·10⁻¹⁰', 'Dolní okraj exp. rozsahu se formátuje chybně.');\nassert.equal(api.formatExponentialText('9.6', 10), '9,6·10¹⁰', 'Horní okraj exp. rozsahu se formátuje chybně.');\n\nconst ssRangeCfg = structuredClone(defaults);\nssRangeCfg.mode = 'ss';\napi.setSettings(ssRangeCfg);\nconst ssExpRange = api.numberRange(null, true);\nassert.equal(ssExpRange.min, 1e-10, 'SŠ exp. rozsah má začínat na 10^-10.');\nassert.equal(ssExpRange.max, 1e10, 'SŠ exp. rozsah má končit na 10^10.');\n\nconst expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];'''
if anchor not in test:
    raise SystemExit('defaults test anchor not found')
test = test.replace(anchor, insert, 1)

test = test.replace(
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách (default Délka/Hmotnost/Síla/Energie), min/max jen pro běžná zadání, exp. rozsah 10^-10 až 10^10, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');",
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');"
)

html_path.write_text(text, encoding='utf-8')
test_path.write_text(test, encoding='utf-8')
