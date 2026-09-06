from pathlib import Path

html_path = Path('prevody.html')
test_path = Path('tests/prevody.test.mjs')
text = html_path.read_text(encoding='utf-8')
test = test_path.read_text(encoding='utf-8')

# Explain the role of min/max clearly in the UI.
old = '''        <div class="settingField">
          <label for="minNumberInput">Nejmenší číslo v zadání</label>
          <input id="minNumberInput" type="number" min="0" step="any">
        </div>
        <div class="settingField">
          <label for="maxNumberInput">Největší číslo v zadání</label>
          <input id="maxNumberInput" type="number" min="0" step="any">
        </div>'''
new = '''        <div class="settingField">
          <label for="minNumberInput">Nejmenší číslo v běžném zadání</label>
          <input id="minNumberInput" type="number" min="0" step="any">
        </div>
        <div class="settingField">
          <label for="maxNumberInput">Největší číslo v běžném zadání</label>
          <input id="maxNumberInput" type="number" min="0" step="any">
        </div>'''
if old not in text:
    raise SystemExit('Min/max UI anchor not found')
text = text.replace(old, new, 1)

old = '''      </div>
      <div class="sep"></div>
      <label class="check">
        <input id="niceInputRuleInput" type="checkbox">'''
new = '''      </div>
      <p class="small" style="margin-bottom:0">Na SŠ se tento min/max rozsah vztahuje jen na běžná zadání bez exponenciálního tvaru. Exponenciální zadání mají vlastní rozsah řádů.</p>
      <div class="sep"></div>
      <label class="check">
        <input id="niceInputRuleInput" type="checkbox">'''
if old not in text:
    raise SystemExit('Min/max note anchor not found')
text = text.replace(old, new, 1)

# Two significant digits max for generated assignment numbers.
old = '''function randomChoice(arr){
  return arr[Math.floor(Math.random() * arr.length)];
}

function decimalPlacesFor(x){'''
new = '''function randomChoice(arr){
  return arr[Math.floor(Math.random() * arr.length)];
}

function roundToSignificant(value, significantFigures = 2){
  if(!Number.isFinite(value) || value === 0) return value;
  const sig = clampInt(significantFigures, 1, 15);
  const exponent = Math.floor(Math.log10(Math.abs(value)));
  const scale = Math.pow(10, sig - 1 - exponent);
  return Math.round(value * scale) / scale;
}

function decimalPlacesFor(x){'''
if old not in text:
    raise SystemExit('roundToSignificant anchor not found')
text = text.replace(old, new, 1)

# SŠ exponential inputs deliberately ignore the global plain-number min/max.
old = '''function numberRange(pair = null){
  const numberSettings = numberSettingsForMode();
  let min = positiveNumber(numberSettings.minNumber, 0.01);
  let max = positiveNumber(numberSettings.maxNumber, 9999);'''
new = '''function numberRange(pair = null, useExponential = false){
  if(settings.mode === 'ss' && useExponential){
    return {min:1e-10, max:1e10};
  }
  const numberSettings = numberSettingsForMode();
  let min = positiveNumber(numberSettings.minNumber, 0.01);
  let max = positiveNumber(numberSettings.maxNumber, 9999);'''
if old not in text:
    raise SystemExit('numberRange anchor not found')
text = text.replace(old, new, 1)

old = '''function randomVisibleNumber(useExponential = false, pair = null){
  const range = numberRange(pair);
  return useExponential ? randomExponentialNumber(range) : randomPlainNumber(range);
}'''
new = '''function randomVisibleNumber(useExponential = false, pair = null){
  const range = numberRange(pair, useExponential);
  return useExponential ? randomExponentialNumber(range) : randomPlainNumber(range);
}'''
if old not in text:
    raise SystemExit('randomVisibleNumber anchor not found')
text = text.replace(old, new, 1)

old = '''function randomPlainNumber(range){
  for(let attempt=0; attempt<200; attempt++){
    const value = randomValueInRange(range.min, range.max);
    const decimals = decimalPlacesFor(value);
    const visible = formatCz(value, decimals, decimals);
    const parsed = parseCzNumber(visible);
    if(parsed > 0 && parsed >= range.min && parsed <= range.max){
      return {visible, value:parsed, exponential:false};
    }
  }

  const fallback = Math.min(range.max, Math.max(range.min, 1));
  const decimals = decimalPlacesFor(fallback);
  const visible = formatCz(fallback, decimals, decimals);
  return {visible, value:parseCzNumber(visible), exponential:false};
}'''
new = '''function randomPlainNumber(range){
  for(let attempt=0; attempt<200; attempt++){
    const rawValue = randomValueInRange(range.min, range.max);
    const value = roundToSignificant(rawValue, 2);
    const decimals = decimalPlacesFor(value);
    const visible = formatCz(value, decimals, decimals);
    const parsed = parseCzNumber(visible);
    if(parsed > 0 && parsed >= range.min && parsed <= range.max){
      return {visible, value:parsed, exponential:false};
    }
  }

  const fallbackRaw = Math.min(range.max, Math.max(range.min, 1));
  const fallback = roundToSignificant(fallbackRaw, 2);
  const decimals = decimalPlacesFor(fallback);
  const visible = formatCz(fallback, decimals, decimals);
  return {visible, value:parseCzNumber(visible), exponential:false};
}'''
if old not in text:
    raise SystemExit('randomPlainNumber anchor not found')
