from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

old_speed = '''function buildSpeedUnits(mode){
  const units = [
    compoundUnit('m/s', 1, 0, 'm', 's', ''),
    compoundUnit('km/h', 1 / 3.6, .55, 'km', 'h', 'k')
  ];
  if(mode === 'ss'){
    // Pomocná běžná složená jednotka umožní na SŠ měnit jen čitatel nebo jen jmenovatel.
    units.push(compoundUnit('m/min', 1 / 60, Math.log10(1 / 60), 'm', 'min', ''));
  }
  return filterUnits(units);
}'''
new_speed = '''function buildSpeedUnits(mode){
  const units = [
    compoundUnit('m/s', 1, 0, 'm', 's', ''),
    compoundUnit('km/h', 1 / 3.6, .55, 'km', 'h', 'k')
  ];
  if(mode === 'ss'){
    // Doplňkové běžné složené jednotky dovolí při režimu „jen jednu část“
    // měnit samostatně jmenovatel (m/s ↔ m/min) i čitatel (m/min ↔ km/min).
    units.push(
      compoundUnit('m/min', 1 / 60, Math.log10(1 / 60), 'm', 'min', ''),
      compoundUnit('km/min', 1000 / 60, Math.log10(1000 / 60), 'km', 'min', 'k')
    );
  }
  return filterUnits(units);
}'''
if old_speed not in text:
    raise SystemExit('buildSpeedUnits block not found')
text = text.replace(old_speed, new_speed, 1)

old_help = 'Platí pro veličiny jako rychlost, hustota a zrychlení. Např. m/s → km/h mění obě části, m/s → m/min jen jednu.'
new_help = 'Platí pro veličiny jako rychlost, hustota a zrychlení. Např. m/s → km/h mění obě části; m/s → m/min mění jen jmenovatel a m/min → km/min jen čitatel.'
if old_help not in text:
    raise SystemExit('compound help text not found')
text = text.replace(old_help, new_help, 1)
html_path.write_text(text, encoding='utf-8')

test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')
anchor = '''// Elektrický náboj nesmí používat absurdně velké předpony.
{'''
insert = '''// Rychlost na SŠ musí umět při režimu „jen jednu část“ změnit zvlášť jmenovatel i čitatel.
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

'''
if anchor not in test:
    raise SystemExit('test insertion anchor not found')
test = test.replace(anchor, insert + anchor, 1)
test_path.write_text(test, encoding='utf-8')
