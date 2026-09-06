from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

old = """const commonTimeUnits = new Set(['den','h','min','s','ms']);\n\nfunction isCommonTimePair(pair){\n  return commonTimeUnits.has(pair.from.unit) && commonTimeUnits.has(pair.to.unit);\n}\n"""
new = """const timeUnitOrder = ['den','h','min','s','ms','µs','ns','ps','fs'];\nconst commonTimeUnits = new Set(['den','h','min','s','ms']);\n\nfunction isCommonTimePair(pair){\n  return commonTimeUnits.has(pair.from.unit) && commonTimeUnits.has(pair.to.unit);\n}\n\nfunction isAdjacentTimePair(pair){\n  const fromIndex = timeUnitOrder.indexOf(pair.from.unit);\n  const toIndex = timeUnitOrder.indexOf(pair.to.unit);\n  if(fromIndex < 0 || toIndex < 0) return false;\n  return Math.abs(fromIndex - toIndex) === 1;\n}\n"""
if old not in text:
    raise SystemExit('time helper block not found')
text = text.replace(old, new, 1)

old = """  // Čas má vlastní logiku: většinu příkladů skládáme z běžných jednotek,\n  // aby negeneroval hlavně dvojice typu ns ↔ ms. Velmi malé jednotky zůstávají možné.\n  if(quantityId === 'cas'){\n    const common = candidates.filter(isCommonTimePair);\n    const pool = common.length && Math.random() < 0.85 ? common : candidates;\n    const chosen = randomChoice(pool);\n    return chosen ? {from:chosen.from, to:chosen.to} : null;\n  }\n"""
new = """  // Čas má vlastní logiku: sousední jednotky (např. h ↔ min, min ↔ s) nepoužíváme.\n  // Většinu příkladů skládáme z běžných jednotek den/h/min/s/ms; velmi malé jednotky zůstávají možné jen občas.\n  if(quantityId === 'cas'){\n    const nonAdjacent = candidates.filter(pair => !isAdjacentTimePair(pair));\n    const available = nonAdjacent.length ? nonAdjacent : candidates;\n    const common = available.filter(isCommonTimePair);\n    const pool = common.length && Math.random() < 0.85 ? common : available;\n    const chosen = randomChoice(pool);\n    return chosen ? {from:chosen.from, to:chosen.to} : null;\n  }\n"""
if old not in text:
    raise SystemExit('time choose block not found')
text = text.replace(old, new, 1)

text = text.replace(
    "Výchozí jsou 3 řády = alespoň 1 000×. Toto pravidlo se nepoužívá pro složené jednotky ani pro čas. U času se naopak upřednostňují běžné dvojice den, h, min, s a ms; velmi malé jednotky se mohou objevit jen občas.",
    "Výchozí jsou 3 řády = alespoň 1 000×. Toto pravidlo se nepoužívá pro složené jednotky ani pro čas. U času se nepoužívají bezprostředně sousední jednotky (např. h ↔ min nebo min ↔ s); upřednostňují se běžné jednotky den, h, min, s a ms a velmi malé jednotky se mohou objevit jen občas."
)

html_path.write_text(text, encoding='utf-8')

test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')
old_test = """// Čas odstup v řádech ignoruje a výrazně preferuje běžné jednotky den/h/min/s/ms.\n{\n  const cfg = structuredClone(defaults);\n  cfg.mode = 'ss';\n  cfg.minJump = 6;\n  api.setSettings(cfg);\n  const time = quantityById('cas');\n  const common = new Set(['den','h','min','s','ms']);\n  let commonCount = 0;\n  for(let i=0; i<1000; i++){\n    const pair = api.chooseUnitPair(time.build('ss'), 'cas');\n    assert(pair, 'Čas musí být generovatelný i při vysokém odstupu.');\n    if(common.has(pair.from.unit) && common.has(pair.to.unit)) commonCount++;\n  }\n  assert(commonCount >= 700, `Běžné časové dvojice mají výrazně převažovat; bylo jich ${commonCount}/1000.`);\n}\n"""
new_test = """// Čas odstup v řádech ignoruje, nepoužívá sousední jednotky a výrazně preferuje den/h/min/s/ms.\n{\n  const cfg = structuredClone(defaults);\n  cfg.mode = 'ss';\n  cfg.minJump = 6;\n  api.setSettings(cfg);\n  const time = quantityById('cas');\n  const common = new Set(['den','h','min','s','ms']);\n  const order = ['den','h','min','s','ms','µs','ns','ps','fs'];\n  let commonCount = 0;\n  for(let i=0; i<1000; i++){\n    const pair = api.chooseUnitPair(time.build('ss'), 'cas');\n    assert(pair, 'Čas musí být generovatelný i při vysokém odstupu.');\n    const distance = Math.abs(order.indexOf(pair.from.unit) - order.indexOf(pair.to.unit));\n    assert(distance !== 1, `Čas nesmí použít sousední jednotky: ${pair.from.unit} → ${pair.to.unit}.`);\n    if(common.has(pair.from.unit) && common.has(pair.to.unit)) commonCount++;\n  }\n  assert(commonCount >= 700, `Běžné časové dvojice mají výrazně převažovat; bylo jich ${commonCount}/1000.`);\n}\n"""
if old_test not in test:
    raise SystemExit('time test block not found')
test = test.replace(old_test, new_test, 1)
test_path.write_text(test, encoding='utf-8')
