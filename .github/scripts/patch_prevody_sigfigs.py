from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

# Remove the temporary ZŠ result-length controls.
old = '''        <div class="settingField zsResultLimit">\n          <label for="zsResultMaxIntegerDigitsInput">Maximálně číslic před desetinnou čárkou ve výsledku (ZŠ)</label>\n          <input id="zsResultMaxIntegerDigitsInput" type="number" min="1" max="15" step="1">\n        </div>\n        <div class="settingField zsResultLimit">\n          <label for="zsResultMaxDecimalsInput">Maximálně desetinných míst ve výsledku (ZŠ)</label>\n          <input id="zsResultMaxDecimalsInput" type="number" min="0" max="20" step="1">\n        </div>\n'''
assert old in text, 'ZŠ result controls not found'
text = text.replace(old, '', 1)

old = '''  minJump:2,\n  zsResultMaxIntegerDigits:7,\n  zsResultMaxDecimals:6,\n  prefixes:'''
new = '''  minJump:2,\n  prefixes:'''
assert old in text, 'ZŠ result defaults not found'
text = text.replace(old, new, 1)

# Results are no longer filtered by arbitrary result length. Instead, derive
# significant figures from exactly what the pupil can see in the assignment.
old = '''    const result = x.value * pair.from.factor / pair.to.factor;\n    if(!Number.isFinite(result) || result === 0) continue;\n    if(settings.mode === 'zs' && !zsResultFitsLimits(result)) continue;\n    return {\n      index,\n      quantity:q.title,\n      quantityId:q.id,\n      value:x.visible,\n      exponentialInput:x.exponential,\n      from:pair.from.unit,\n      to:pair.to.unit,\n      result,\n      resultPlain:settings.mode === 'zs' ? formatZsResultNumber(result) : formatPlainNumber(result),\n      resultExp:formatExpNumber(result)\n    };'''
new = '''    const result = x.value * pair.from.factor / pair.to.factor;\n    if(!Number.isFinite(result) || result === 0) continue;\n    const significantFigures = countVisibleSignificantFigures(x.visible);\n    return {\n      index,\n      quantity:q.title,\n      quantityId:q.id,\n      value:x.visible,\n      exponentialInput:x.exponential,\n      from:pair.from.unit,\n      to:pair.to.unit,\n      result,\n      significantFigures,\n      resultPlain:formatSignificantPlain(result, significantFigures),\n      resultExp:formatExpNumber(result, significantFigures)\n    };'''
assert old in text, 'makeExample result block not found'
text = text.replace(old, new, 1)

