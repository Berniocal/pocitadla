from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

# 1) Replace ZŠ-only controls with per-mode controls and an enable switch.
old = '''        <div class="settingField zsResultLimit">
          <label for="zsResultMaxIntegerDigitsInput">Maximálně číslic před desetinnou čárkou ve výsledku (ZŠ)</label>
          <input id="zsResultMaxIntegerDigitsInput" type="number" min="1" max="15" step="1">
        </div>
        <div class="settingField zsResultLimit">
          <label for="zsResultMaxDecimalsInput">Maximálně desetinných míst ve výsledku (ZŠ)</label>
          <input id="zsResultMaxDecimalsInput" type="number" min="0" max="20" step="1">
        </div>'''
new = '''        <div class="settingField">
          <label class="check">
            <input id="resultLimitEnabledInput" type="checkbox">
            <span>Omezit délku výsledku</span>
          </label>
        </div>
        <div class="settingField">
          <label for="resultMaxIntegerDigitsInput">Maximálně číslic před desetinnou čárkou ve výsledku</label>
          <input id="resultMaxIntegerDigitsInput" type="number" min="1" max="15" step="1">
        </div>
        <div class="settingField">
          <label for="resultMaxDecimalsInput">Maximálně desetinných míst ve výsledku</label>
          <input id="resultMaxDecimalsInput" type="number" min="0" max="20" step="1">
        </div>'''
assert old in text, 'old ZŠ controls not found'
text = text.replace(old, new, 1)

# 2) Per-mode defaults: on for ZŠ, off for SŠ.
old = '''  minJump:2,
  zsResultMaxIntegerDigits:7,
  zsResultMaxDecimals:6,
  prefixes:'''
new = '''  minJump:2,
  resultLimitsByMode:{
    zs:{enabled:true, maxIntegerDigits:7, maxDecimals:6},
    ss:{enabled:false, maxIntegerDigits:7, maxDecimals:6}
  },
  prefixes:'''
assert old in text, 'old result-limit defaults not found'
text = text.replace(old, new, 1)

# 3) Add a helper for current mode result limits.
old = '''function numberSettingsForMode(mode = settings.mode){
  if(!settings.numberSettingsByMode) settings.numberSettingsByMode = structuredClone(defaultSettings.numberSettingsByMode);
  if(!settings.numberSettingsByMode[mode]){
    settings.numberSettingsByMode[mode] = structuredClone(defaultSettings.numberSettingsByMode[mode] || defaultSettings.numberSettingsByMode.zs);
  }
  return settings.numberSettingsByMode[mode];
}
'''
new = old + '''
function resultLimitsForMode(mode = settings.mode){
  if(!settings.resultLimitsByMode) settings.resultLimitsByMode = structuredClone(defaultSettings.resultLimitsByMode);
  if(!settings.resultLimitsByMode[mode]){
    settings.resultLimitsByMode[mode] = structuredClone(defaultSettings.resultLimitsByMode[mode] || defaultSettings.resultLimitsByMode.zs);
  }
  return settings.resultLimitsByMode[mode];
}
'''
assert old in text, 'numberSettingsForMode anchor not found'
text = text.replace(old, new, 1)

# 4) Apply the current mode's limits only when enabled.
old = '''    const significantFigures = countVisibleSignificantFigures(x.visible);
    if(settings.mode === 'zs' && !zsResultFitsLimits(result, significantFigures)) continue;
    return {'''
new = '''    const significantFigures = countVisibleSignificantFigures(x.visible);
    const resultLimits = resultLimitsForMode();
    if(resultLimits.enabled && !resultFitsLimits(result, significantFigures, resultLimits)) continue;
    return {'''
assert old in text, 'makeExample limit check not found'
text = text.replace(old, new, 1)

# 5) Make the limit checker generic and driven by passed mode settings.
old = '''function zsResultFitsLimits(value, significantFigures){
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
}'''
new = '''function resultFitsLimits(value, significantFigures, limits = resultLimitsForMode()){
  const formatted = formatSignificantPlain(value, significantFigures)
    .replace(/\\u202f/g, '')
    .replace(/\\s/g, '');
  const unsigned = formatted.replace(/^[+-]/, '');
  const parts = unsigned.split(',');
  const integerPart = parts[0] || '0';
  const fractionPart = parts[1] || '';
  const maxIntegerDigits = clampInt(limits.maxIntegerDigits ?? 7, 1, 15);
  const maxDecimals = clampInt(limits.maxDecimals ?? 6, 0, 20);
  return integerPart.length <= maxIntegerDigits && fractionPart.length <= maxDecimals;
}'''
assert old in text, 'zsResultFitsLimits function not found'
text = text.replace(old, new, 1)

