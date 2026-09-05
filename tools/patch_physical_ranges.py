from pathlib import Path

p = Path('prevody.html')
s = p.read_text(encoding='utf-8')

def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit('Missing expected snippet: ' + old[:180].replace('\n', ' '))
    s = s.replace(old, new, count)

# Keep exponential form ready by default for every SŠ quantity, including those
# that are not selected initially. The user can still switch it off per quantity.
rep(
"  expQuantitiesSS:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','cas'],",
"  expQuantitiesSS:['delka','plocha','objem','hmotnost','sila','rychlost','hustota','tlak','energie','energieplus','napeti','cas','vykon','proud','odpor','zrychleni','frekvence','uhel','naboj','kapacita','vodivost','magindukce','magnetickytok','indukcnost','latkovemnozstvi'],"
)

# Electric charge should live in realistic school-scale prefixes, not kC/MC/etc.
rep(
"function buildChargeUnits(){\n  return prefixedUnits('C', ['f','p','n','µ','m','','k','M','G','T','P']);\n}",
"function buildChargeUnits(){\n  return prefixedUnits('C', ['p','n','µ','m']);\n}"
)

profiles = r'''
// Realistické výchozí fyzikální rozsahy jsou zadány v SI.
// U širokých veličin (délka, hmotnost, napětí, energie...) zůstává původní
// obecný generátor. Omezení používáme hlavně tam, kde by náhodné hodnoty
// snadno přestaly dávat fyzikální nebo školní smysl.
const quantityValueProfiles = {
  rychlost:{
    zs:{bands:[
      {min:3, max:15, weight:.45},              // cyklista
      {min:15, max:45, weight:.55}              // běžné auto
    ]},
    ss:{bands:[
      {min:1, max:70, weight:.60},               // běžné pozemské rychlosti
      {min:1000, max:8000, weight:.25},          // rakety a družice
      {min:1e5, max:2.99792458e8, weight:.15, log:true} // vysoké rychlosti až pod c
    ]}
  },
  hustota:{
    zs:{bands:[
      {min:.8, max:2, weight:.10},               // plyny kolem běžných podmínek
      {min:500, max:1500, weight:.45},           // kapaliny a lehké materiály
      {min:1500, max:20000, weight:.45, log:true}// běžné pevné látky a kovy
    ]},
    ss:{bands:[
      {min:.05, max:10, weight:.15, log:true},
      {min:500, max:2000, weight:.35},
      {min:2000, max:23000, weight:.50, log:true}// zhruba do hustoty nejtěžších běžných prvků
    ]}
  },
  tlak:{
    zs:{min:1e3, max:2e5, log:true},
    ss:{min:1, max:1e9, log:true}
  },
  vykon:{
    zs:{min:1, max:2e5, log:true},
    ss:{min:1e-6, max:1e9, log:true}
  },
  proud:{
    zs:{min:1e-3, max:20, log:true},
    ss:{min:1e-9, max:1e4, log:true}
  },
  odpor:{
    zs:{min:1, max:1e6, log:true},
    ss:{min:1e-3, max:1e9, log:true}
  },
  zrychleni:{
    zs:{min:.5, max:20},
    ss:{min:1e-3, max:1e4, log:true}
  },
  frekvence:{
    zs:{min:1, max:2e4, log:true},
    ss:{min:1e-3, max:1e12, log:true}
  },
  uhel:{
    zs:{min:Math.PI/180, max:2*Math.PI},
    ss:{min:Math.PI/180, max:2*Math.PI}
  },
  naboj:{
    ss:{min:1e-12, max:1e-3, log:true}           // pC až mC; typicky nC a µC
  },
  kapacita:{
    ss:{min:1e-12, max:1e-2, log:true}           // pF až mF
  },
  vodivost:{
    ss:{min:1e-6, max:10, log:true}
  },
  magindukce:{
    ss:{min:1e-6, max:10, log:true}              // µT až jednotky T
  },
  magnetickytok:{
    ss:{min:1e-9, max:1, log:true}
  },
  indukcnost:{
    ss:{min:1e-6, max:10, log:true}
  },
  latkovemnozstvi:{
    ss:{min:1e-6, max:1e3, log:true}
  }
};
'''.strip()

