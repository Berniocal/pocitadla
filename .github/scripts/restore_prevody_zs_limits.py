from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

# Restore ZŠ-only result length controls.
old = '''        <div class="settingField">
          <label for="jumpInput">Nejmenší skok mezi běžnými jednotkami</label>
          <input id="jumpInput" type="number" min="1" max="8" step="1">
        </div>'''
new = old + '''
        <div class="settingField zsResultLimit">
          <label for="zsResultMaxIntegerDigitsInput">Maximálně číslic před desetinnou čárkou ve výsledku (ZŠ)</label>
          <input id="zsResultMaxIntegerDigitsInput" type="number" min="1" max="15" step="1">
        </div>
        <div class="settingField zsResultLimit">
          <label for="zsResultMaxDecimalsInput">Maximálně desetinných míst ve výsledku (ZŠ)</label>
          <input id="zsResultMaxDecimalsInput" type="number" min="0" max="20" step="1">
        </div>'''
assert old in text, 'settings controls anchor not found'
text = text.replace(old, new, 1)

# Restore defaults: 7 integer digits and 6 decimal places.
old = '''  smallDecimals:2,
  mediumDecimals:1,
  largeDecimals:0,
  minJump:2,
  prefixes:'''
new = '''  smallDecimals:2,
  mediumDecimals:1,
  largeDecimals:0,
  minJump:2,
  zsResultMaxIntegerDigits:7,
  zsResultMaxDecimals:6,
  prefixes:'''
assert old in text, 'defaults anchor not found'
text = text.replace(old, new, 1)

# Keep significant figures from the visible assignment, but reject ZŠ examples
# whose correctly formatted result would exceed the chosen length limits.
old = '''    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    const significantFigures = countVisibleSignificantFigures(x.visible);
    return {'''
new = '''    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    const significantFigures = countVisibleSignificantFigures(x.visible);
    if(settings.mode === 'zs' && !zsResultFitsLimits(result, significantFigures)) continue;
    return {'''
assert old in text, 'makeExample anchor not found'
text = text.replace(old, new, 1)

# Add a limit check based on the already significant-figure-formatted plain result.
old = '''function formatExpNumber(value, significantFigures = 3){
  if(value === 0) return '0';'''
new = '''function zsResultFitsLimits(value, significantFigures){
  const formatted = formatSignificantPlain(value, significantFigures)
    .replace(/\\u202f/g, '')
    .replace(/\\s/g, '');
  const unsigned = formatted.replace(/^[+-]/, '');
  const parts = unsigned.split(',');
  const integerPart = parts[0] || '0';
  const fractionPart = parts[1] || '';
  const maxIntegerDigits = clampInt(settings.zsResultMaxIntegerDigits ?? 7, 1, 15);
  const maxDecimals = clampInt(settings.zsResultMaxDecimals ?? 6, 0, 20);
  return integerPart.length <= maxIntegerDigits && fractionPart.length <= maxDecimals;
}

function formatExpNumber(value, significantFigures = 3){
  if(value === 0) return '0';'''
assert old in text, 'formatter anchor not found'
text = text.replace(old, new, 1)

# Restore summary pill in ZŠ mode.
old = '''    <span class="pill">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
new = '''    <span class="pill">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>
    ${settings.mode === 'zs' ? `<span class="pill">výsledek: max ${settings.zsResultMaxIntegerDigits} číslic / ${settings.zsResultMaxDecimals} des. míst</span>` : ''}
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
assert old in text, 'summary anchor not found'
text = text.replace(old, new, 1)

# Populate and show the limits only for ZŠ.
old = '''  $('largeDecimalsInput').value = settings.largeDecimals;
  $('jumpInput').value = settings.minJump;
  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
new = '''  $('largeDecimalsInput').value = settings.largeDecimals;
  $('jumpInput').value = settings.minJump;
  $('zsResultMaxIntegerDigitsInput').value = settings.zsResultMaxIntegerDigits ?? 7;
  $('zsResultMaxDecimalsInput').value = settings.zsResultMaxDecimals ?? 6;
  document.querySelectorAll('.zsResultLimit').forEach(el => {
    el.style.display = settings.mode === 'zs' ? 'flex' : 'none';
  });
  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
assert old in text, 'fillSettings anchor not found'
text = text.replace(old, new, 1)

# Read the limits back from the form.
old = '''  settings.largeDecimals = clampInt($('largeDecimalsInput').value, 0, 8);
  settings.minJump = clampInt($('jumpInput').value, 1, 8);
  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
new = '''  settings.largeDecimals = clampInt($('largeDecimalsInput').value, 0, 8);
  settings.minJump = clampInt($('jumpInput').value, 1, 8);
  if(settings.mode === 'zs'){
    settings.zsResultMaxIntegerDigits = clampInt($('zsResultMaxIntegerDigitsInput').value, 1, 15);
    settings.zsResultMaxDecimals = clampInt($('zsResultMaxDecimalsInput').value, 0, 20);
  }
  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
assert old in text, 'applySettings anchor not found'
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