# 6) Summary reports on/off for whichever mode is active.
old = '''  const numberSettings = numberSettingsForMode();
  $('summary').innerHTML = `'''
new = '''  const numberSettings = numberSettingsForMode();
  const resultLimits = resultLimitsForMode();
  $('summary').innerHTML = `'''
assert old in text, 'summary preamble not found'
text = text.replace(old, new, 1)

old = '''    ${settings.mode === 'zs' ? `<span class="pill">výsledek: max ${settings.zsResultMaxIntegerDigits} číslic / ${settings.zsResultMaxDecimals} des. míst</span>` : ''}
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
new = '''    <span class="pill">${resultLimits.enabled ? `omezení výsledku: max ${resultLimits.maxIntegerDigits} číslic / ${resultLimits.maxDecimals} des. míst` : 'omezení výsledku vypnuto'}</span>
    <p class="small">Předpony: ${prefixText || 'žádné'}</p>'''
assert old in text, 'old summary result-limit pill not found'
text = text.replace(old, new, 1)

# 7) Fill controls from current mode and disable numeric inputs when limit is off.
old = '''function fillSettingsForm(){
  const numberSettings = numberSettingsForMode();'''
new = '''function fillSettingsForm(){
  const numberSettings = numberSettingsForMode();
  const resultLimits = resultLimitsForMode();'''
assert old in text, 'fillSettingsForm preamble not found'
text = text.replace(old, new, 1)

old = '''  $('largeDecimalsInput').value = settings.largeDecimals;
  $('jumpInput').value = settings.minJump;
  $('zsResultMaxIntegerDigitsInput').value = settings.zsResultMaxIntegerDigits ?? 7;
  $('zsResultMaxDecimalsInput').value = settings.zsResultMaxDecimals ?? 6;
  document.querySelectorAll('.zsResultLimit').forEach(el => {
    el.style.display = settings.mode === 'zs' ? 'flex' : 'none';
  });
  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
new = '''  $('largeDecimalsInput').value = settings.largeDecimals;
  $('jumpInput').value = settings.minJump;
  $('resultLimitEnabledInput').checked = Boolean(resultLimits.enabled);
  $('resultMaxIntegerDigitsInput').value = resultLimits.maxIntegerDigits ?? 7;
  $('resultMaxDecimalsInput').value = resultLimits.maxDecimals ?? 6;
  $('resultMaxIntegerDigitsInput').disabled = !resultLimits.enabled;
  $('resultMaxDecimalsInput').disabled = !resultLimits.enabled;
  $('niceInputRuleInput').checked = Boolean(numberSettings.niceInputByUnitSize);'''
assert old in text, 'old fillSettings result-limit block not found'
text = text.replace(old, new, 1)

# 8) Read controls back into the current mode only.
old = '''  settings.largeDecimals = clampInt($('largeDecimalsInput').value, 0, 8);
  settings.minJump = clampInt($('jumpInput').value, 1, 8);
  if(settings.mode === 'zs'){
    settings.zsResultMaxIntegerDigits = clampInt($('zsResultMaxIntegerDigitsInput').value, 1, 15);
    settings.zsResultMaxDecimals = clampInt($('zsResultMaxDecimalsInput').value, 0, 20);
  }
  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
new = '''  settings.largeDecimals = clampInt($('largeDecimalsInput').value, 0, 8);
  settings.minJump = clampInt($('jumpInput').value, 1, 8);
  const resultLimits = resultLimitsForMode();
  resultLimits.enabled = $('resultLimitEnabledInput').checked;
  resultLimits.maxIntegerDigits = clampInt($('resultMaxIntegerDigitsInput').value, 1, 15);
  resultLimits.maxDecimals = clampInt($('resultMaxDecimalsInput').value, 0, 20);
  numberSettings.niceInputByUnitSize = $('niceInputRuleInput').checked;'''
assert old in text, 'old applySettings result-limit block not found'
text = text.replace(old, new, 1)

# 9) Make enable/disable immediately visible in the settings dialog.
old = '''  $('applySettings').addEventListener('click', applySettingsFromForm);
  $('defaultsSettings').addEventListener('click', () => {'''
new = '''  $('applySettings').addEventListener('click', applySettingsFromForm);
  $('resultLimitEnabledInput').addEventListener('change', () => {
    const enabled = $('resultLimitEnabledInput').checked;
    $('resultMaxIntegerDigitsInput').disabled = !enabled;
    $('resultMaxDecimalsInput').disabled = !enabled;
  });
  $('defaultsSettings').addEventListener('click', () => {'''
assert old in text, 'wireEvents anchor not found'
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
