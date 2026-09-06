from pathlib import Path

html_path = Path('prevody.html')
test_path = Path('tests/prevody.test.mjs')
text = html_path.read_text(encoding='utf-8')
test = test_path.read_text(encoding='utf-8')

old = '''function randomVisibleNumber(useExponential = false, pair = null){
  const range = numberRange(pair, useExponential);
  return useExponential ? randomExponentialNumber(range) : randomPlainNumber(range);
}'''
new = '''function randomVisibleNumber(useExponential = false, pair = null){
  const range = numberRange(pair, useExponential);
  return useExponential ? randomExponentialNumber(range, pair) : randomPlainNumber(range);
}'''
if old not in text:
    raise SystemExit('randomVisibleNumber anchor not found')
text = text.replace(old, new, 1)

old = '''function randomExponentialNumber(range){
  const minExp = Math.floor(Math.log10(range.min));
  const maxExp = Math.floor(Math.log10(range.max));
  for(let attempt=0; attempt<400; attempt++){
    const exponent = randomInt(minExp, maxExp);
    const lowMantissa = exponent === minExp ? range.min / Math.pow(10, exponent) : 1;
    const highMantissa = exponent === maxExp ? range.max / Math.pow(10, exponent) : 9.99;'''
new = '''function randomExponentialNumber(range, pair = null){
  const minExp = Math.floor(Math.log10(range.min));
  const maxExp = Math.floor(Math.log10(range.max));
  const fromIsSmaller = Boolean(pair && pair.from.factor < pair.to.factor);
  const fromIsLarger = Boolean(pair && pair.from.factor > pair.to.factor);
  let allowedMinExp = minExp;
  let allowedMaxExp = maxExp;
  if(fromIsSmaller){
    allowedMinExp = Math.max(1, minExp);
  }else if(fromIsLarger){
    allowedMaxExp = Math.min(-1, maxExp);
  }
  if(allowedMinExp > allowedMaxExp) return randomPlainNumber(range);

  for(let attempt=0; attempt<400; attempt++){
    let exponent = randomInt(allowedMinExp, allowedMaxExp);
    if(!fromIsSmaller && !fromIsLarger && exponent === 0){
      exponent = maxExp >= 1 ? 1 : (minExp <= -1 ? -1 : 0);
    }
    const lowMantissa = exponent === minExp ? range.min / Math.pow(10, exponent) : 1;
    const highMantissa = exponent === maxExp ? range.max / Math.pow(10, exponent) : 9.99;'''
if old not in text:
    raise SystemExit('randomExponentialNumber anchor not found')
text = text.replace(old, new, 1)

# Add a short UI explanation in SŠ mode metadata.
old = "    : 'SŠ režim: exponenciální tvar zadání i výsledku se nastavuje samostatně u každé veličiny.';"
new = "    : 'SŠ režim: exponenciální tvar zadání i výsledku se nastavuje samostatně u každé veličiny. V zadání je při převodu z menší jednotky na větší exponent kladný, opačným směrem záporný.';"
if old not in text:
    raise SystemExit('SŠ meta anchor not found')
text = text.replace(old, new, 1)

# Test helper for extracting a displayed exponent. A missing exponent means zero.
anchor = '''function nearlyEqual(a, b, rel = 1e-12){
  const scale = Math.max(1, Math.abs(a), Math.abs(b));
  return Math.abs(a - b) <= rel * scale;
}
'''
insert = '''function nearlyEqual(a, b, rel = 1e-12){
  const scale = Math.max(1, Math.abs(a), Math.abs(b));
  return Math.abs(a - b) <= rel * scale;
}

function visibleExponent(visible){
  const compact = String(visible).replace(/\\u202f/g, '').replace(/\\s/g, '');
  const parts = compact.split('·10');
  if(parts.length === 1) return 0;
  return Number([...parts[1]].map(ch => superscriptDigits[ch] ?? ch).join(''));
}
'''
if anchor not in test:
    raise SystemExit('nearlyEqual anchor not found')
test = test.replace(anchor, insert, 1)

# Check exponent sign against conversion direction for every generated exponential example.
old = '''      if(mode === 'ss' && ex.exponentialInput){
        assert(input >= 1e-10 - 1e-24, `Exponenciální zadání ${ex.value} je pod 10^-10.`);
        assert(input <= 1e10 + 1e-2, `Exponenciální zadání ${ex.value} je nad 10^10.`);
      }else{'''
new = '''      if(mode === 'ss' && ex.exponentialInput){
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
      }else{'''
if old not in test:
    raise SystemExit('primary exponential range test anchor not found')
test = test.replace(old, new, 1)

# Also check all optional SŠ quantities with result limits disabled.
old = '''      assert.equal(ex.quantityId, q.id, `Veličina ${q.id} (${mode}) byla nahrazena za ${ex.quantityId}.`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Veličina ${q.id} (${mode}) vygenerovala více než dvě platné číslice: ${ex.value}.`);
      generated++;'''
new = '''      assert.equal(ex.quantityId, q.id, `Veličina ${q.id} (${mode}) byla nahrazena za ${ex.quantityId}.`);
      assert(api.countVisibleSignificantFigures(ex.value) <= 2, `Veličina ${q.id} (${mode}) vygenerovala více než dvě platné číslice: ${ex.value}.`);
      if(mode === 'ss' && ex.exponentialInput){
        const fromFactorForSign = unitFactor(q, mode, ex.from);
        const toFactorForSign = unitFactor(q, mode, ex.to);
        const exponent = visibleExponent(ex.value);
        if(fromFactorForSign < toFactorForSign) assert(exponent > 0, `${q.id}: menší → větší musí mít kladný exponent (${ex.value}).`);
        if(fromFactorForSign > toFactorForSign) assert(exponent < 0, `${q.id}: větší → menší musí mít záporný exponent (${ex.value}).`);
      }
      generated++;'''
if old not in test:
    raise SystemExit('secondary sign test anchor not found')
test = test.replace(old, new, 1)

test = test.replace(
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');",
    "console.log('Kontrolováno: povinná veličina, max. 2 platné číslice, exp. tvar po veličinách, znaménko exponentu podle směru převodu, bez zbytečného 10^0, exp. rozsah 10^-10 až 10^10, min/max jen pro běžná zadání, převod z viditelného čísla, limit výsledku a Energie* bez kalorií.');"
)

html_path.write_text(text, encoding='utf-8')
test_path.write_text(test, encoding='utf-8')
