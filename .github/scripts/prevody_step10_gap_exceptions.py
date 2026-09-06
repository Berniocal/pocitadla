from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

text = text.replace("  minJump:2,", "  minJump:3,", 1)

old_ui = '''          <label for="jumpInput">Preferovaný minimální rozdíl velikosti jednotek</label>
          <select id="jumpInput">
            <option value="1">1 řád (alespoň 10×)</option>
            <option value="2">2 řády (alespoň 100×)</option>
            <option value="3">3 řády (alespoň 1 000×)</option>
            <option value="4">4 řády (alespoň 10 000×)</option>
            <option value="5">5 řádů (alespoň 100 000×)</option>
            <option value="6">6 řádů (alespoň 1 000 000×)</option>
          </select>
          <span class="small">Počítá se podle převodního poměru, ne podle počtu sousedních předpon. Např. 2 řády znamenají rozdíl alespoň 100×. Pokud taková dvojice u dané veličiny neexistuje, použije se nejvzdálenější dostupná.</span>'''
new_ui = '''          <label for="jumpInput">Preferovaný minimální rozdíl velikosti jednoduchých jednotek</label>
          <select id="jumpInput">
            <option value="1">1 řád (alespoň 10×)</option>
            <option value="2">2 řády (alespoň 100×)</option>
            <option value="3">3 řády (alespoň 1 000×)</option>
            <option value="4">4 řády (alespoň 10 000×)</option>
            <option value="5">5 řádů (alespoň 100 000×)</option>
            <option value="6">6 řádů (alespoň 1 000 000×)</option>
          </select>
          <span class="small">Výchozí jsou 3 řády = alespoň 1 000×. Toto pravidlo se nepoužívá pro složené jednotky ani pro čas. U času se naopak upřednostňují běžné dvojice den, h, min, s a ms; velmi malé jednotky se mohou objevit jen občas.</span>'''
if old_ui not in text:
    raise SystemExit('unit-gap UI block not found')
text = text.replace(old_ui, new_ui, 1)

old_choose = '''function chooseUnitPair(units){
  if(units.length < 2) return null;
  const compoundMode = compoundConversionMode();
  const candidates = [];

  for(let i=0; i<units.length; i++){
    for(let j=0; j<units.length; j++){
      if(i === j) continue;
      const from = units[i];
      const to = units[j];
      if(from.unit === to.unit) continue;
      if(Math.abs(from.factor - to.factor) <= Math.max(Math.abs(from.factor), Math.abs(to.factor), 1) * 1e-15) continue;

      const diffCount = compoundDifferenceCount(from, to);
      if(compoundMode && diffCount !== null){
        if(compoundMode === 'one' && diffCount !== 1) continue;
        if(compoundMode === 'both' && diffCount !== 2) continue;
      }

      const jump = Math.abs((from.order ?? Math.log10(Math.abs(from.factor))) - (to.order ?? Math.log10(Math.abs(to.factor))));
      candidates.push({from, to, jump});
    }
  }

  if(!candidates.length) return null;
  const minJump = clampInt(settings.minJump, 1, 6);
  const preferred = candidates.filter(pair => pair.jump + 1e-12 >= minJump);
  const pool = preferred.length
    ? preferred
    : (() => {
        const maxJump = Math.max(...candidates.map(pair => pair.jump));
        return candidates.filter(pair => Math.abs(pair.jump - maxJump) <= 1e-12);
      })();
  const chosen = randomChoice(pool);
  return chosen ? {from:chosen.from, to:chosen.to} : null;
}'''
new_choose = '''const commonTimeUnits = new Set(['den','h','min','s','ms']);

function isCommonTimePair(pair){
  return commonTimeUnits.has(pair.from.unit) && commonTimeUnits.has(pair.to.unit);
}

function chooseUnitPair(units, quantityId = null){
  if(units.length < 2) return null;
  const compoundMode = compoundConversionMode();
  const candidates = [];

  for(let i=0; i<units.length; i++){
    for(let j=0; j<units.length; j++){
      if(i === j) continue;
      const from = units[i];
      const to = units[j];
      if(from.unit === to.unit) continue;
      if(Math.abs(from.factor - to.factor) <= Math.max(Math.abs(from.factor), Math.abs(to.factor), 1) * 1e-15) continue;

      const diffCount = compoundDifferenceCount(from, to);
      if(compoundMode && diffCount !== null){
        if(compoundMode === 'one' && diffCount !== 1) continue;
        if(compoundMode === 'both' && diffCount !== 2) continue;
      }

      const jump = Math.abs((from.order ?? Math.log10(Math.abs(from.factor))) - (to.order ?? Math.log10(Math.abs(to.factor))));
      candidates.push({from, to, jump, compound:diffCount !== null});
    }
  }

  if(!candidates.length) return null;

  // Čas má vlastní logiku: většinu příkladů skládáme z běžných jednotek,
  // aby negeneroval hlavně dvojice typu ns ↔ ms. Velmi malé jednotky zůstávají možné.
  if(quantityId === 'cas'){
    const common = candidates.filter(isCommonTimePair);
    const pool = common.length && Math.random() < 0.85 ? common : candidates;
    const chosen = randomChoice(pool);
    return chosen ? {from:chosen.from, to:chosen.to} : null;
  }

  // U složených jednotek má přednost pedagogická volba „měnit jednu / obě části“.
  // Odstup v řádech proto aplikujeme jen na jednoduché jednotky.
  const hasCompoundUnits = candidates.some(pair => pair.compound);
  if(hasCompoundUnits){
    const chosen = randomChoice(candidates);
    return chosen ? {from:chosen.from, to:chosen.to} : null;
  }

  const minJump = clampInt(settings.minJump, 1, 6);
  const preferred = candidates.filter(pair => pair.jump + 1e-12 >= minJump);
  const pool = preferred.length
    ? preferred
    : (() => {
        const maxJump = Math.max(...candidates.map(pair => pair.jump));
        return candidates.filter(pair => Math.abs(pair.jump - maxJump) <= 1e-12);
      })();
  const chosen = randomChoice(pool);
  return chosen ? {from:chosen.from, to:chosen.to} : null;
}'''
if old_choose not in text:
    raise SystemExit('chooseUnitPair block not found')
