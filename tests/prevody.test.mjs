import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const html = fs.readFileSync('prevody.html', 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/);
assert(scriptMatch, 'Nepodařilo se najít hlavní <script> v prevody.html.');

let code = scriptMatch[1];
code = code.replace(/\nwireEvents\(\);\s*generateExamples\(\);\s*$/, '');
code += `\nglobalThis.__prevodyTestApi = {
  getDefaultSettings: () => structuredClone(defaultSettings),
  setSettings: value => { settings = structuredClone(value); },
  getSettings: () => settings,
  quantityMeta,
  makeExample,
  countVisibleSignificantFigures,
  resultFitsLimits
};`;

const sandbox = {
  console,
  Math,
  Number,
  Intl,
  structuredClone,
  Date,
  Set,
  Map,
  Array,
  Object,
  String,
  Boolean,
  RegExp,
  JSON,
  parseInt,
  parseFloat,
  isFinite,
  document: {
    getElementById(){ return null; },
    querySelectorAll(){ return []; },
    addEventListener(){}
  },
  navigator: {}
};

vm.createContext(sandbox);
vm.runInContext(code, sandbox, {filename:'prevody.inline.js'});
const api = sandbox.__prevodyTestApi;
assert(api, 'Testovací API generátoru nebylo vytvořeno.');

const superscriptDigits = {
  '⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9','⁻':'-'
};

function visibleNumberToNumber(visible){
  const compact = String(visible).replace(/\u202f/g, '').replace(/\s/g, '');
  const parts = compact.split('·10');
  const mantissa = Number(parts[0].replace(',', '.'));
  if(parts.length === 1) return mantissa;
  const exponent = Number([...parts[1]].map(ch => superscriptDigits[ch] ?? ch).join(''));
  return mantissa * Math.pow(10, exponent);
}

function nearlyEqual(a, b, rel = 1e-12){
  const scale = Math.max(1, Math.abs(a), Math.abs(b));
  return Math.abs(a - b) <= rel * scale;
}

function quantityById(id){
  const q = api.quantityMeta.find(item => item.id === id);
  assert(q, `Chybí veličina ${id}.`);
  return q;
}

function unitFactor(quantity, mode, unitName){
  const found = quantity.build(mode).find(u => u.unit === unitName);
  assert(found, `U veličiny ${quantity.id} chybí jednotka ${unitName}.`);
  return found.factor;
}

const defaults = api.getDefaultSettings();
const expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];
assert.equal(JSON.stringify(defaults.quantitiesByMode.zs), JSON.stringify(expectedDefaults), 'Výchozí ZŠ veličiny se změnily.');
assert.equal(JSON.stringify(defaults.quantitiesByMode.ss), JSON.stringify(expectedDefaults), 'Výchozí SŠ veličiny se změnily.');

for(const mode of ['zs','ss']){
  const cfg = structuredClone(defaults);
  cfg.mode = mode;
  api.setSettings(cfg);
  const energyPlus = quantityById('energieplus');
  const energyUnits = energyPlus.build(mode).map(u => u.unit);
  assert(!energyUnits.includes('cal'), 'Energie* nesmí obsahovat cal.');
  assert(!energyUnits.includes('kcal'), 'Energie* nesmí obsahovat kcal.');
}

let generated = 0;

for(const mode of ['zs','ss']){
  const cfg = structuredClone(defaults);
  cfg.mode = mode;
  api.setSettings(cfg);
  const range = cfg.numberSettingsByMode[mode];

  for(const quantityId of expectedDefaults){
    const q = quantityById(quantityId);
    for(let i = 0; i < 250; i++){
      const useExp = mode === 'ss' && (i % 2 === 1);
      const ex = api.makeExample(i + 1, q, useExp);
      assert(ex, `Nepodařilo se vytvořit ${quantityId} (${mode}) při výchozím nastavení.`);
      assert.equal(ex.quantityId, quantityId, `Povinná veličina ${quantityId} byla nahrazena za ${ex.quantityId}.`);

      const input = visibleNumberToNumber(ex.value);
      assert(Number.isFinite(input) && input > 0, `Neplatné číslo v zadání: ${ex.value}`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Zadání má více než dvě platné číslice: ${ex.value}.`);
      if(mode === 'ss' && ex.exponentialInput){
        assert(input >= 1e-10 - 1e-24, `Exponenciální zadání ${ex.value} je pod 10^-10.`);
        assert(input <= 1e10 + 1e-2, `Exponenciální zadání ${ex.value} je nad 10^10.`);
      }else{
        assert(input >= range.minNumber - 1e-12, `Zadání ${ex.value} je pod minimem ${range.minNumber} (${quantityId}, ${mode}).`);
        assert(input <= range.maxNumber + 1e-12, `Zadání ${ex.value} překročilo maximum ${range.maxNumber} (${quantityId}, ${mode}).`);
      }

      const fromFactor = unitFactor(q, mode, ex.from);
      const toFactor = unitFactor(q, mode, ex.to);
      const expectedResult = input * fromFactor / toFactor;
      assert(nearlyEqual(ex.result, expectedResult), `Výsledek se nepočítá z viditelného zadání: ${ex.value} ${ex.from} -> ${ex.to}.`);

      assert.equal(ex.significantFigures, api.countVisibleSignificantFigures(ex.value), `Nesedí počet platných číslic u ${ex.value}.`);
      if(cfg.resultLimitsByMode[mode].enabled){
        assert(api.resultFitsLimits(ex.result, ex.significantFigures, cfg.resultLimitsByMode[mode]), `Výsledek porušuje aktivní limit délky (${quantityId}, ${mode}).`);
      }
      generated++;
    }
  }
}

// Každá aktuálně dostupná veličina musí být samostatně generovatelná a nesmí se změnit na jinou.
for(const mode of ['zs','ss']){
  const cfg = structuredClone(defaults);
  cfg.mode = mode;
  cfg.resultLimitsByMode[mode].enabled = false;
  cfg.minJump = 1;
  api.setSettings(cfg);

  for(const q of api.quantityMeta.filter(item => item.modes.includes(mode))){
    for(let i = 0; i < 50; i++){
      const ex = api.makeExample(i + 1, q, mode === 'ss' && (i % 2 === 1));
      assert(ex, `Veličina ${q.id} (${mode}) není generovatelná ani po opakovaných pokusech.`);
      assert.equal(ex.quantityId, q.id, `Veličina ${q.id} (${mode}) byla nahrazena za ${ex.quantityId}.`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Veličina ${q.id} (${mode}) vygenerovala více než dvě platné číslice: ${ex.value}.`);
      generated++;
    }
  }
}

console.log(`OK: ${generated} náhodně vygenerovaných příkladů prošlo kontrolami.`);
console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, min/max jen pro běžná zadání, exp. rozsah 10^-10 až 10^10, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');
