from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

# Small regenerate button styling.
old_css = ".exampleTop{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}\n.task{font-size:22px;font-weight:780;line-height:1.3}"
new_css = ".exampleTop{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}\n.exampleActions{display:flex;align-items:center;gap:6px}\n.regenBtn{width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;font-size:18px;line-height:1;color:var(--ink);padding:0}\n.regenBtn:hover{background:#fff8e8;border-color:var(--accent)}\n.task{font-size:22px;font-weight:780;line-height:1.3}"
if old_css not in text:
    raise SystemExit('exampleTop CSS anchor not found')
text = text.replace(old_css, new_css, 1)

# Exponential input: absolute exponent at least 3.
text = text.replace("    allowedMinExp = Math.max(1, minExp);", "    allowedMinExp = Math.max(3, minExp);", 1)
text = text.replace("    allowedMaxExp = Math.min(-1, maxExp);", "    allowedMaxExp = Math.min(-3, maxExp);", 1)
old_neutral = """    if(!fromIsSmaller && !fromIsLarger && exponent === 0){
      exponent = maxExp >= 1 ? 1 : (minExp <= -1 ? -1 : 0);
    }"""
new_neutral = """    if(!fromIsSmaller && !fromIsLarger && Math.abs(exponent) < 3){
      if(maxExp >= 3 && minExp <= -3){
        exponent = Math.random() < 0.5 ? randomInt(3, maxExp) : randomInt(minExp, -3);
      }else if(maxExp >= 3){
        exponent = randomInt(3, maxExp);
      }else if(minExp <= -3){
        exponent = randomInt(minExp, -3);
      }else{
        return randomPlainNumber(range);
      }
    }"""
if old_neutral not in text:
    raise SystemExit('neutral exponent block not found')
text = text.replace(old_neutral, new_neutral, 1)

old_visible = """    const exponent = Math.floor(Math.log10(rounded));
    if(exponent < -10 || exponent > 10) return null;
    if(pair.from.factor < pair.to.factor && exponent <= 0) return null;
    if(pair.from.factor > pair.to.factor && exponent >= 0) return null;"""
new_visible = """    const exponent = Math.floor(Math.log10(rounded));
    if(exponent < -10 || exponent > 10) return null;
    if(Math.abs(exponent) < 3) return null;
    if(pair.from.factor < pair.to.factor && exponent < 3) return null;
    if(pair.from.factor > pair.to.factor && exponent > -3) return null;"""
if old_visible not in text:
    raise SystemExit('visible exponent validation block not found')
text = text.replace(old_visible, new_visible, 1)

# Pure replacement helper + UI wrapper. Same quantity, same current exp preference.
anchor = """function generateExamples(){
  const quantities = selectedQuantities();"""
insert = """function replacementExampleFor(ex){
  if(!ex) return null;
  const q = quantityMeta.find(item => item.id === ex.quantityId && item.modes.includes(settings.mode));
  if(!q) return null;
  return makeExample(ex.index, q, usesExponentialForQuantity(q.id));
}

function regenerateExampleAt(index){
  const position = examples.findIndex(ex => ex.index === index);
  if(position < 0) return false;
  const oldExample = examples[position];
  const replacement = replacementExampleFor(oldExample);
  if(!replacement){
    $('copyState').textContent = `Příklad ${index} se nepodařilo přegenerovat bez porušení nastavení.`;
    return false;
  }
  examples[position] = replacement;
  generationFailures = generationFailures.filter(name => name !== oldExample.quantity);
  $('copyState').textContent = `Příklad ${index} byl přegenerován.`;
  renderExamples();
  return true;
}

function generateExamples(){
  const quantities = selectedQuantities();"""
if anchor not in text:
    raise SystemExit('generateExamples anchor not found')
text = text.replace(anchor, insert, 1)

# Per-example button in top-right action area.
old_top = """        <div class=\"exampleTop\">
          <span class=\"pill good\">${ex.index}. ${ex.quantity}</span>
          <span class=\"pill\">${settings.mode === 'ss' ? 'SŠ' : 'ZŠ'}</span>
        </div>"""
new_top = """        <div class=\"exampleTop\">
          <span class=\"pill good\">${ex.index}. ${ex.quantity}</span>
          <span class=\"exampleActions\">
            <span class=\"pill\">${settings.mode === 'ss' ? 'SŠ' : 'ZŠ'}</span>
            <button type=\"button\" class=\"regenBtn\" data-regenerate-index=\"${ex.index}\" title=\"Přegenerovat tento příklad stejné veličiny\" aria-label=\"Přegenerovat příklad ${ex.index}\">↻</button>
          </span>
        </div>"""
if old_top not in text:
    raise SystemExit('exampleTop markup not found')
text = text.replace(old_top, new_top, 1)

old_status = "SŠ režim: exponenciální tvar zadání se nastavuje samostatně u každé veličiny. Výsledek se vždy zobrazí dvakrát – běžně i v exponenciálním tvaru. V zadání je při převodu z menší jednotky na větší exponent kladný, opačným směrem záporný."
new_status = "SŠ režim: exponenciální tvar zadání se nastavuje samostatně u každé veličiny. V exponenciálním zadání má mocnina absolutní hodnotu alespoň 3. Výsledek se vždy zobrazí dvakrát – běžně i v exponenciálním tvaru. Při převodu z menší jednotky na větší je exponent alespoň +3, opačným směrem nejvýše −3."
if old_status not in text:
    raise SystemExit('status text not found')
