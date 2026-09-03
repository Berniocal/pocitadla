from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

# 1) Add ZŠ-only result limit controls to settings.
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

# 2) Defaults.
old = '''  smallDecimals:2,
  mediumDecimals:1,
  largeDecimals:0,
  minJump:2,'''
new = '''  smallDecimals:2,
  mediumDecimals:1,
  largeDecimals:0,
  minJump:2,
  zsResultMaxIntegerDigits:7,
  zsResultMaxDecimals:6,'''
assert old in text, 'defaults anchor not found'
text = text.replace(old, new, 1)

# 3) Reject ZŠ examples whose result would be unreadable with chosen limits.
old = '''    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    return {'''
new = '''    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    if(settings.mode === 'zs' && !zsResultFitsLimits(result)) continue;
    return {'''
assert old in text, 'result validation anchor not found'
text = text.replace(old, new, 1)

old = '''      result,
      resultPlain:formatPlainNumber(result),
      resultExp:formatExpNumber(result)'''
new = '''      result,
      resultPlain:settings.mode === 'zs' ? formatZsResultNumber(result) : formatPlainNumber(result),
      resultExp:formatExpNumber(result)'''
assert old in text, 'resultPlain anchor not found'
text = text.replace(old, new, 1)

# 4) Add ZŠ formatter. It groups fractional digits in threes and applies display limits.
old = '''function formatExpNumber(value){
  const exponent = value === 0 ? 0 : Math.floor(Math.log10(Math.abs(value)));'''
new = '''function groupFractionDigits(str){
  const parts = String(str).split(',');
  if(parts.length < 2 || !parts[1]) return str;
  const groupedFraction = parts[1].replace(/(.{3})(?=.)/g, `$1${NBSP}`);
  return `${parts[0]},${groupedFraction}`;
}

function formatZsResultNumber(value){
  const maxDecimals = clampInt(settings.zsResultMaxDecimals ?? 6, 0, 20);
  const formatted = trimCz(formatCz(value, 0, maxDecimals));
  return groupFractionDigits(formatted);
}

function zsResultFitsLimits(value){
  const abs = Math.abs(value);
  const maxIntegerDigits = clampInt(settings.zsResultMaxIntegerDigits ?? 7, 1, 15);
  const maxDecimals = clampInt(settings.zsResultMaxDecimals ?? 6, 0, 20);

  if(abs >= Math.pow(10, maxIntegerDigits)) return false;
  if(abs > 0 && abs < 1){
    const rounded = Number(value.toFixed(maxDecimals));
    if(rounded === 0) return false;
  }
  return true;
}

function formatExpNumber(value){
  const exponent = value === 0 ? 0 : Math.floor(Math.log10(Math.abs(value)));'''
assert old in text, 'formatter anchor not found'
text = text.replace(old, new, 1)

# 5) Show current limits in the summary for ZŠ.
old = '''    <span class="pill">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
new = '''    <span class="pill">${numberSettings.niceInputByUnitSize ? 'hezčí zadání zapnuto' : 'hezčí zadání vypnuto'}</span>
    ${settings.mode === 'zs' ? `<span class="pill">výsledek: max ${settings.zsResultMaxIntegerDigits} číslic / ${settings.zsResultMaxDecimals} des. míst</span>` : ''}
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
assert old in text, 'summary anchor not found'
text = text.replace(old, new, 1)

# 6) Populate and show/hide the ZŠ-only controls.
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
assert old in text, 'fill form anchor not found'
text = text.replace(old, new, 1)

# 7) Read values back from settings in ZŠ mode.
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
assert old in text, 'apply form anchor not found'
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
