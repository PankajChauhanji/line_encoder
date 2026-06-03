from flask import Flask, render_template_string, request, jsonify
from line_encoder import encode_and_plot, ENCODERS

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Line Encoder</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0a0a;
    --surface:  #111111;
    --border:   #1e1e1e;
    --accent:   #00c896;
    --blue:     #4a9eff;
    --text:     #e0e0e0;
    --muted:    #555;
    --font-mono: 'JetBrains Mono', monospace;
    --font-sans: 'Syne', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 20px 80px;
  }

  /* ── header ── */
  header {
    width: 100%;
    max-width: 740px;
    margin-bottom: 48px;
  }
  header h1 {
    font-size: clamp(1.6rem, 4vw, 2.4rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #fff;
  }
  header h1 span { color: var(--accent); }
  header p {
    margin-top: 6px;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.06em;
  }

  /* ── card ── */
  .card {
    width: 100%;
    max-width: 740px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 32px;
  }

  /* ── form ── */
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
  }
  @media (max-width: 520px) { .form-row { grid-template-columns: 1fr; } }

  label {
    display: block;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  input[type="text"] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 11px 14px;
    font-family: var(--font-mono);
    font-size: 1rem;
    color: var(--text);
    outline: none;
    transition: border-color .2s;
    letter-spacing: 0.15em;
  }
  input[type="text"]:focus { border-color: var(--accent); }

  select {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 11px 14px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--text);
    outline: none;
    appearance: none;
    cursor: pointer;
    transition: border-color .2s;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23555' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;
  }
  select:focus { border-color: var(--accent); }

  button {
    width: 100%;
    padding: 12px;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 5px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: opacity .2s, transform .1s;
  }
  button:hover  { opacity: .88; }
  button:active { transform: scale(.98); }
  button:disabled { opacity: .4; cursor: not-allowed; }

  /* ── error ── */
  .error {
    margin-top: 16px;
    padding: 10px 14px;
    border: 1px solid #ff4d6d44;
    background: #ff4d6d11;
    border-radius: 5px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: #ff6b85;
    display: none;
  }

  /* ── results ── */
  .results {
    width: 100%;
    max-width: 740px;
    margin-top: 28px;
    display: none;
    flex-direction: column;
    gap: 16px;
  }

  .plot-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    animation: fadeUp .35s ease both;
  }
  .plot-card:nth-child(2) { animation-delay: .1s; }

  @keyframes fadeUp {
    from { opacity:0; transform: translateY(14px); }
    to   { opacity:1; transform: translateY(0); }
  }

  .plot-label {
    padding: 12px 18px;
    border-bottom: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .plot-label .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--blue);
    flex-shrink: 0;
  }
  .plot-label .dot.green { background: var(--accent); }

  .plot-card img {
    width: 100%;
    display: block;
  }
</style>
</head>
<body>

<header>
  <h1>Line <span>Encoder</span></h1>
  <p>// digital signal encoding visualiser</p>
</header>

<div class="card">
  <div class="form-row">
    <div>
      <label>Binary Input</label>
      <input type="text" id="dataInput" placeholder="e.g. 10110010" maxlength="32">
    </div>
    <div>
      <label>Encoding Scheme</label>
      <select id="schemeSelect" onchange="updateHint()">
        <optgroup label="NRZ Family">
          <option value="nrz_l">NRZ-L</option>
          <option value="nrz_i">NRZ-I</option>
        </optgroup>
        <optgroup label="Biphase">
          <option value="manchester">Manchester</option>
          <option value="differential_manchester">Differential Manchester</option>
        </optgroup>
        <optgroup label="Bipolar / Multilevel">
          <option value="ami">AMI</option>
          <option value="hdb3">HDB3</option>
          <option value="mlt3">MLT-3</option>
        </optgroup>
        <optgroup label="Block Coding">
          <option value="four_b_five_b">4B/5B + NRZ-I</option>
        </optgroup>
      </select>
      <div id="schemeHint" style="margin-top:7px;font-family:var(--font-mono);font-size:0.68rem;color:var(--muted);min-height:1em;"></div>
    </div>
  </div>
  <button id="encodeBtn" onclick="encode()">Encode</button>
  <div class="error" id="errorBox"></div>
</div>

<div class="results" id="results">
  <div class="plot-card">
    <div class="plot-label"><span class="dot"></span>Original Signal</div>
    <img id="origImg" src="" alt="Original signal">
  </div>
  <div class="plot-card">
    <div class="plot-label"><span class="dot green"></span><span id="encLabel">Encoded Signal</span></div>
    <img id="encImg" src="" alt="Encoded signal">
  </div>
</div>

<script>
  const HINTS = {
    nrz_l:                  '0 → +1 &nbsp;|&nbsp; 1 → −1',
    nrz_i:                  'Transition on 1 · no transition on 0',
    manchester:             '0 → −1,+1 &nbsp;|&nbsp; 1 → +1,−1 &nbsp;(IEEE 802.3)',
    differential_manchester:'Mid-bit transition always · start transition on 0',
    ami:                    '0 → 0 &nbsp;|&nbsp; 1 → alternating ±1',
    hdb3:                   'AMI + substitutes every run of 4 zeros (used in E1/E3)',
    mlt3:                   'Cycles ±1,0 on each 1-bit · 0-bits hold (used in 100BASE-TX)',
    four_b_five_b:          'Maps 4-bit groups → 5-bit codes, then NRZ-I · input padded to ×4',
  };

  function updateHint() {
    const s = document.getElementById('schemeSelect').value;
    document.getElementById('schemeHint').innerHTML = HINTS[s] || '';
  }
  updateHint();

  async function encode() {
    const data   = document.getElementById('dataInput').value.trim();
    const scheme = document.getElementById('schemeSelect').value;
    const btn    = document.getElementById('encodeBtn');
    const errBox = document.getElementById('errorBox');
    const results = document.getElementById('results');

    errBox.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Encoding…';

    try {
      const res  = await fetch('/encode', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({ data, scheme })
      });
      const json = await res.json();

      if (json.error) {
        errBox.textContent = json.error;
        errBox.style.display = 'block';
        results.style.display = 'none';
        return;
      }

      document.getElementById('origImg').src = 'data:image/png;base64,' + json.original;
      document.getElementById('encImg').src  = 'data:image/png;base64,' + json.encoded;
      document.getElementById('encLabel').textContent = json.label + ' — Encoded Signal';
      results.style.display = 'flex';

      // re-trigger animation
      results.querySelectorAll('.plot-card').forEach(c => {
        c.style.animation = 'none';
        void c.offsetWidth;
        c.style.animation = '';
      });

    } catch(e) {
      errBox.textContent = 'Server error — is Flask running?';
      errBox.style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Encode';
    }
  }

  // allow Enter key
  document.getElementById('dataInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') encode();
  });
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/encode', methods=['POST'])
def encode():
    body   = request.get_json(force=True)
    data   = body.get('data', '').strip()
    scheme = body.get('scheme', '')
    try:
        orig_img, enc_img, label = encode_and_plot(data, scheme)
        return jsonify(original=orig_img, encoded=enc_img, label=label)
    except ValueError as e:
        return jsonify(error=str(e))


if __name__ == '__main__':
    app.run(debug=True)