rep(
"const $ = id => document.getElementById(id);",
profiles + "\n\nconst $ = id => document.getElementById(id);"
)

helpers = r'''
function valueProfileForQuantity(quantityId){
  const profile = quantityValueProfiles[quantityId];
  return profile ? (profile[settings.mode] || null) : null;
}

function sampleProfileValue(profile){
  let range = profile;
  if(Array.isArray(profile.bands) && profile.bands.length){
    const total = profile.bands.reduce((sum, band) => sum + (Number(band.weight) || 0), 0) || profile.bands.length;
    let pick = Math.random() * total;
    range = profile.bands[profile.bands.length - 1];
    for(const band of profile.bands){
      pick -= (Number(band.weight) || (total === profile.bands.length ? 1 : 0));
      if(pick <= 0){ range = band; break; }
    }
  }
  const min = Number(range.min);
  const max = Number(range.max);
  if(!(min > 0) || !(max > min)) return null;
  return range.log
    ? Math.pow(10, randomFloat(Math.log10(min), Math.log10(max)))
    : randomFloat(min, max);
}

function visibleNumberFromFixedValue(value, useExponential){
  if(!Number.isFinite(value) || value <= 0) return null;

  if(useExponential){
    const exponent = Math.floor(Math.log10(Math.abs(value)));
    const mantissa = value / Math.pow(10, exponent);
    const mantissaVisible = trimCz(formatCz(mantissa, 0, 2));
    const parsedMantissa = parseCzNumber(mantissaVisible);
    if(exponent === 0){
      return {visible:mantissaVisible, value:parsedMantissa, exponential:false};
    }
    return {
      visible:`${mantissaVisible}·10${toSuperscript(exponent)}`,
      value:parsedMantissa * Math.pow(10, exponent),
      exponential:true
    };
  }

  let decimals = decimalPlacesFor(value);
  const abs = Math.abs(value);
  if(abs > 0 && abs < Math.pow(10, -decimals)){
    decimals = Math.min(12, Math.ceil(-Math.log10(abs)) + 2);
  }
  const visible = formatCz(value, decimals, decimals);
  const parsed = parseCzNumber(visible);
  if(!(parsed > 0)) return null;
  return {visible, value:parsed, exponential:false};
}

function randomVisibleNumberForQuantity(quantity, useExponential, pair){
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
'''.strip()

rep(
"function randomInt(min, max){",
helpers + "\n\nfunction randomInt(min, max){"
)

rep(
"    const x = randomVisibleNumber(useExponential, pair);",
"    const x = randomVisibleNumberForQuantity(q, useExponential, pair);"
)

rep(
"      <p class=\"small\" style=\"margin-bottom:0\">* Energie* obsahuje i Wh, kWh, MWh a cal; na SŠ také eV, keV, MeV a GeV.</p>",
"      <p class=\"small\" style=\"margin-bottom:6px\">* Energie* obsahuje i Wh, kWh, MWh a cal; na SŠ také eV, keV, MeV a GeV.</p>\n      <p class=\"small\" style=\"margin-bottom:0\">U veličin, kde je to fyzikálně důležité, generátor používá realistický výchozí rozsah v SI. Například rychlost na ZŠ odpovídá hlavně cyklistům a autům, na SŠ se přidávají družice a vysoké rychlosti; hustota zůstává v rozsahu běžných pozemských látek a elektrický náboj v pC–mC. U širokých veličin jako délka, hmotnost, napětí nebo energie zůstává obecný rozsah.</p>"
)

p.write_text(s, encoding='utf-8')
