from pathlib import Path

html_path = Path('prevody.html')
text = html_path.read_text(encoding='utf-8')

# Accordion styling for settings groups.
css_anchor = ".settingsHeader{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}\n.settingsGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}"
css_new = ".settingsHeader{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}\n.settingsGroups{display:grid;gap:10px;margin:14px 0}\n.settingsGroup{background:white;border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(70,50,20,.04)}\n.settingsGroup summary{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 14px;cursor:pointer;font-weight:800;list-style:none;user-select:none;background:#fffdf9}\n.settingsGroup summary::-webkit-details-marker{display:none}\n.settingsGroup summary::after{content:'＋';font-size:18px;font-weight:500;color:var(--muted);line-height:1}\n.settingsGroup[open] summary{background:#fff8e8}\n.settingsGroup[open] summary::after{content:'−'}\n.settingsGroupBody{padding:14px;border-top:1px solid var(--line)}\n.settingsGroupBody>.small:first-child{margin-top:0}\n.settingsGroupBody>.small:last-child{margin-bottom:0}\n.settingsGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}"
if css_anchor not in text:
    raise SystemExit('settings CSS anchor not found')
text = text.replace(css_anchor, css_new, 1)

start = text.index('    <div class="card">\n      <h3>Základ</h3>')
end_marker = '''    <div class="btnrow">\n      <button class="btn" id="applySettings">Použít a vygenerovat</button>'''
end = text.index(end_marker, start)

