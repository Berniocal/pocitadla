from pathlib import Path
p = Path('prevody.html')
text = p.read_text(encoding='utf-8')
text2 = text.replace(
    "units.push(compoundUnit('m/h', 1 / 3600, Math.log10(1 / 3600), 'm', 'h', ''));",
    "units.push(compoundUnit('m/min', 1 / 60, Math.log10(1 / 60), 'm', 'min', ''));",
    1
).replace(
    "Např. m/s → km/h mění obě části, m/s → m/h jen jednu.",
    "Např. m/s → km/h mění obě části, m/s → m/min jen jednu.",
    1
)
if text2 == text:
    raise SystemExit('speed one-part replacements not found')
p.write_text(text2, encoding='utf-8')
