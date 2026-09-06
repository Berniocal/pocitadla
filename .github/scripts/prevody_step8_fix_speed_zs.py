from pathlib import Path
p = Path('prevody.html')
text = p.read_text(encoding='utf-8')
old = """function buildSpeedUnits(){
  return filterUnits([
    compoundUnit('m/s', 1, 0, 'm', 's', ''),
    compoundUnit('km/h', 1 / 3.6, .55, 'km', 'h', 'k'),
    compoundUnit('m/h', 1 / 3600, Math.log10(1 / 3600), 'm', 'h', '')
  ]);
}
"""
new = """function buildSpeedUnits(mode){
  const units = [
    compoundUnit('m/s', 1, 0, 'm', 's', ''),
    compoundUnit('km/h', 1 / 3.6, .55, 'km', 'h', 'k')
  ];
  if(mode === 'ss'){
    // Pomocná běžná složená jednotka umožní na SŠ měnit jen čitatel nebo jen jmenovatel.
    units.push(compoundUnit('m/h', 1 / 3600, Math.log10(1 / 3600), 'm', 'h', ''));
  }
  return filterUnits(units);
}
"""
if old not in text:
    raise SystemExit('speed block not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8')
