from pathlib import Path

path = Path('prevody.html')
text = path.read_text(encoding='utf-8')

# 1) Energie*: odstranit kalorické jednotky úplně.
text = text.replace("    unit('cal', 4.184, Math.log10(4.184), null),\n", "")
text = text.replace("    unit('kcal', 4184, Math.log10(4184), null)\n", "")
text = text.replace("    unit('MWh', 3.6e9, Math.log10(3.6e9), null),\n  ];", "    unit('MWh', 3.6e9, Math.log10(3.6e9), null)\n  ];")
text = text.replace(
    '* Energie* obsahuje i Wh, kWh, MWh, cal a kcal; na SŠ také eV, keV, MeV a GeV.',
    '* Energie* obsahuje i Wh, kWh a MWh; na SŠ také eV, keV, MeV a GeV.'
)

# 2) Jádro generátoru: pokud je požadována konkrétní veličina,
#    všechny pokusy zůstávají u ní a nesmí se přejít na jinou.
old = '''function makeExample(index, preferredQuantity, useExponentialInput = false){
  const quantities = preferredQuantity ? [preferredQuantity, ...selectedQuantities().filter(q => q.id !== preferredQuantity.id)] : selectedQuantities();
  if(!quantities.length) return null;
  for(let guard=0; guard<200; guard++){
    const q = guard < quantities.length ? quantities[guard] : randomChoice(quantities);
    const units = q.build(settings.mode).filter(u => Number.isFinite(u.factor) && u.factor !== 0);
    const pair = chooseUnitPair(units);
    if(!pair) continue;
    const x = randomVisibleNumber(useExponentialInput, pair);
    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    const significantFigures = countVisibleSignificantFigures(x.visible);
    const resultLimits = resultLimitsForMode();
    if(resultLimits.enabled && !resultFitsLimits(result, significantFigures, resultLimits)) continue;
    return {
      index,
      quantity:q.title,
      quantityId:q.id,
      value:x.visible,
      exponentialInput:x.exponential,
      from:pair.from.unit,
      to:pair.to.unit,
      result,
      significantFigures,
      resultPlain:formatSignificantPlain(result, significantFigures),
      resultExp:formatExpNumber(result, significantFigures)
    };
  }
  return null;
}'''
new = '''function makeExample(index, preferredQuantity, useExponentialInput = false){
  const quantities = preferredQuantity ? [preferredQuantity] : selectedQuantities();
  if(!quantities.length) return null;
  for(let guard=0; guard<500; guard++){
    const q = preferredQuantity || randomChoice(quantities);
    const units = q.build(settings.mode).filter(u => Number.isFinite(u.factor) && u.factor !== 0);
    const pair = chooseUnitPair(units);
    if(!pair) continue;
    const x = randomVisibleNumber(useExponentialInput, pair);
    const result = x.value * pair.from.factor / pair.to.factor;
    if(!Number.isFinite(result) || result === 0) continue;
    const significantFigures = countVisibleSignificantFigures(x.visible);
    const resultLimits = resultLimitsForMode();
    if(resultLimits.enabled && !resultFitsLimits(result, significantFigures, resultLimits)) continue;
    return {
      index,
      quantity:q.title,
      quantityId:q.id,
      value:x.visible,
      exponentialInput:x.exponential,
      from:pair.from.unit,
      to:pair.to.unit,
      result,
      significantFigures,
      resultPlain:formatSignificantPlain(result, significantFigures),
      resultExp:formatExpNumber(result, significantFigures)
    };
  }
  return null;
}'''
if old not in text:
    raise SystemExit('makeExample block not found')
text = text.replace(old, new, 1)

# 3) Když nastavení pro konkrétní veličinu nejde splnit, nic nenahrazovat.
#    Uživatel dostane jasné upozornění na konflikt nastavení.
text = text.replace(
    'let examples = [];\nlet answersVisible = false;',
    'let examples = [];\nlet answersVisible = false;\nlet generationFailures = [];',
    1
)

old = '''  examples = [];
  for(let i=1; i<=count; i++){
    if(cycle.length === 0) cycle = shuffle(quantities);
    if(cycle.length > 1 && cycle[0].id === previousId){
      cycle.push(cycle.shift());
    }
    const preferred = cycle.shift();
    const ex = makeExample(i, preferred, expInputSlots.has(i));
    if(ex) examples.push(ex);
    previousId = ex ? ex.quantityId : previousId;
  }'''
new = '''  examples = [];
  generationFailures = [];
  for(let i=1; i<=count; i++){
    if(cycle.length === 0) cycle = shuffle(quantities);
    if(cycle.length > 1 && cycle[0].id === previousId){
      cycle.push(cycle.shift());
    }
    const preferred = cycle.shift();
    const ex = makeExample(i, preferred, expInputSlots.has(i));
    if(ex){
      examples.push(ex);
      previousId = ex.quantityId;
    }else if(preferred){
      generationFailures.push(preferred.title);
    }
  }'''
if old not in text:
    raise SystemExit('generateExamples loop not found')
text = text.replace(old, new, 1)

old = '''function renderExamples(){
  if(!examples.length){
    $('examples').innerHTML = '<div class="empty">Vyber aspoň jednu veličinu a jednu dvojici jednotek v nastavení.</div>';
    return;
  }
  $('examples').innerHTML = examples.map(ex => {'''
new = '''function renderExamples(){
  const failureNames = [...new Set(generationFailures)];
  const warningHtml = failureNames.length
    ? `<div class="empty"><strong>Některé požadované příklady nešlo vytvořit bez porušení nastavení.</strong><br><span class="small">Nevynechal jsem je ani nenahradil jinou veličinou. Zkontroluj omezení pro: ${failureNames.join(', ')}.</span></div>`
    : '';
  if(!examples.length){
    $('examples').innerHTML = warningHtml || '<div class="empty">Vyber aspoň jednu veličinu a jednu dvojici jednotek v nastavení.</div>';
    return;
  }
  $('examples').innerHTML = warningHtml + examples.map(ex => {'''
if old not in text:
    raise SystemExit('renderExamples header not found')
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
