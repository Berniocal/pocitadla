from pathlib import Path
p = Path('prevody.html')
s = p.read_text(encoding='utf-8')

def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit('Missing expected snippet: ' + old[:180].replace('\n', ' '))
    s = s.replace(old, new, count)

rep(
"      {min:1e5, max:2.99792458e8, weight:.15, log:true} // vysoké rychlosti až pod c",
"      {min:2e8, max:2.99792458e8, weight:.15}    // relativistické rychlosti blízko rychlosti světla"
)

rep(
"  naboj:{\n    ss:{min:1e-12, max:1e-3, log:true}           // pC až mC; typicky nC a µC\n  },",
"  naboj:{\n    ss:{bands:[\n      {min:1e-9, max:1e-5, weight:.70, log:true},// hlavně nC až µC\n      {min:1e-12, max:1e-9, weight:.15, log:true},\n      {min:1e-5, max:1e-3, weight:.15, log:true}\n    ]}\n  },"
)

old = """function randomVisibleNumberForQuantity(quantity, useExponential, pair){
  const profile = valueProfileForQuantity(quantity.id);
  if(!profile) return randomVisibleNumber(useExponential, pair);

  for(let attempt=0; attempt<200; attempt++){
    const siValue = sampleProfileValue(profile);
    if(!(siValue > 0)) continue;
    const inputValue = siValue / pair.from.factor;
    const formatted = visibleNumberFromFixedValue(inputValue, useExponential);
    if(formatted) return formatted;
  }
  return randomVisibleNumber(useExponential, pair);
}
"""
new = """function randomVisibleNumberForQuantity(quantity, useExponential, pair){
  const profile = valueProfileForQuantity(quantity.id);
  if(!profile) return randomVisibleNumber(useExponential, pair);

  for(let attempt=0; attempt<200; attempt++){
    const siValue = sampleProfileValue(profile);
    if(!(siValue > 0)) continue;
    const inputValue = siValue / pair.from.factor;
    if(useExponential){
      const exponent = Math.floor(Math.log10(Math.abs(inputValue)));
      if(exponent < -10 || exponent > 10) continue;
    }
    const formatted = visibleNumberFromFixedValue(inputValue, useExponential);
    if(formatted) return formatted;
  }
  return null;
}
"""
rep(old, new)

rep(
"    const x = randomVisibleNumberForQuantity(q, useExponential, pair);\n    const result = x.value * pair.from.factor / pair.to.factor;",
"    const x = randomVisibleNumberForQuantity(q, useExponential, pair);\n    if(!x) continue;\n    const result = x.value * pair.from.factor / pair.to.factor;"
)

p.write_text(s, encoding='utf-8')
