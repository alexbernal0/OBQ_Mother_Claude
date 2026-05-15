---
name: lwc-gui-skills
description: "Lightweight-charts-python + PyWebView GUI architecture patterns for OBQ desktop apps. Use when building or debugging GUI components in OBQ_AI_OptionsApp, OBQ_EH_v1, or any app using louisnw01/lightweight-charts-python. Contains the 8 golden rules, proven API patterns from source code, and createElement patterns that actually work."
compatibility: "Claude Code (VSCode + CLI), OpenCode"
metadata:
  author: OBQ
  source: OBQ_AI_OptionsApp GUI Assessment 2026-03-23
  updated: "2026-03-23"
  version: "1.0"
  allowed-tools: "Read, Bash"
---

# LWC GUI SKILLS — OBQ Desktop App Patterns

Reference source: `louisnw01/lightweight-charts-python` (1,972★) · `r0x0r/pywebview` (5,814★) · `tradingview/lightweight-charts` (14,113★)
Working reference app: `C:\Users\admin\Desktop\OBQ_EH_v1\EH_GUI\eh_app.py`

---

## THE 8 GOLDEN RULES (violations cause all known GUI bugs)

```
RULE 1  Never innerHTML for structure → use createElement() + appendChild()
RULE 2  Never <style> inside display:none div → inject into document.head
RULE 3  Tab switching = closure refs captured at creation, NOT getElementById()
RULE 4  Zero CDN — bundle all JS in LWC js/ folder or copy to lwc package
RULE 5  Build custom tables with createElement — NOT Tabulator/ag-grid
RULE 6  create_line(name='') always — NOT name='IVR' unless df has 'IVR' column
RULE 7  callbackFunction('event_name_~_data') — _~_ delimiter ALWAYS
RULE 8  Theme switch = rebuild panel via createElement, NOT CSS patching
```

---

## LINE / SERIES API (from abstract.py source)

```python
# CORRECT: name='' → accepts DataFrame with 'time' + 'value' columns
line = chart.create_line(name='', color='#00c5a8', width=2,
                          price_line=False, price_label=True)
df = pd.DataFrame({'time': ['2024-01-01', '2024-01-02'], 'value': [25.3, 26.1]})
line.set(df)  # works

# WRONG: name='IVR' → set() expects a column called 'IVR', not 'value'
line = chart.create_line(name='IVR', ...)
line.set(df)  # NameError: No column named "IVR"
# Fix: either use name='' OR rename df column: df.rename(columns={'value':'IVR'})

# OHLC data (chart.set)
df = pd.DataFrame({'time':..., 'open':..., 'high':..., 'low':..., 'close':...})
chart.set(df)  # no 'volume' column = no volume bars shown

# Subgraph
sub = chart.create_subchart(position='bottom', height=0.22, sync=True)
sub_line = sub.create_line(name='', color='#00c5a8', width=2, price_line=False)
sub_line.set(ivr_df)  # same time+value format
```

---

## BUILT-IN TABLE (use this, not Tabulator)

```python
# chart.create_table() is built-in — zero CDN dependency
table = chart.create_table(
    width=0.35,           # fraction of window width
    height=0.5,           # fraction
    headings=('Symbol', 'IVR', 'Value', 'Signal'),
    widths=(0.2, 0.15, 0.25, 0.4),
    alignments=('left', 'center', 'left', 'left'),
    position='right',
    draggable=False,
    background_color='#ffffff',
    border_color='#e5e7eb',
)
# Add rows
row = table.new_row()
row.set('Symbol', 'SPY')
row.set('IVR', '72.3')
# Style a cell
row['Signal'].background_color = '#f0fdf4'
row['Signal'].set('FIRING')
```

---

## CALLBACK PROTOCOL (from abstract.py L917)

```python
# JS → Python: MUST use _~_ separator
# In injected JS:
button.onclick = () => window.callbackFunction('my_event_~_some_data')

# In Python: register handler BEFORE chart.show()
chart.win.handlers['my_event'] = lambda data: handle(data)

# The LWC event loop splits on _~_ and routes to handlers dict
# DO NOT use ~ alone — it won't route correctly
```

---

## PANEL INJECTION PATTERN (EH_v1 golden standard)

```python
# CORRECT: createElement chain (EH_v1 eh_app.py lines 121-267)
chart.run_script(f'''
    const panel = document.createElement('div');
    panel.id = 'my-panel';
    panel.style.cssText = `
        position: absolute; top: 0; right: 0;
        width: 35%; height: 100%;
        background: {t['bg']};
        display: flex; flex-direction: column;
        z-index: 3000;
    `;

    // Tab buttons with CLOSURE references (not getElementById)
    const tab1 = document.createElement('button');
    const tab2 = document.createElement('button');
    const view1 = document.createElement('div');
    const view2 = document.createElement('div');

    tab1.onclick = () => {{
        view1.style.display = 'flex';
        view2.style.display = 'none';
        tab1.style.fontWeight = '700';
        tab2.style.fontWeight = '400';
    }};
    tab2.onclick = () => {{
        view1.style.display = 'none';
        view2.style.display = 'flex';
        tab2.style.fontWeight = '700';
        tab1.style.fontWeight = '400';
    }};

    panel.appendChild(tab1);
    panel.appendChild(tab2);
    panel.appendChild(view1);
    panel.appendChild(view2);
    document.body.appendChild(panel);
''')

# WRONG: innerHTML injection
chart.run_script(f'''
    var w = document.createElement('div');
    w.innerHTML = {json.dumps(html)};  // <style> tags IGNORED, <script> NOT executed
    document.body.appendChild(w);
''')
```