# Replace fixed decimal-result formatting by significant-figure formatting.
old = '''function groupFractionDigits(str){\n  const parts = String(str).split(',');\n  if(parts.length < 2 || !parts[1]) return str;\n  const groupedFraction = parts[1].replace(/(.{3})(?=.)/g, `$1${NBSP}`);\n  return `${parts[0]},${groupedFraction}`;\n}\n\nfunction formatZsResultNumber(value){\n  const maxDecimals = clampInt(settings.zsResultMaxDecimals ?? 6, 0, 20);\n  const formatted = trimCz(formatCz(value, 0, maxDecimals));\n  return groupFractionDigits(formatted);\n}\n\nfunction zsResultFitsLimits(value){\n  const abs = Math.abs(value);\n  const maxIntegerDigits = clampInt(settings.zsResultMaxIntegerDigits ?? 7, 1, 15);\n  const maxDecimals = clampInt(settings.zsResultMaxDecimals ?? 6, 0, 20);\n\n  if(abs >= Math.pow(10, maxIntegerDigits)) return false;\n  if(abs > 0 && abs < 1){\n    const rounded = Number(value.toFixed(maxDecimals));\n    if(rounded === 0) return false;\n  }\n  return true;\n}\n\nfunction formatExpNumber(value){\n  const exponent = value === 0 ? 0 : Math.floor(Math.log10(Math.abs(value)));\n  const mantissa = value === 0 ? 0 : value / Math.pow(10, exponent);\n  return `${trimCz(formatCz(mantissa, 0, 3))}·10${toSuperscript(exponent)}`;\n}'''
new = '''function countVisibleSignificantFigures(visible){\n  let s = String(visible ?? '').replace(/\\u202f/g, '').replace(/\\s/g, '');\n  s = s.split('·10')[0].split('×10')[0];\n  s = s.replace(/^[+-]/, '').replace(/[,.]/g, '');\n  s = s.replace(/^0+/, '');\n  return clampInt(s.length || 1, 1, 15);\n}\n\nfunction groupPlainNumberString(raw){\n  let s = String(raw);\n  let sign = '';\n  if(s.startsWith('-')){\n    sign = '-';\n    s = s.slice(1);\n  }\n  const [integerPart, fractionPart = ''] = s.split('.');\n  const groupedInteger = integerPart.replace(/\\B(?=(\\d{3})+(?!\\d))/g, NBSP);\n  const groupedFraction = fractionPart.replace(/(\\d{3})(?=\\d)/g, `$1${NBSP}`);\n  return sign + groupedInteger + (fractionPart ? `,${groupedFraction}` : '');\n}\n\nfunction significantExponentialParts(value, significantFigures){\n  const sig = clampInt(significantFigures, 1, 15);\n  const scientific = Number(value).toExponential(sig - 1);\n  const [mantissa, exponentText] = scientific.split('e');\n  return {mantissa, exponent:Number(exponentText)};\n}\n\nfunction formatSignificantPlain(value, significantFigures){\n  if(!Number.isFinite(value)) return '';\n  if(value === 0) return '0';\n\n  const {mantissa, exponent} = significantExponentialParts(value, significantFigures);\n  const negative = mantissa.startsWith('-');\n  const unsignedMantissa = negative ? mantissa.slice(1) : mantissa;\n  const digits = unsignedMantissa.replace('.', '');\n  const decimalIndex = 1 + exponent;\n\n  let raw;\n  if(decimalIndex <= 0){\n    raw = `0.${'0'.repeat(-decimalIndex)}${digits}`;\n  }else if(decimalIndex >= digits.length){\n    raw = `${digits}${'0'.repeat(decimalIndex - digits.length)}`;\n  }else{\n    raw = `${digits.slice(0, decimalIndex)}.${digits.slice(decimalIndex)}`;\n  }\n\n  return groupPlainNumberString((negative ? '-' : '') + raw);\n}\n\nfunction formatExpNumber(value, significantFigures = 3){\n  if(value === 0) return '0';\n  const {mantissa, exponent} = significantExponentialParts(value, significantFigures);\n  return `${mantissa.replace('.', ',')}·10${toSuperscript(exponent)}`;\n}'''
assert old in text, 'old ZŠ/result formatter block not found'
text = text.replace(old, new, 1)

# Remove summary text about fixed output limits.
old = '''    ${settings.mode === 'zs' ? `<span class="pill">výsledek: max ${settings.zsResultMaxIntegerDigits} číslic / ${settings.zsResultMaxDecimals} des. míst</span>` : ''}\n'''
assert old in text, 'summary ZŠ limit pill not found'
text = text.replace(old, '', 1)

# Remove form population/show-hide logic for deleted controls.
old = '''  $('jumpInput').value = settings.minJump;\n  $('zsResultMaxIntegerDigitsInput').value = settings.zsResultMaxIntegerDigits ?? 7;\n  $('zsResultMaxDecimalsInput').value = settings.zsResultMaxDecimals ?? 6;\n  document.querySelectorAll('.zsResultLimit').forEach(el => {\n    el.style.display = settings.mode === 'zs' ? 'flex' : 'none';\n  });\n  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
new = '''  $('jumpInput').value = settings.minJump;\n  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
assert old in text, 'fillSettings ZŠ limit block not found'
text = text.replace(old, new, 1)

# Remove form read-back logic for deleted controls.
old = '''  settings.minJump = clampInt($('jumpInput').value, 1, 8);\n  if(settings.mode === 'zs'){\n    settings.zsResultMaxIntegerDigits = clampInt($('zsResultMaxIntegerDigitsInput').value, 1, 15);\n    settings.zsResultMaxDecimals = clampInt($('zsResultMaxDecimalsInput').value, 0, 20);\n  }\n  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
new = '''  settings.minJump = clampInt($('jumpInput').value, 1, 8);\n  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
assert old in text, 'applySettings ZŠ limit block not found'
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
