from pathlib import Path
p = Path('prevody.html')
text = p.read_text(encoding='utf-8')
old = """    const rounded = roundToSignificant(raw, 2);
    if(!Number.isFinite(rounded) || rounded <= 0) return null;
    const exponent = Math.floor(Math.log10(rounded));
    if(exponent < -10 || exponent > 10) return null;
"""
new = """    const rounded = roundToSignificant(raw, 2);
    if(!Number.isFinite(rounded) || rounded <= 0) return null;
    if(rounded < 1e-10 || rounded > 1e10) return null;
    const exponent = Math.floor(Math.log10(rounded));
    if(exponent < -10 || exponent > 10) return null;
"""
if old not in text:
    raise SystemExit('exp formatter block not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8')