text = text.replace(old_status, new_status, 1)

# Delegated click handler survives rerenders.
old_wire = """function wireEvents(){
  $('generateBtn').addEventListener('click', generateExamples);"""
new_wire = """function wireEvents(){
  $('generateBtn').addEventListener('click', generateExamples);
  $('examples').addEventListener('click', event => {
    const button = event.target.closest('[data-regenerate-index]');
    if(!button) return;
    regenerateExampleAt(Number(button.dataset.regenerateIndex));
  });"""
if old_wire not in text:
    raise SystemExit('wireEvents anchor not found')
text = text.replace(old_wire, new_wire, 1)

html_path.write_text(text, encoding='utf-8')

# Tests.
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')
old_api = """  resultNeedsTenths,
  formattedResultForPair
};"""
new_api = """  resultNeedsTenths,
  formattedResultForPair,
  replacementExampleFor
};"""
if old_api not in test:
    raise SystemExit('test API anchor not found')
test = test.replace(old_api, new_api, 1)

# Require |exponent| >= 3 in both randomized exp checks.
old_dir1 = """        const exponent = visibleExponent(ex.value);
        if(fromFactorForSign < toFactorForSign){
          assert(exponent > 0, `Při převodu z menší jednotky ${ex.from} na větší ${ex.to} musí být exponent kladný, ale je ${ex.value}.`);
        }else if(fromFactorForSign > toFactorForSign){
          assert(exponent < 0, `Při převodu z větší jednotky ${ex.from} na menší ${ex.to} musí být exponent záporný, ale je ${ex.value}.`);
        }"""
new_dir1 = """        const exponent = visibleExponent(ex.value);
        assert(Math.abs(exponent) >= 3, `Exponenciální zadání musí mít |exponent| alespoň 3, ale je ${ex.value}.`);
        if(fromFactorForSign < toFactorForSign){
          assert(exponent >= 3, `Při převodu z menší jednotky ${ex.from} na větší ${ex.to} musí být exponent alespoň +3, ale je ${ex.value}.`);
        }else if(fromFactorForSign > toFactorForSign){
          assert(exponent <= -3, `Při převodu z větší jednotky ${ex.from} na menší ${ex.to} musí být exponent nejvýše -3, ale je ${ex.value}.`);
        }"""
if old_dir1 not in test:
    raise SystemExit('first exponent direction test block not found')
test = test.replace(old_dir1, new_dir1, 1)

old_dir2 = """        const exponent = visibleExponent(ex.value);
        if(fromFactorForSign < toFactorForSign) assert(exponent > 0, `${q.id}: menší → větší musí mít kladný exponent (${ex.value}).`);
        if(fromFactorForSign > toFactorForSign) assert(exponent < 0, `${q.id}: větší → menší musí mít záporný exponent (${ex.value}).`);"""
new_dir2 = """        const exponent = visibleExponent(ex.value);
        assert(Math.abs(exponent) >= 3, `${q.id}: exp. zadání musí mít |exponent| alespoň 3 (${ex.value}).`);
        if(fromFactorForSign < toFactorForSign) assert(exponent >= 3, `${q.id}: menší → větší musí mít exponent alespoň +3 (${ex.value}).`);
        if(fromFactorForSign > toFactorForSign) assert(exponent <= -3, `${q.id}: větší → menší musí mít exponent nejvýše -3 (${ex.value}).`);"""
if old_dir2 not in test:
    raise SystemExit('second exponent direction test block not found')
test = test.replace(old_dir2, new_dir2, 1)

# Replacement helper must keep quantity, index and exp preference.
anchor_test = """// Ovladač odstupu znamená řády převodního poměru u jednoduchých jednotek: 2 = alespoň 100×.
{"""
insert_test = """// Přegenerování jednoho příkladu musí zachovat jeho veličinu, pořadové číslo a aktuální exp. režim veličiny.
{
  const cfg = structuredClone(defaults);
  cfg.mode = 'ss';
  api.setSettings(cfg);
  const q = quantityById('delka');
  const original = api.makeExample(7, q, true);
  assert(original, 'Nelze vytvořit výchozí příklad pro test přegenerování.');
  const replacement = api.replacementExampleFor(original);
  assert(replacement, 'Přegenerování jednoho příkladu selhalo.');
  assert.equal(replacement.index, 7, 'Přegenerování musí zachovat pořadové číslo.');
  assert.equal(replacement.quantityId, 'delka', 'Přegenerování musí zachovat veličinu.');
  assert.equal(replacement.exponentialInput, true, 'Přegenerování musí zachovat aktuální exp. režim veličiny.');
  assert(Math.abs(visibleExponent(replacement.value)) >= 3, 'Přegenerovaný exp. příklad musí mít |exponent| alespoň 3.');
}

"""
if anchor_test not in test:
    raise SystemExit('replacement test anchor not found')
test = test.replace(anchor_test, insert_test + anchor_test, 1)

test = test.replace('znaménko exponentu podle směru převodu, bez zbytečného 10^0', 'znaménko exponentu podle směru převodu a |exponent| ≥ 3, bez zbytečného 10^0', 1)
test_path.write_text(test, encoding='utf-8')