---

## CSS INJECTION (only correct way)

```python
# Inject into document.head BEFORE panel creation
chart.run_script(f'''
    var s = document.createElement('style');
    s.textContent = `
        .my-card {{ background: {t['bg']}; border: 1px solid {t['border']}; }}
        .my-card:hover {{ background: {t['bg_panel']}; }}
    `;
    document.head.appendChild(s);
''')
# After this, all .my-card elements will have the style regardless of display state
```

---

## CUSTOM TABLE (createElement, zero deps)

```python
chart.run_script(f'''
    const tbody = document.createElement('div');
    tbody.id = 'results-tbody';
    tbody.style.cssText = 'flex:1;overflow-y:auto;';

    // Add a data row (call this from Python via run_script)
    window.addResultRow = function(data) {{
        const row = document.createElement('div');
        row.style.cssText = `
            display:flex;padding:5px 8px;
            border-bottom:1px solid {t['border']};
            background: ${{data.firing ? '#f0fdf4' : '{t["bg"]}'}};
            border-left: ${{data.firing ? '3px solid #00c5a8' : '3px solid transparent'}};
            cursor:pointer;
        `;
        row.onclick = () => window.callbackFunction('row_click_~_' + data.id);

        const cols = [data.label, data.value, data.threshold, data.hist_pct];
        const widths = ['40%', '20%', '20%', '20%'];
        cols.forEach((text, i) => {{
            const cell = document.createElement('div');
            cell.textContent = text || '—';
            cell.style.cssText = `width:${{widths[i]}};font-size:11px;color:{t['text']};`;
            row.appendChild(cell);
        }});
        tbody.appendChild(row);
    }};

    // Clear all rows
    window.clearResults = function() {{ tbody.innerHTML = ''; }};
''')

# Push data from Python
def push_results(rows):
    chart.run_script("clearResults();")
    for r in rows:
        import json
        chart.run_script(f"addResultRow({json.dumps(r)});")
```

---

## CHART STYLE (price scale + date axis)

```python
chart.price_scale(
    visible=True,
    scale_margin_top=0.1,
    scale_margin_bottom=0.1,
    border_visible=True,
)
chart.time_scale(
    visible=True,
    time_visible=True,
    seconds_visible=False,   # shows dates, not timestamps
    border_visible=True,
)
chart.volume_config(             # hide volume bars
    up_color='rgba(0,0,0,0)',
    down_color='rgba(0,0,0,0)',
)

# Enable both price scales directly via JS (Python wrapper doesn't expose left scale)
chart.run_script(f'''
    {chart.id}.chart.applyOptions({{
        leftPriceScale: {{ visible: true, borderVisible: true, autoScale: true }},
        rightPriceScale: {{ visible: true, borderVisible: true, autoScale: true }},
    }});
''')
```

---

## TOPBAR WIDGETS

```python
# Switcher — func receives the widget object (not the value string)
chart.topbar.switcher('theme', options=('Light','Dark'), default='Light',
                       func=lambda _: handle_theme(chart.topbar['theme'].value))

# Textbox — update via .set()
chart.topbar.textbox('status', 'Ready')
chart.topbar['status'].set('Running...')   # bracket access, NOT .get()

# Button
chart.topbar.button('run', 'RUN', func=lambda _: on_run())

# Common mistake: topbar.get('status') → AttributeError
# Correct: topbar['status']
```

---

## EXTERNAL JS BUNDLING (no CDN)

```python
# Copy JS libraries INTO the LWC package js/ folder so they're served as relative URLs
import shutil
LWC_JS = Path('C:/Users/admin/AppData/Local/Programs/Python/Python312/Lib/site-packages/lightweight_charts/js')
shutil.copy('tabulator.min.js', LWC_JS / 'tabulator.min.js')
shutil.copy('tabulator.min.css', LWC_JS / 'tabulator.min.css')

# Then reference in injected HTML as:
# <link rel="stylesheet" href="./tabulator.min.css">
# <script src="./tabulator.min.js"></script>
```

---

## KNOWN PYWEBVIEW GOTCHAS

```
1. CDN URLs (unpkg.com, cdn.jsdelivr.net) may be blocked — always bundle locally
2. evaluate_js() is async — results may not be immediate; use run_script() for fire-and-forget
3. <script> tags in innerHTML are NOT executed — inject via createElement('script').textContent
4. <style> in display:none elements is NOT processed at load time
5. window.callbackFunction must use _~_ separator — single ~ does not route to handlers
6. JSON strings > ~500KB in run_script() may timeout — chunk large data
7. panel injection timing: build panel BEFORE chart.show(), OR use run_last=True on run_script()
```

---

## REFERENCE FILES

```
Working app:     C:\Users\admin\Desktop\OBQ_EH_v1\EH_GUI\eh_app.py
Options app:     C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_OptionsApp\gui\app.py
LWC source:      %PYTHON%/site-packages/lightweight_charts/abstract.py
PyWebView:       https://github.com/r0x0r/pywebview/tree/master/examples
LWC JS API:      https://tradingview.github.io/lightweight-charts/docs/api
LWC Python docs: https://lightweight-charts-python.readthedocs.io
```
