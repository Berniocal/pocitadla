from pathlib import Path

p = Path('prevody.html')
s = p.read_text(encoding='utf-8')

def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit('Missing expected snippet: ' + old[:180].replace('\n','\\n'))
    s = s.replace(old, new, count)

# UI toggle for input-number limits.
rep(
'''        <div class="settingField">
          <label for="minNumberInput">Nejmenší číslo v zadání</label>
          <input id="minNumberInput" type="number" min="0" step="any">
        </div>''',
'''        <div class="settingField">
          <label class="check">
            <input id="numberLimitEnabledInput" type="checkbox">
            <span>Omezit nejmenší a největší číslo v zadání</span>
          </label>
        </div>
        <div class="settingField">
          <label for="minNumberInput">Nejmenší číslo v zadání</label>
          <input id="minNumberInput" type="number" min="0" step="any">
        </div>'''
)

# Defaults: ZS retains old behavior, SS follows physical profiles / broad fallback.
rep(
'''    zs:{minNumber:0.1, maxNumber:100, niceInputByUnitSize:true},
    ss:{minNumber:0.01, maxNumber:9999, niceInputByUnitSize:false}''',
'''    zs:{inputLimitEnabled:true, minNumber:0.1, maxNumber:100, niceInputByUnitSize:true},
    ss:{inputLimitEnabled:false, minNumber:0.01, maxNumber:9999, niceInputByUnitSize:false}'''
)

# Default exponential mode only for the four quantities shown by the user.
start = s.index("  expQuantitiesSS:[")
end = s.index("],\n  prefixes:", start) + 1
s = s[:start] + "  expQuantitiesSS:['delka','hmotnost','sila','energie']" + s[end:]

# Generic number range: when SS global input limits are off, do not constrain by min/max.
rep(
'''function numberRange(pair = null){
  const numberSettings = numberSettingsForMode();
  let min = positiveNumber(numberSettings.minNumber, 0.01);
  let max = positiveNumber(numberSettings.maxNumber, 9999);
  if(min > max) [min, max] = [max, min];''',
'''function numberRange(pair = null){
  const numberSettings = numberSettingsForMode();
  if(numberSettings.inputLimitEnabled === false){
    // U SŠ bez globálního omezení mají přednost fyzikální profily jednotlivých veličin.
    // Široké veličiny bez profilu dostanou pouze technický rozsah, aby generátor zůstal numericky stabilní.
    return settings.mode === 'ss' ? {min:1e-10, max:1e10} : {min:0.1, max:100};
  }
  let min = positiveNumber(numberSettings.minNumber, 0.01);
  let max = positiveNumber(numberSettings.maxNumber, 9999);
  if(min > max) [min, max] = [max, min];'''
)

# Summary shows whether the input-number limit is active.
rep(
'''    <span class="pill">${formatPlainNumber(numberSettings.minNumber)} až ${formatPlainNumber(numberSettings.maxNumber)}</span>''',
'''    <span class="pill">${numberSettings.inputLimitEnabled === false ? 'omezení čísla v zadání vypnuto' : `${formatPlainNumber(numberSettings.minNumber)} až ${formatPlainNumber(numberSettings.maxNumber)}`}</span>'''
)

# Fill settings form and disable min/max when off.
rep(
'''  $('countInput').value = settings.count;
  $('minNumberInput').value = numberSettings.minNumber;
  $('maxNumberInput').value = numberSettings.maxNumber;''',
'''  $('countInput').value = settings.count;
  if(typeof numberSettings.inputLimitEnabled !== 'boolean'){
    numberSettings.inputLimitEnabled = settings.mode === 'zs';
  }
  $('numberLimitEnabledInput').checked = numberSettings.inputLimitEnabled;
  $('minNumberInput').value = numberSettings.minNumber;
  $('maxNumberInput').value = numberSettings.maxNumber;
  $('minNumberInput').disabled = !numberSettings.inputLimitEnabled;
  $('maxNumberInput').disabled = !numberSettings.inputLimitEnabled;'''
)

# Store checkbox setting.
rep(
'''  const numberSettings = numberSettingsForMode();
  numberSettings.minNumber = positiveNumber($('minNumberInput').value, 0.01);''',
'''  const numberSettings = numberSettingsForMode();
  numberSettings.inputLimitEnabled = $('numberLimitEnabledInput').checked;
  numberSettings.minNumber = positiveNumber($('minNumberInput').value, 0.01);'''
)

# Event listener for input-number limit toggle.
rep(
'''  $('applySettings').addEventListener('click', applySettingsFromForm);
  $('resultLimitEnabledInput').addEventListener('change', () => {''',
'''  $('applySettings').addEventListener('click', applySettingsFromForm);
  $('numberLimitEnabledInput').addEventListener('change', () => {
    const enabled = $('numberLimitEnabledInput').checked;
    $('minNumberInput').disabled = !enabled;
    $('maxNumberInput').disabled = !enabled;
  });
  $('resultLimitEnabledInput').addEventListener('change', () => {'''
)

p.write_text(s, encoding='utf-8')
