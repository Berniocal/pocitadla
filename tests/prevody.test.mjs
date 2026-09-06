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
  resultFitsLimits,
  usesExponentialForQuantity,
  formatExponentialText,
  numberRange,
  resultTextsForExample,
  physicalValueFitsProfile,
  compoundDifferenceCount,
  chooseUnitPair,
  resultNeedsTenths,
  formattedResultForPair
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

function visibleExponent(visible){
  const compact = String(visible).replace(/\u202f/g, '').replace(/\s/g, '');
  const parts = compact.split('·10');
  if(parts.length === 1) return 0;
  return Number([...parts[1]].map(ch => superscriptDigits[ch] ?? ch).join(''));
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

// Exponent 0 se nesmí zobrazovat jako zbytečné ·10⁰.
assert.equal(api.formatExponentialText('3,5', 0), '3,5', 'Exponent 0 se má zobrazit běžně.');
assert.equal(api.formatExponentialText('3.5', 0), '3,5', 'Exponent 0 musí používat desetinnou čárku.');
assert.equal(api.formatExponentialText('3.5', -10), '3,5·10⁻¹⁰', 'Dolní okraj exp. rozsahu se formátuje chybně.');
assert.equal(api.formatExponentialText('9.6', 10), '9,6·10¹⁰', 'Horní okraj exp. rozsahu se formátuje chybně.');

const ssRangeCfg = structuredClone(defaults);
ssRangeCfg.mode = 'ss';
api.setSettings(ssRangeCfg);
const ssExpRange = api.numberRange(null, true);
assert.equal(ssExpRange.min, 1e-10, 'SŠ exp. rozsah má začínat na 10^-10.');
assert.equal(ssExpRange.max, 1e10, 'SŠ exp. rozsah má končit na 10^10.');

const dualResultProbe = {resultPlain:'12 000', resultExp:'1,2·10⁴'};
assert.deepEqual(
  JSON.parse(JSON.stringify(api.resultTextsForExample(dualResultProbe, 'ss'))),
  {plain:'12 000', exponential:'1,2·10⁴'},
  'Na SŠ musí být dostupný běžný i exponenciální výsledek.'
);
assert.deepEqual(
  JSON.parse(JSON.stringify(api.resultTextsForExample(dualResultProbe, 'zs'))),
  {plain:'12 000', exponential:null},
  'Na ZŠ se má zobrazovat jen běžný výsledek.'
);

const expectedDefaults = ['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'];
assert.equal(JSON.stringify(defaults.quantitiesByMode.zs), JSON.stringify(expectedDefaults), 'Výchozí ZŠ veličiny se změnily.');
assert.equal(JSON.stringify(defaults.quantitiesByMode.ss), JSON.stringify(expectedDefaults), 'Výchozí SŠ veličiny se změnily.');
assert.equal(JSON.stringify(defaults.exponentialQuantitiesByMode.ss), JSON.stringify(['delka','hmotnost','sila','energie']), 'Výchozí SŠ exp. veličiny se změnily.');
assert.equal(defaults.compoundConversionByMode.ss, 'both', 'Výchozí SŠ složené jednotky mají měnit obě části.');
assert.equal(defaults.minJump, 3, 'Výchozí odstup jednoduchých jednotek má být 3 řády.');
assert.equal(defaults.numberSettingsByMode.ss.niceInputByUnitSize, true, 'SŠ má mít výchozí hezčí zadání zapnuté.');
assert.equal(defaults.resultLimitsByMode.ss.enabled, true, 'SŠ má mít výchozí omezení délky výsledku zapnuté.');

for(const mode of ['zs','ss']){
  const cfg = structuredClone(defaults);
  cfg.mode = mode;
  api.setSettings(cfg);
  const energyPlus = quantityById('energieplus');
  const energyUnits = energyPlus.build(mode).map(u => u.unit);
  assert(!energyUnits.includes('cal'), 'Energie* nesmí obsahovat cal.');
  assert(!energyUnits.includes('kcal'), 'Energie* nesmí obsahovat kcal.');
}


{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  api.setSettings(cfg);
  for(const q of api.quantityMeta.filter(item => item.modes.includes('ss'))){
    const shouldExp = ['delka','hmotnost','sila','energie'].includes(q.id);
    assert.equal(api.usesExponentialForQuantity(q.id), shouldExp, `Chybné výchozí exp. nastavení pro ${q.id}.`);
    const ex = api.makeExample(1, q, shouldExp);
    assert(ex, `Nelze vytvořit kontrolní SŠ příklad pro ${q.id}.`);
    assert.equal(ex.exponentialFormat, shouldExp, `Výsledek ${q.id} nemá správný exp. režim.`);
    assert.equal(ex.exponentialInput, shouldExp, `Zadání ${q.id} nemá správný exp. režim.`);
  }
}

// Ovladač odstupu znamená řády převodního poměru u jednoduchých jednotek: 2 = alespoň 100×.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 2;
  cfg.compoundConversionByMode.ss = 'both';
  api.setSettings(cfg);
  const synthetic = [
    {unit:'u0', factor:1, order:0, parts:null},
    {unit:'u1', factor:10, order:1, parts:null},
    {unit:'u2', factor:100, order:2, parts:null},
    {unit:'u3', factor:1000, order:3, parts:null}
  ];
  for(let i=0; i<100; i++){
    const pair = api.chooseUnitPair(synthetic);
    assert(pair, 'Nelze vybrat kontrolní dvojici jednotek.');
    const ratio = Math.max(pair.from.factor, pair.to.factor) / Math.min(pair.from.factor, pair.to.factor);
    assert(ratio >= 100 - 1e-12, `Při minJump=2 musí být preferovaná dvojice alespoň 100× od sebe, ale je ${ratio}×.`);
  }
}