text = text.replace(old_choose, new_choose, 1)

old_call = "    const pair = chooseUnitPair(units);"
new_call = "    const pair = chooseUnitPair(units, q.id);"
if old_call not in text:
    raise SystemExit('makeExample chooseUnitPair call not found')
text = text.replace(old_call, new_call, 1)

html_path.write_text(text, encoding='utf-8')

# Tests
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')

old_default_assert = "assert.equal(defaults.compoundConversionByMode.ss, 'both', 'Výchozí SŠ složené jednotky mají měnit obě části.');"
new_default_assert = old_default_assert + "\nassert.equal(defaults.minJump, 3, 'Výchozí odstup jednoduchých jednotek má být 3 řády.');"
if old_default_assert not in test:
    raise SystemExit('default assertion anchor not found')
test = test.replace(old_default_assert, new_default_assert, 1)

old_gap_comment = "// Ovladač odstupu znamená řády převodního poměru: 2 = alespoň 100×, ne dvě sousední předpony."
new_gap_comment = "// Ovladač odstupu znamená řády převodního poměru u jednoduchých jednotek: 2 = alespoň 100×."
test = test.replace(old_gap_comment, new_gap_comment, 1)

marker = "// Když požadovaný odstup v nabídce neexistuje, musí se použít opravdu nejvzdálenější dostupná dvojice."
addition = r'''// Složené jednotky odstup v řádech ignorují; rozhoduje volba změny jedné/obou částí.
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

// Čas odstup v řádech ignoruje a výrazně preferuje běžné jednotky den/h/min/s/ms.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  cfg.minJump = 6;
  api.setSettings(cfg);
  const time = quantityById('cas');
  const common = new Set(['den','h','min','s','ms']);
  let commonCount = 0;
  for(let i=0; i<1000; i++){
    const pair = api.chooseUnitPair(time.build('ss'), 'cas');
    assert(pair, 'Čas musí být generovatelný i při vysokém odstupu.');
    if(common.has(pair.from.unit) && common.has(pair.to.unit)) commonCount++;
  }
  assert(commonCount >= 700, `Běžné časové dvojice mají výrazně převažovat; bylo jich ${commonCount}/1000.`);
}

'''
if marker not in test:
    raise SystemExit('gap fallback marker not found')
test = test.replace(marker, addition + marker, 1)

test_path.write_text(test, encoding='utf-8')