text = text.replace(old, new, 1)

old = '''    const mantissaRaw = randomFloat(Math.max(1, lowMantissa), Math.min(9.99, highMantissa));
    const mantissa = Number(trimCz(formatCz(mantissaRaw, 0, 2)).replace(',', '.'));
    const value = mantissa * Math.pow(10, exponent);
    if(value >= range.min && value <= range.max){
      const visible = `${trimCz(formatCz(mantissa, 0, 2))}·10${toSuperscript(exponent)}`;
      return {visible, value, exponential:true};
    }'''
new = '''    const mantissaRaw = randomFloat(Math.max(1, lowMantissa), Math.min(9.99, highMantissa));
    const mantissa = roundToSignificant(mantissaRaw, 2);
    if(mantissa < 1 || mantissa >= 10) continue;
    const value = mantissa * Math.pow(10, exponent);
    if(value >= range.min && value <= range.max){
      const visible = `${trimCz(formatCz(mantissa, 0, 1))}·10${toSuperscript(exponent)}`;
      return {visible, value, exponential:true};
    }'''
if old not in text:
    raise SystemExit('randomExponentialNumber anchor not found')
text = text.replace(old, new, 1)

# Integer trailing zeros are placeholders of order, not extra significant figures.
old = '''function countVisibleSignificantFigures(visible){
  let s = String(visible ?? '').replace(/\\u202f/g, '').replace(/\\s/g, '');
  s = s.split('·10')[0].split('×10')[0];
  s = s.replace(/^[+-]/, '').replace(/[,.]/g, '');
  s = s.replace(/^0+/, '');
  return clampInt(s.length || 1, 1, 15);
}'''
new = '''function countVisibleSignificantFigures(visible){
  let raw = String(visible ?? '').replace(/\\u202f/g, '').replace(/\\s/g, '');
  raw = raw.split('·10')[0].split('×10')[0].replace(/^[+-]/, '');
  const hasDecimalSeparator = /[,.]/.test(raw);
  let s = raw.replace(/[,.]/g, '').replace(/^0+/, '');
  if(!hasDecimalSeparator) s = s.replace(/0+$/, '');
  return clampInt(s.length || 1, 1, 15);
}'''
if old not in text:
    raise SystemExit('countVisibleSignificantFigures anchor not found')
text = text.replace(old, new, 1)

# Strengthen regression tests: max two sig figs and min/max only for non-exponential SŠ inputs.
old = '''      const input = visibleNumberToNumber(ex.value);
      assert(Number.isFinite(input) && input > 0, `Neplatné číslo v zadání: ${ex.value}`);
      assert(input >= range.minNumber - 1e-12, `Zadání ${ex.value} je pod minimem ${range.minNumber} (${quantityId}, ${mode}).`);
      assert(input <= range.maxNumber + 1e-12, `Zadání ${ex.value} překročilo maximum ${range.maxNumber} (${quantityId}, ${mode}).`);

      const fromFactor = unitFactor(q, mode, ex.from);'''
new = '''      const input = visibleNumberToNumber(ex.value);
      assert(Number.isFinite(input) && input > 0, `Neplatné číslo v zadání: ${ex.value}`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Zadání má více než dvě platné číslice: ${ex.value}.`);
      if(mode === 'ss' && ex.exponentialInput){
        assert(input >= 1e-10 - 1e-24, `Exponenciální zadání ${ex.value} je pod 10^-10.`);
        assert(input <= 1e10 + 1e-2, `Exponenciální zadání ${ex.value} je nad 10^10.`);
      }else{
        assert(input >= range.minNumber - 1e-12, `Zadání ${ex.value} je pod minimem ${range.minNumber} (${quantityId}, ${mode}).`);
        assert(input <= range.maxNumber + 1e-12, `Zadání ${ex.value} překročilo maximum ${range.maxNumber} (${quantityId}, ${mode}).`);
      }

      const fromFactor = unitFactor(q, mode, ex.from);'''
if old not in test:
    raise SystemExit('Primary test input-range anchor not found')
test = test.replace(old, new, 1)

old = '''      assert.equal(ex.quantityId, q.id, `Veličina ${q.id} (${mode}) byla nahrazena za ${ex.quantityId}.`);
      generated++;'''
new = '''      assert.equal(ex.quantityId, q.id, `Veličina ${q.id} (${mode}) byla nahrazena za ${ex.quantityId}.`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Veličina ${q.id} (${mode}) vygenerovala více než dvě platné číslice: ${ex.value}.`);
      generated++;'''
if old not in test:
    raise SystemExit('Secondary test sigfig anchor not found')
test = test.replace(old, new, 1)

test = test.replace(
    "console.log('Kontrolováno: povinná veličina, globální min/max zadání, převod z viditelného čísla, platné číslice, limit výsledku a Energie* bez kalorií.');",
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, min/max jen pro běžná zadání, exp. rozsah 10^-10 až 10^10, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');"
)

html_path.write_text(text, encoding='utf-8')
test_path.write_text(test, encoding='utf-8')