// Složené jednotky odstup v řádech ignorují; rozhoduje volba změny jedné/obou částí.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 6;
  cfg.compoundConversionByMode.ss = 'both';
  api.setSettings(cfg);
  const speed = quantityById('rychlost');
  for(let i=0; i<50; i++){
    const pair = api.chooseUnitPair(speed.build('ss'), 'rychlost');
    assert(pair, 'Složená rychlost nesmí být zablokována vysokým odstupem v řádech.');
  }
}

// Čas odstup v řádech ignoruje, nepoužívá sousední jednotky a výrazně preferuje den/h/min/s/ms.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 6;
  api.setSettings(cfg);
  const time = quantityById('cas');
  const common = new Set(['den','h','min','s','ms']);
  const order = ['den','h','min','s','ms','µs','ns','ps','fs'];
  let commonCount = 0;
  for(let i=0; i<1000; i++){
    const pair = api.chooseUnitPair(time.build('ss'), 'cas');
    assert(pair, 'Čas musí být generovatelný i při vysokém odstupu.');
    const distance = Math.abs(order.indexOf(pair.from.unit) - order.indexOf(pair.to.unit));
    assert(distance !== 1, `Čas nesmí použít sousední jednotky: ${pair.from.unit} → ${pair.to.unit}.`);
    if(common.has(pair.from.unit) && common.has(pair.to.unit)) commonCount++;
  }
  assert(commonCount >= 700, `Běžné časové dvojice mají výrazně převažovat; bylo jich ${commonCount}/1000.`);
}