new_settings = '''    <div class="settingsGroups">
      <details class="settingsGroup">
        <summary>Počet příkladů</summary>
        <div class="settingsGroupBody">
          <div class="settingField">
            <label for="countInput">Počet příkladů</label>
            <input id="countInput" type="number" min="1" max="60" step="1">
          </div>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Čísla v zadání – minimum a maximum</summary>
        <div class="settingsGroupBody">
          <div class="settingsGrid">
            <div class="settingField">
              <label for="minNumberInput">Nejmenší číslo v běžném zadání</label>
              <input id="minNumberInput" type="number" min="0" step="any">
            </div>
            <div class="settingField">
              <label for="maxNumberInput">Největší číslo v běžném zadání</label>
              <input id="maxNumberInput" type="number" min="0" step="any">
            </div>
          </div>
          <p class="small">Na SŠ se tento min/max rozsah vztahuje jen na běžná zadání bez exponenciálního tvaru. Exponenciální zadání mají vlastní rozsah řádů.</p>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Desetinná místa v zadání</summary>
        <div class="settingsGroupBody">
          <div class="settingsGrid">
            <div class="settingField">
              <label for="smallDecimalsInput">Pro čísla menší než 1</label>
              <input id="smallDecimalsInput" type="number" min="0" max="8" step="1">
            </div>
            <div class="settingField">
              <label for="mediumDecimalsInput">Pro čísla menší než 10</label>
              <input id="mediumDecimalsInput" type="number" min="0" max="8" step="1">
            </div>
            <div class="settingField">
              <label for="largeDecimalsInput">Pro čísla od 10 výš</label>
              <input id="largeDecimalsInput" type="number" min="0" max="8" step="1">
            </div>
          </div>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Jednotky a směr převodu</summary>
        <div class="settingsGroupBody">
          <div class="settingField">
            <label for="jumpInput">Preferovaný minimální rozdíl velikosti jednoduchých jednotek</label>
            <select id="jumpInput">
              <option value="1">1 řád (alespoň 10×)</option>
              <option value="2">2 řády (alespoň 100×)</option>
              <option value="3">3 řády (alespoň 1 000×)</option>
              <option value="4">4 řády (alespoň 10 000×)</option>
              <option value="5">5 řádů (alespoň 100 000×)</option>
              <option value="6">6 řádů (alespoň 1 000 000×)</option>
            </select>
            <span class="small">Výchozí jsou 3 řády = alespoň 1 000×. Toto pravidlo se nepoužívá pro složené jednotky ani pro čas. U času se nepoužívají bezprostředně sousední jednotky a upřednostňují se den, h, min, s a ms.</span>
          </div>
          <div class="sep"></div>
          <label class="check">
            <input id="niceInputRuleInput" type="checkbox">
            <span>Podle směru převodu volit hezčí zadání: z menší jednotky číslo větší než 10, z větší jednotky číslo menší než 1.</span>
          </label>
          <div class="settingField" id="compoundConversionSetting" style="margin-top:12px">
            <label for="compoundConversionInput">SŠ – u složených jednotek měnit</label>
            <select id="compoundConversionInput">
              <option value="both">obě části jednotky</option>
              <option value="one">jen jednu část jednotky</option>
            </select>
            <span class="small">Např. m/s → km/h mění obě části; m/s → m/min jen jmenovatel a m/min → km/min jen čitatel.</span>
          </div>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Výsledek</summary>
        <div class="settingsGroupBody">
          <label class="check" style="margin-bottom:10px">
            <input id="resultLimitEnabledInput" type="checkbox">
            <span>Omezit délku výsledku</span>
          </label>
          <div class="settingsGrid">
            <div class="settingField">
              <label for="resultMaxIntegerDigitsInput">Maximálně číslic před desetinnou čárkou</label>
              <input id="resultMaxIntegerDigitsInput" type="number" min="1" max="15" step="1">
            </div>
            <div class="settingField">
              <label for="resultMaxDecimalsInput">Maximálně desetinných míst</label>
              <input id="resultMaxDecimalsInput" type="number" min="0" max="20" step="1">
            </div>
          </div>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Veličiny</summary>
        <div class="settingsGroupBody">
          <label class="check" style="margin-bottom:10px">
            <input id="ensureAllQuantitiesInput" type="checkbox">
            <span>Každá vybraná veličina se má v sadě objevit alespoň jednou.</span>
          </label>
          <p class="small">Když je volba zapnutá a je vybráno více veličin než příkladů, počet příkladů se automaticky zvýší. Na SŠ se exponenciální tvar nastavuje u každé veličiny zvlášť.</p>
          <div id="quantityChecks" class="checks"></div>
          <p class="small">* Energie* obsahuje i Wh, kWh a MWh; na SŠ také eV, keV, MeV a GeV.</p>
        </div>
      </details>

      <details class="settingsGroup">
        <summary>Předpony</summary>
        <div class="settingsGroupBody">
          <div id="prefixChecks" class="prefixes"></div>
        </div>
      </details>
    </div>

'''
text = text[:start] + new_settings + text[end:]
html_path.write_text(text, encoding='utf-8')

# Add lightweight structural tests so future edits do not accidentally flatten the settings again.
test_path = Path('tests/prevody.test.mjs')
test = test_path.read_text(encoding='utf-8')
anchor = "const html = fs.readFileSync('prevody.html', 'utf8');\n"
checks = """const html = fs.readFileSync('prevody.html', 'utf8');
const settingsGroupCount = (html.match(/<details class=\"settingsGroup\">/g) || []).length;
assert.equal(settingsGroupCount, 7, 'Nastavení má být rozdělené do 7 samostatných sbalených balíků.');
for(const title of ['Počet příkladů','Čísla v zadání – minimum a maximum','Desetinná místa v zadání','Jednotky a směr převodu','Výsledek','Veličiny','Předpony']){
  assert(html.includes(`<summary>${title}</summary>`), `Chybí sbalitelný balík nastavení: ${title}.`);
}
assert(!/<details class=\"settingsGroup\"[^>]*\sopen(?:\s|>|=)/.test(html), 'Balíky nastavení mají být po otevření panelu výchozí sbalené.');
"""
if anchor not in test:
    raise SystemExit('test html anchor not found')
test = test.replace(anchor, checks, 1)
test_path.write_text(test, encoding='utf-8')