// Když požadovaný odstup v nabídce neexistuje, musí se použít opravdu nejvzdálenější dostupná dvojice.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 6;
  api.setSettings(cfg);
  const synthetic = [
    {unit:'u0', factor:1, order:0, parts:null},
    {unit:'u1', factor:10, order:1, parts:null},
    {unit:'u2', factor:100, order:2, parts:null}
  ];
  for(let i=0; i<50; i++){
    const pair = api.chooseUnitPair(synthetic);
    const ratio = Math.max(pair.from.factor, pair.to.factor) / Math.min(pair.from.factor, pair.to.factor);
    assert.equal(ratio, 100, 'Fallback má použít nejvzdálenější dostupnou dvojici.');
  }
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
      const fromFactorPhysical = unitFactor(q, mode, ex.from);
      const siValue = input * fromFactorPhysical;
      assert(api.physicalValueFitsProfile(quantityId, siValue, mode), `Fyzikální hodnota mimo profil: ${ex.value} ${ex.from} (${quantityId}, ${mode}).`);
      if(quantityId === 'rychlost') assert(siValue >= 3 - 1e-12 && siValue <= 45 + 1e-12, `Rychlost není cyklistická/automobilní: ${siValue} m/s.`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Zadání má více než dvě platné číslice: ${ex.value}.`);
      if(mode === 'ss' && ex.exponentialInput){
        assert(input >= 1e-10 - 1e-24, `Exponenciální zadání ${ex.value} je pod 10^-10.`);
        assert(input <= 1e10 + 1e-2, `Exponenciální zadání ${ex.value} je nad 10^10.`);
        const fromFactorForSign = unitFactor(q, mode, ex.from);
        const toFactorForSign = unitFactor(q, mode, ex.to);
        const exponent = visibleExponent(ex.value);
        if(fromFactorForSign < toFactorForSign){
          assert(exponent > 0, `Při převodu z menší jednotky ${ex.from} na větší ${ex.to} musí být exponent kladný, ale je ${ex.value}.`);
        }else if(fromFactorForSign > toFactorForSign){
          assert(exponent < 0, `Při převodu z větší jednotky ${ex.from} na menší ${ex.to} musí být exponent záporný, ale je ${ex.value}.`);
        }
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
      if(mode === 'ss' && ex.exponentialInput){
        const fromFactorForSign = unitFactor(q, mode, ex.from);
        const toFactorForSign = unitFactor(q, mode, ex.to);
        const exponent = visibleExponent(ex.value);
        if(fromFactorForSign < toFactorForSign) assert(exponent > 0, `${q.id}: menší → větší musí mít kladný exponent (${ex.value}).`);
        if(fromFactorForSign > toFactorForSign) assert(exponent < 0, `${q.id}: větší → menší musí mít záporný exponent (${ex.value}).`);
      }
      generated++;
    }
  }
}

// SŠ: u složených jednotek musí jít vynutit změnu obou částí i jen jedné části.
for(const compoundMode of ['both','one']){
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.compoundConversionByMode.ss = compoundMode;
  cfg.resultLimitsByMode.ss.enabled = false;
  cfg.minJump = 1;
  api.setSettings(cfg);
  for(const quantityId of ['rychlost','hustota','zrychleni']){
    const q = quantityById(quantityId);
    for(let i=0; i<120; i++){
      const ex = api.makeExample(i + 1, q, false);
      assert(ex, `${quantityId}: nelze vytvořit SŠ složený převod v režimu ${compoundMode}.`);
      const fromUnit = q.build('ss').find(u => u.unit === ex.from);
      const toUnit = q.build('ss').find(u => u.unit === ex.to);
      const diff = api.compoundDifferenceCount(fromUnit, toUnit);
      assert.equal(diff, compoundMode === 'one' ? 1 : 2, `${quantityId}: režim ${compoundMode} změnil ${diff} částí (${ex.from} → ${ex.to}).`);
      generated++;
    }
  }
}

// Rychlost na SŠ musí umět při režimu „jen jednu část“ změnit zvlášť jmenovatel i čitatel.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.compoundConversionByMode.ss = 'one';
  api.setSettings(cfg);
  const speedUnits = quantityById('rychlost').build('ss');
  const byName = name => speedUnits.find(u => u.unit === name);
  const mPerS = byName('m/s');
  const mPerMin = byName('m/min');
  const kmPerMin = byName('km/min');
  assert(mPerS && mPerMin && kmPerMin, 'SŠ rychlost musí obsahovat m/s, m/min a km/min.');
  assert.equal(api.compoundDifferenceCount(mPerS, mPerMin), 1, 'm/s → m/min má měnit jen jmenovatel.');
  assert.equal(api.compoundDifferenceCount(mPerMin, kmPerMin), 1, 'm/min → km/min má měnit jen čitatel.');
  assert(nearlyEqual(kmPerMin.factor, 1000 / 60), 'km/min má chybný převodní faktor.');
}

// Při dělení 3,6 nebo 60 se běžný výsledek zaokrouhlí alespoň na desetiny.
{
  const speedUnits = quantityById('rychlost').build('ss');
  const byName = name => speedUnits.find(u => u.unit === name);
  const kmhToMs = {from:byName('km/h'), to:byName('m/s')};
  const mminToMs = {from:byName('m/min'), to:byName('m/s')};
  assert(api.resultNeedsTenths(kmhToMs), 'km/h → m/s musí používat desetiny (dělení 3,6).');
  assert(api.resultNeedsTenths(mminToMs), 'm/min → m/s musí používat desetiny (dělení 60).');
  assert.equal(api.formattedResultForPair(100 / 3.6, 1, kmhToMs).plain, '27,8', '100 km/h → m/s má být 27,8 m/s.');
  assert.equal(api.formattedResultForPair(900 / 60, 1, mminToMs).plain, '15,0', '900 m/min → m/s má být 15,0 m/s.');
}

// Elektrický náboj nesmí používat absurdně velké předpony.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  api.setSettings(cfg);
  const chargeUnits = quantityById('naboj').build('ss').map(u => u.unit);
  for(const forbidden of ['kC','MC','GC','TC','PC']) assert(!chargeUnits.includes(forbidden), `Náboj nesmí obsahovat ${forbidden}.`);
}

console.log(`OK: ${generated} náhodně vygenerovaných příkladů prošlo kontrolami.`);
console.log('Kontrolováno: povinná veličina, realistické SI profily, rychlost 3–45 m/s, max. 2 platné číslice, SŠ složené jednotky jedna/obě části, exp. tvar zadání po veličinách, dva výsledky na SŠ (běžný + exp.), znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku, rozumné jednotky náboje a Energie* bez kalorií.');
