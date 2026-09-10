/**
 * FarmTwin AI - Main Application JavaScript
 * Handles all UI interactions, API calls, and real-time updates
 */

const API = {
  base: '',
  async get(path) {
    const r = await fetch(API.base + path);
    if (!r.ok) throw new Error(`API error ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(API.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(`API error ${r.status}`);
    return r.json();
  },
  async postForm(path, formData) {
    const r = await fetch(API.base + path, { method: 'POST', body: formData });
    if (!r.ok) throw new Error(`API error ${r.status}`);
    return r.json();
  }
};

// ─── State ────────────────────────────────────────────────────────────────────
const state = {
  currentPage: 'dashboard',
  dashboardData: null,
  farmData: null,
  loading: false,
  chatOpen: false,
  chatHistory: []
};

// ─── Navigation ───────────────────────────────────────────────────────────────
function navigateTo(page) {
  state.currentPage = page;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach(el => {
    el.style.display = el.id === `page-${page}` ? 'block' : 'none';
  });
  const titles = {
    dashboard: { title: 'Dashboard', sub: 'FarmTwin Digital Twin Overview' },
    'my-farm': { title: 'My Farm', sub: 'Farm Profile & Sensor Data' },
    advisor: { title: 'AI Advisor', sub: 'Crop Advisory & Recommendations' },
    detection: { title: 'Disease Detection', sub: 'AI Crop Image Analysis' },
    irrigation: { title: 'Irrigation', sub: 'Weather & Water Management' },
    market: { title: 'Market Intelligence', sub: 'Prices, Profit & Market Strategy' },
    whatif: { title: 'What-If Simulator', sub: 'Scenario Planning & Optimization' },
    knowledge: { title: 'Knowledge Center', sub: 'Agricultural RAG Knowledge Base' }
  };
  const info = titles[page] || titles.dashboard;
  const titleEl = document.getElementById('topbar-title');
  const subEl = document.getElementById('topbar-sub');
  if (titleEl) titleEl.textContent = info.title;
  if (subEl) subEl.textContent = info.sub;

  // Load page-specific data
  loadPageData(page);
  window.scrollTo(0, 0);
}

async function loadPageData(page) {
  switch (page) {
    case 'dashboard': await loadDashboard(); break;
    case 'my-farm': await loadFarmProfile(); break;
    case 'advisor': await loadAdvisor(); break;
    case 'irrigation': await loadIrrigation(); break;
    case 'market': await loadMarket(); break;
    case 'knowledge': await loadKnowledge(); break;
  }
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    showLoading('dashboard');
    const data = await API.get('/api/dashboard');
    state.dashboardData = data;
    renderDashboard(data);
  } catch (e) {
    console.error('Dashboard error:', e);
    showError('dashboard', 'Failed to load dashboard. Using demo data.');
  }
}

function renderDashboard(data) {
  // Farm Health Score ring
  renderScoreRing('health-score-ring', data.farm_health_score, '#4ade80');
  setText('health-score-val', data.farm_health_score);
  setText('crop-health-val', data.crop_health || 'Good');

  // Key metrics
  setText('soil-moisture-val', `${data.soil_moisture}%`);
  setText('temperature-val', `${data.temperature}°C`);
  setText('rain-prob-val', `${data.rain_probability}%`);
  setText('pest-risk-val', `${data.pest_risk}%`);
  setText('market-price-val', `₹${data.current_market_price}`);
  setText('expected-profit-val', `₹${formatINR(data.expected_profit)}`);
  setText('yield-val', `${data.expected_yield_tons}T`);
  setText('sustainability-val', `${data.sustainability_score}`);

  // Progress bars
  setProgress('moisture-bar', data.soil_moisture);
  setProgress('pest-bar', data.pest_risk, true);

  // Irrigation recommendation
  const irrEl = document.getElementById('irrigation-rec');
  if (irrEl) {
    const isSkip = (data.irrigation_recommendation || '').includes('SKIP');
    irrEl.innerHTML = `
      <div class="flex items-center gap-2">
        <span style="font-size:24px">${isSkip ? '⏸️' : '💧'}</span>
        <div>
          <div style="font-size:16px;font-weight:800;color:${isSkip ? 'var(--accent3)' : 'var(--accent2)'}">${data.irrigation_recommendation}</div>
          <div class="text-sm text-muted mt-1">${data.irrigation_reason || ''}</div>
        </div>
      </div>`;
  }

  // Pest/Disease status
  setText('pest-status-val', data.pest_disease_status || 'Monitor');

  // Today's Actions
  renderTodaysActions(data.todays_actions || []);

  // Risk Alerts
  renderAlerts(data.risk_alerts || []);

  // 7-Day Timeline
  renderTimeline(data.timeline_7day || []);

  // Agents status
  if (data.demo_mode) {
    document.querySelectorAll('.demo-indicator').forEach(el => el.style.display = 'flex');
  }
}

function renderTodaysActions(actions) {
  const el = document.getElementById('todays-actions');
  if (!el) return;
  el.innerHTML = actions.map(a => `
    <div class="action-item fade-in">
      <span style="font-size:22px;flex-shrink:0">${a.icon}</span>
      <div style="flex:1">
        <div class="flex items-center gap-2 mb-1">
          <span class="action-priority priority-${a.priority}">${a.priority}</span>
          <span class="text-sm text-muted">${a.category}</span>
        </div>
        <div style="font-size:13px;font-weight:600;margin-bottom:2px">${a.action}</div>
        <div class="text-sm text-muted">${a.reason}</div>
        <div class="text-sm text-green mt-1">Impact: ${a.impact}</div>
      </div>
    </div>
  `).join('');
}

function renderAlerts(alerts) {
  const el = document.getElementById('risk-alerts');
  if (!el) return;
  if (!alerts.length) {
    el.innerHTML = '<div class="alert-item alert-success"><span>✅</span><div><b>All Clear</b> — No immediate risks detected</div></div>';
    return;
  }
  el.innerHTML = alerts.map(a => `
    <div class="alert-item alert-${a.level} fade-in">
      <span style="font-size:18px">${a.level === 'danger' ? '🚨' : a.level === 'warning' ? '⚠️' : 'ℹ️'}</span>
      <div>
        <div style="font-weight:700;font-size:13px">${a.title}</div>
        <div class="text-sm text-muted">${a.message}</div>
        <div class="text-sm" style="margin-top:4px;font-weight:600">Action: ${a.action}</div>
      </div>
    </div>
  `).join('');
}

function renderTimeline(days) {
  const el = document.getElementById('timeline-7day');
  if (!el) return;
  el.innerHTML = days.map((d, i) => `
    <div class="timeline-item fade-in delay-${Math.min(i+1,5)}">
      <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;padding-top:4px">
        <div class="timeline-dot timeline-dot-${d.priority}" style="margin-left:14px"></div>
      </div>
      <div class="timeline-content">
        <div class="timeline-day">${d.day} <span class="text-sm text-muted">${d.date}</span></div>
        <div class="timeline-weather">${d.weather}</div>
        <div class="timeline-tasks">
          ${d.tasks.map(t => `<div class="timeline-task">${t}</div>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

// ─── Farm Profile ─────────────────────────────────────────────────────────────
async function loadFarmProfile() {
  try {
    const [farm, sensors] = await Promise.all([
      API.get('/api/farm/1'),
      API.get('/api/sensors/1')
    ]);
    state.farmData = { farm, sensors };
    renderFarmProfile(farm, sensors);
  } catch (e) {
    console.error('Farm profile error:', e);
  }
}

function renderFarmProfile(farm, sensors) {
  const formFields = ['name', 'farmer_name', 'location', 'area_acres', 'crop_type', 'soil_type', 'irrigation_type', 'crop_stage', 'sowing_date', 'expected_harvest'];
  formFields.forEach(f => {
    const el = document.getElementById(`farm-${f}`);
    if (el) el.value = farm[f] || '';
  });

  // Sensor displays
  const sensorFields = [
    ['soil_moisture', '%'], ['temperature', '°C'], ['humidity', '%'],
    ['rain_probability', '%'], ['ph_level', ''], ['nitrogen', ''], ['phosphorus', ''], ['potassium', '']
  ];
  sensorFields.forEach(([f, unit]) => {
    const el = document.getElementById(`sensor-${f}`);
    if (el) el.value = sensors[f] || '';
    const disp = document.getElementById(`sensor-${f}-display`);
    if (disp) disp.textContent = (sensors[f] || '-') + unit;
  });
}

async function saveFarmProfile() {
  const fields = ['name', 'farmer_name', 'location', 'area_acres', 'crop_type', 'soil_type', 'irrigation_type', 'crop_stage'];
  const body = {};
  fields.forEach(f => {
    const el = document.getElementById(`farm-${f}`);
    if (el) body[f] = f === 'area_acres' ? parseFloat(el.value) : el.value;
  });
  try {
    await API.post('/api/farm/1', body);
    showToast('Farm profile saved successfully! ✅');
  } catch (e) {
    showToast('Error saving farm profile', 'error');
  }
}

async function saveSensors() {
  const fields = ['soil_moisture', 'temperature', 'humidity', 'rain_probability', 'ph_level', 'nitrogen', 'phosphorus', 'potassium'];
  const body = {};
  fields.forEach(f => {
    const el = document.getElementById(`sensor-${f}`);
    if (el && el.value) body[f] = parseFloat(el.value);
  });
  try {
    await API.post('/api/sensors/1', body);
    showToast('Sensor data updated! ✅');
    await loadDashboard();
  } catch (e) {
    showToast('Error saving sensor data', 'error');
  }
}

// ─── AI Advisor ───────────────────────────────────────────────────────────────
async function loadAdvisor() {
  try {
    const data = await API.get('/api/dashboard');
    renderAdvisor(data);
  } catch (e) {
    console.error('Advisor error:', e);
  }
}

function renderAdvisor(data) {
  const crop = data.crop_advice || {};
  const status = crop.current_status || {};
  const fert = crop.fertilizer_recommendation || {};
  const harvest = crop.harvest_forecast || {};

  setText('advisor-stage', status.stage || 'Flowering');
  setText('advisor-health', status.health_score || 78);
  setText('advisor-days-harvest', harvest.days_remaining || 42);
  setText('advisor-yield', harvest.expected_yield_tons || 4.2);
  setText('advisor-fert-product', fert.product || 'NPK 0:0:50 + Calcium Nitrate');
  setText('advisor-fert-dose', fert.dose || '5g/L via fertigation');
  setText('advisor-fert-reason', fert.reason || 'Flowering stage demands high K');

  const actEl = document.getElementById('advisor-actions');
  if (actEl && crop.actions) {
    actEl.innerHTML = crop.actions.map(a => `
      <div class="action-item fade-in">
        <span style="font-size:18px">✅</span>
        <div style="font-size:13px">${a}</div>
      </div>
    `).join('');
  }
}

// ─── Disease Detection ────────────────────────────────────────────────────────
function setupDiseaseDetection() {
  const zone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('disease-file');
  const preview = document.getElementById('preview-img');

  if (!zone) return;

  zone.addEventListener('click', () => fileInput?.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleImageFile(file);
  });

  fileInput?.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) handleImageFile(file);
  });
}

function handleImageFile(file) {
  const preview = document.getElementById('preview-img');
  const zone = document.getElementById('upload-zone');
  if (preview) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.style.display = 'block';
      if (zone) zone.style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  // Store file for upload
  document.getElementById('disease-file').fileToUpload = file;
  document.getElementById('analyze-btn')?.removeAttribute('disabled');
}

async function analyzeImage() {
  const fileInput = document.getElementById('disease-file');
  const file = fileInput?.fileToUpload || (fileInput?.files && fileInput.files[0]);

  if (!file) {
    showToast('Please select an image first', 'error');
    return;
  }

  const btn = document.getElementById('analyze-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loading-spinner"></span> Analyzing...'; }

  try {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('farm_id', '1');

    const result = await API.postForm('/api/detect-disease', formData);
    renderDiseaseResult(result);
  } catch (e) {
    showToast('Analysis failed: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '🔬 Analyze Image'; }
  }
}

function renderDiseaseResult(result) {
  const panel = document.getElementById('disease-result-panel');
  if (!panel) return;

  const severityColor = {
    'None': 'var(--accent)', 'Low': 'var(--accent)',
    'Medium': 'var(--accent3)', 'High': 'var(--accent4)', 'Critical': '#dc2626'
  }[result.severity] || 'var(--accent3)';

  panel.style.display = 'flex';
  panel.innerHTML = `
    <div class="card fade-in">
      <div class="card-header">
        <div>
          <div class="card-title">🔬 Analysis Result</div>
          <div class="card-subtitle">${result.source || 'Demo Mode'} ${result.demo_mode ? '· Demo Data' : ''}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:28px;font-weight:900;color:${severityColor}">${result.confidence}%</div>
          <div class="text-sm text-muted">Confidence</div>
        </div>
      </div>

      <div class="grid-2" style="gap:16px;margin-bottom:16px">
        <div class="result-item">
          <div class="result-item-label">Detected</div>
          <div style="font-size:15px;font-weight:700;color:${result.disease_name.includes('No Disease') ? 'var(--accent)' : 'var(--accent3)'}">${result.disease_name}</div>
        </div>
        <div class="result-item">
          <div class="result-item-label">Severity</div>
          <div style="font-size:18px;font-weight:800;color:${severityColor}">${result.severity}</div>
        </div>
        <div class="result-item">
          <div class="result-item-label">Affected Area</div>
          <div class="result-item-value result-neutral">${result.affected_area_pct}%</div>
        </div>
        <div class="result-item">
          <div class="result-item-label">Urgency</div>
          <div style="font-size:13px;font-weight:700;color:${result.urgency === 'Immediate' ? 'var(--accent4)' : 'var(--accent3)'}">${result.urgency}</div>
        </div>
      </div>

      ${result.symptoms && result.symptoms.length ? `
        <div class="mb-4">
          <div style="font-size:13px;font-weight:700;margin-bottom:8px">📋 Symptoms Observed</div>
          ${result.symptoms.map(s => `<div class="text-sm text-muted" style="padding:4px 0;border-bottom:1px solid var(--border)">• ${s}</div>`).join('')}
        </div>
      ` : ''}

      ${result.recommended_actions && result.recommended_actions.length ? `
        <div class="mb-4">
          <div style="font-size:13px;font-weight:700;margin-bottom:8px">💊 Recommended Actions</div>
          ${result.recommended_actions.map((a, i) => `
            <div class="action-item" style="padding:10px 12px;margin-bottom:6px">
              <span style="background:var(--accent);color:#0a1a0f;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0">${i+1}</span>
              <div class="text-sm">${a}</div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      ${result.chemical_treatments && result.chemical_treatments.length ? `
        <div class="mb-4">
          <div style="font-size:13px;font-weight:700;margin-bottom:8px">🧪 Chemical Treatments</div>
          <table class="market-table">
            <tr><th>Product</th><th>Dose</th><th>Frequency</th></tr>
            ${result.chemical_treatments.map(t => `<tr><td>${t.product}</td><td>${t.dose}</td><td>${t.frequency}</td></tr>`).join('')}
          </table>
        </div>
      ` : ''}

      ${result.organic_alternatives && result.organic_alternatives.length ? `
        <div>
          <div style="font-size:13px;font-weight:700;margin-bottom:8px">🌿 Organic Alternatives</div>
          ${result.organic_alternatives.map(o => `<div class="text-sm text-muted" style="padding:4px 0">• ${o}</div>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

// ─── What-If Simulator ────────────────────────────────────────────────────────
const whatifState = {
  irrigation_pct: 100,
  fertilizer_amount_pct: 100,
  harvest_days_offset: 0,
  selling_market: 'Local Market',
  debounceTimer: null
};

function setupWhatIf() {
  ['irrigation', 'fertilizer'].forEach(param => {
    const slider = document.getElementById(`wi-${param}`);
    const display = document.getElementById(`wi-${param}-val`);
    if (slider) {
      slider.addEventListener('input', () => {
        const val = parseInt(slider.value);
        whatifState[param === 'irrigation' ? 'irrigation_pct' : 'fertilizer_amount_pct'] = val;
        if (display) display.textContent = val + '%';
        debouncedRunWhatIf();
      });
    }
  });

  const harvestSlider = document.getElementById('wi-harvest');
  const harvestDisplay = document.getElementById('wi-harvest-val');
  if (harvestSlider) {
    harvestSlider.addEventListener('input', () => {
      const val = parseInt(harvestSlider.value);
      whatifState.harvest_days_offset = val;
      if (harvestDisplay) harvestDisplay.textContent = val > 0 ? `+${val} days` : val === 0 ? 'Optimal' : `${val} days`;
      debouncedRunWhatIf();
    });
  }

  const marketSel = document.getElementById('wi-market');
  if (marketSel) {
    marketSel.addEventListener('change', () => {
      whatifState.selling_market = marketSel.value;
      debouncedRunWhatIf();
    });
  }
}

function debouncedRunWhatIf() {
  clearTimeout(whatifState.debounceTimer);
  whatifState.debounceTimer = setTimeout(runWhatIf, 300);
}

async function runWhatIf() {
  try {
    const result = await API.post('/api/whatif', {
      irrigation_pct: whatifState.irrigation_pct,
      fertilizer_amount_pct: whatifState.fertilizer_amount_pct,
      harvest_days_offset: whatifState.harvest_days_offset,
      selling_market: whatifState.selling_market,
      area_acres: 2.0
    });
    renderWhatIfResults(result);
  } catch (e) {
    console.error('WhatIf error:', e);
  }
}

function renderWhatIfResults(r) {
  const pct = v => v >= 0 ? `+${v}%` : `${v}%`;
  const pctClass = v => v >= 0 ? 'result-positive' : 'result-negative';
  const inr = v => `₹${formatINR(Math.abs(v))}`;

  setText('wi-water-saved', `${Math.max(0, r.water_saved_liters).toLocaleString()}L`);
  setText('wi-water-saved-pct', `${r.water_saved_pct > 0 ? '-' : '+'}${Math.abs(r.water_saved_pct).toFixed(1)}%`);
  setText('wi-yield', `${r.scenario_yield_kg.toLocaleString()} kg`);
  setText('wi-yield-change', pct(r.yield_change_pct));
  document.getElementById('wi-yield-change')?.classList.add(pctClass(r.yield_change_pct));
  setText('wi-cost', inr(r.total_cost));
  setText('wi-revenue', inr(r.gross_revenue));
  setText('wi-profit', inr(r.net_profit));
  setText('wi-profit-vs-base', `${r.profit_vs_baseline >= 0 ? '+' : ''}₹${formatINR(r.profit_vs_baseline)}`);
  const profitVsEl = document.getElementById('wi-profit-vs-base');
  if (profitVsEl) {
    profitVsEl.style.color = r.profit_vs_baseline >= 0 ? 'var(--accent)' : 'var(--accent4)';
  }
  setText('wi-roi', `${r.roi_pct}%`);
  setText('wi-sustainability', r.sustainability_score);
  renderScoreRing('wi-sustainability-ring', r.sustainability_score, '#a78bfa');
  renderWhatIfChart(r);

  const recEl = document.getElementById('wi-recommendation');
  if (recEl) recEl.innerHTML = `<div class="text-sm" style="padding:12px;background:var(--surface2);border-radius:8px;border-left:3px solid var(--accent)">${r.recommendation}</div>`;

  const insightsEl = document.getElementById('wi-insights');
  if (insightsEl && r.key_insights) {
    insightsEl.innerHTML = r.key_insights.map(i => `
      <div class="flex items-center gap-2 mt-2">
        <span>${i.icon}</span>
        <span class="text-sm" style="color:${i.type === 'positive' ? 'var(--accent)' : i.type === 'negative' ? 'var(--accent4)' : 'var(--text-muted)'}">${i.text}</span>
      </div>
    `).join('');
  }
}

function renderWhatIfChart(r) {
  const canvas = document.getElementById('wi-profit-chart');
  if (!canvas) return;
  // Simple SVG bar comparison
  const baseline = 94400; // local market baseline
  const max = Math.max(r.net_profit, baseline) * 1.1;
  const w = canvas.clientWidth || 300;
  const h = 120;
  const bw = 60;

  const baselineH = (baseline / max) * h;
  const scenarioH = (Math.max(0, r.net_profit) / max) * h;
  const color = r.net_profit >= baseline ? '#4ade80' : '#f87171';

  canvas.innerHTML = `
    <svg width="100%" height="${h + 40}" viewBox="0 0 200 ${h + 40}">
      <rect x="20" y="${h - baselineH}" width="${bw}" height="${baselineH}" fill="rgba(139,146,176,0.3)" rx="4"/>
      <text x="50" y="${h + 16}" text-anchor="middle" font-size="10" fill="#8b92b0">Baseline</text>
      <text x="50" y="${h - baselineH - 6}" text-anchor="middle" font-size="10" fill="#8b92b0">₹${formatINR(baseline)}</text>
      <rect x="120" y="${h - scenarioH}" width="${bw}" height="${scenarioH}" fill="${color}" rx="4" opacity="0.8"/>
      <text x="150" y="${h + 16}" text-anchor="middle" font-size="10" fill="${color}">Scenario</text>
      <text x="150" y="${h - scenarioH - 6}" text-anchor="middle" font-size="10" fill="${color}">₹${formatINR(r.net_profit)}</text>
      <line x1="0" y1="${h}" x2="200" y2="${h}" stroke="var(--border)" stroke-width="1"/>
    </svg>
  `;
}

// ─── Market Intelligence ──────────────────────────────────────────────────────
async function loadMarket() {
  try {
    const data = await API.get('/api/market?crop_type=Tomato');
    renderMarket(data);
  } catch (e) {
    console.error('Market error:', e);
  }
}

function renderMarket(data) {
  const pricesEl = document.getElementById('market-prices-table');
  if (pricesEl && data.prices) {
    pricesEl.innerHTML = `
      <table class="market-table" style="width:100%">
        <thead><tr><th>Market</th><th>Price/kg</th><th>Trend</th><th>Expected Profit (2 acres)</th></tr></thead>
        <tbody>
          ${data.prices.map(p => {
            const profit = Math.round(4200 * 0.75 * p.price - 23200);
            return `
              <tr>
                <td style="font-weight:600">${p.market}</td>
                <td><span class="price-tag">₹${p.price}</span></td>
                <td><span class="trend-pill trend-${p.trend}">${p.trend === 'rising' ? '📈 Rising' : p.trend === 'falling' ? '📉 Falling' : '➡️ Stable'}</span></td>
                <td style="font-weight:700;color:${profit > 80000 ? 'var(--accent)' : 'var(--text)'}">₹${formatINR(profit)}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  // Price history chart
  if (data.history) {
    renderPriceChart(data.history);
  }

  // Best market
  if (data.best_market) {
    setText('best-market-name', data.best_market.market || 'Online (eNAM)');
    setText('best-market-price', `₹${data.best_market.price || 38}`);
  }
}

function renderPriceChart(history) {
  const el = document.getElementById('price-history-chart');
  if (!el) return;
  const days = history.dates || [];
  const series = [
    { name: 'Online (eNAM)', data: history.online_enam || [33,34,35,36,36,37,38], color: '#4ade80' },
    { name: 'Mumbai Wholesale', data: history.mumbai_wholesale || [30,31,32,33,34,34,35], color: '#60a5fa' },
    { name: 'Nashik APMC', data: history.nashik_apmc || [28,29,30,31,30,31,32], color: '#f59e0b' },
    { name: 'Local Market', data: history.local_market || [24,25,26,27,27,28,28], color: '#8b92b0' }
  ];

  const w = 600, h = 160, padL = 30, padR = 10, padT = 10, padB = 30;
  const allVals = series.flatMap(s => s.data);
  const minV = Math.min(...allVals) - 2;
  const maxV = Math.max(...allVals) + 2;
  const xStep = (w - padL - padR) / (days.length - 1);
  const yScale = (v) => padT + (h - padT - padB) * (1 - (v - minV) / (maxV - minV));
  const xAt = (i) => padL + i * xStep;

  const linesHTML = series.map(s => {
    const pts = s.data.map((v, i) => `${xAt(i)},${yScale(v)}`).join(' ');
    const circles = s.data.map((v, i) => `<circle cx="${xAt(i)}" cy="${yScale(v)}" r="3" fill="${s.color}"/>`).join('');
    return `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="2" opacity="0.8"/>${circles}`;
  }).join('');

  const xLabels = days.map((d, i) => `<text x="${xAt(i)}" y="${h - 4}" text-anchor="middle" font-size="9" fill="#8b92b0">${d}</text>`).join('');

  const legend = series.map((s, i) => `
    <g transform="translate(${i * 130 + padL}, ${h + 20})">
      <rect width="12" height="3" fill="${s.color}" y="-1"/>
      <text x="16" y="3" font-size="9" fill="#8b92b0">${s.name}</text>
    </g>
  `).join('');

  el.innerHTML = `
    <svg width="100%" viewBox="0 0 ${w} ${h + 48}" style="overflow:visible">
      <g opacity="0.2">
        ${[25,30,35,40].map(v => `<line x1="${padL}" y1="${yScale(v)}" x2="${w-padR}" y2="${yScale(v)}" stroke="var(--border)" stroke-width="1"/>
          <text x="${padL-4}" y="${yScale(v)+4}" text-anchor="end" font-size="9" fill="#8b92b0">₹${v}</text>`).join('')}
      </g>
      ${linesHTML}
      ${xLabels}
      ${legend}
    </svg>
  `;
}

// ─── Irrigation ───────────────────────────────────────────────────────────────
async function loadIrrigation() {
  try {
    const data = await API.get('/api/irrigation/1');
    renderIrrigation(data);
  } catch (e) {
    console.error('Irrigation error:', e);
  }
}

function renderIrrigation(data) {
  const irr = data.irrigation || {};
  const weather = data.current || {};

  setText('irr-recommendation', irr.recommendation || 'SKIP TODAY');
  setText('irr-reason', irr.reason || '');
  setText('irr-water-saved', (irr.water_saved_liters || 0) + 'L');
  setText('irr-next', irr.next_irrigation || 'Thursday');

  // Current weather
  setText('irr-temp', (weather.temperature || 29) + '°C');
  setText('irr-humidity', (weather.humidity || 68) + '%');
  setText('irr-rain', (weather.rain_probability || 72) + '%');
  setText('irr-wind', (weather.wind_speed || 12) + ' km/h');

  // 7-day irrigation schedule
  const schedEl = document.getElementById('irr-schedule');
  if (schedEl && irr.schedule) {
    schedEl.innerHTML = irr.schedule.map(s => `
      <div class="action-item fade-in">
        <span style="font-size:20px">${s.action === 'IRRIGATE' ? '💧' : s.action === 'SKIP' ? '⏸️' : s.action === 'HALF' ? '🌤️' : '🔍'}</span>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:700">${s.day}</div>
          <div class="text-sm text-muted">${s.reason}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:13px;font-weight:700;color:${s.liters > 0 ? 'var(--accent2)' : 'var(--text-muted)'}">${s.liters ? s.liters + 'L' : '—'}</div>
          <div class="text-sm" style="color:${s.action === 'SKIP' ? 'var(--accent)' : s.action === 'IRRIGATE' ? 'var(--accent2)' : 'var(--accent3)'}">${s.action}</div>
        </div>
      </div>
    `).join('');
  }

  // Tips
  const tipsEl = document.getElementById('irr-tips');
  if (tipsEl && irr.tips) {
    tipsEl.innerHTML = irr.tips.map(t => `<div class="text-sm" style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;gap:8px"><span>💡</span><span class="text-muted">${t}</span></div>`).join('');
  }

  // 7-day weather forecast
  render7DayForecast(data.forecast_7day || []);
}

function render7DayForecast(forecast) {
  const el = document.getElementById('weather-forecast');
  if (!el) return;
  el.innerHTML = `
    <div class="flex gap-2" style="overflow-x:auto;padding-bottom:8px">
      ${forecast.map((f, i) => `
        <div style="flex-shrink:0;min-width:90px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:14px 10px;text-align:center">
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;font-weight:600">${f.day}</div>
          <div style="font-size:24px;margin-bottom:6px">${f.icon}</div>
          <div style="font-size:14px;font-weight:800">${f.high}°</div>
          <div style="font-size:11px;color:var(--text-muted)">${f.low}°</div>
          <div style="font-size:11px;margin-top:6px;font-weight:600;color:${f.rain_prob > 60 ? 'var(--accent2)' : 'var(--text-muted)'}">💧${f.rain_prob}%</div>
        </div>
      `).join('')}
    </div>
  `;
}

// ─── Knowledge Center ─────────────────────────────────────────────────────────
async function loadKnowledge() {
  try {
    const data = await API.get('/api/knowledge');
    renderKnowledge(data.articles || []);
  } catch (e) {
    console.error('Knowledge error:', e);
  }
}

function renderKnowledge(articles) {
  const grid = document.getElementById('knowledge-grid');
  if (!grid) return;
  grid.innerHTML = articles.map(a => `
    <div class="knowledge-card fade-in" onclick="showKnowledgeModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">
      <div class="knowledge-card-icon">${a.icon}</div>
      <div class="knowledge-card-cat">${a.category}</div>
      <div class="knowledge-card-title">${a.title}</div>
      <div class="knowledge-card-preview">${a.content.substring(0, 120).trim()}...</div>
    </div>
  `).join('');
}

function showKnowledgeModal(article) {
  const modal = document.getElementById('knowledge-modal');
  const title = document.getElementById('km-title');
  const content = document.getElementById('km-content');
  if (!modal) return;
  if (title) title.textContent = `${article.icon} ${article.title}`;
  if (content) content.innerHTML = article.content.split('\n').map(l => l.trim() ? `<div style="padding:3px 0;${l.startsWith('-') ? 'padding-left:12px' : 'font-weight:600;margin-top:8px'}">${l}</div>` : '').join('');
  modal.classList.add('active');
}

async function searchKnowledge() {
  const query = document.getElementById('knowledge-search')?.value;
  if (!query) return;
  try {
    const result = await API.post('/api/knowledge/search', { query });
    const el = document.getElementById('knowledge-search-result');
    if (el) {
      el.style.display = 'block';
      el.innerHTML = `
        <div class="card mt-4">
          <div class="card-header">
            <div class="card-title">🤖 AI Answer: "${query}"</div>
            <span class="ibm-badge">IBM Langflow RAG</span>
          </div>
          <div class="text-sm" style="line-height:1.8;white-space:pre-wrap">${result.result}</div>
        </div>
      `;
    }
  } catch (e) {
    showToast('Search failed', 'error');
  }
}

// ─── Chatbot ──────────────────────────────────────────────────────────────────
function toggleChat() {
  state.chatOpen = !state.chatOpen;
  const panel = document.getElementById('chatbot-panel');
  const fab = document.getElementById('chatbot-fab');
  if (panel) panel.classList.toggle('hidden', !state.chatOpen);
  if (fab) fab.classList.toggle('chat-open', state.chatOpen);

  if (state.chatOpen && state.chatHistory.length === 0) {
    appendChatMsg('ai', "👋 Hi! I'm **FarmTwin AI**, your personal farm advisor!\n\nYou have a **2-acre Tomato farm** in Nashik at the **Flowering stage**. How can I help you today?\n\nTry asking:\n• Should I irrigate today?\n• Why are my leaves turning yellow?\n• When should I harvest?\n• Which market gives me highest profit?", "FarmTwin AI");
  }
}

function appendChatMsg(role, text, source) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const div = document.createElement('div');
  div.className = `chat-msg ${role} fade-in`;
  div.innerHTML = `
    <div style="white-space:pre-wrap;line-height:1.5">${marked(text)}</div>
    ${source ? `<div class="msg-source">${source}</div>` : ''}
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  state.chatHistory.push({ role, text });
}

function marked(text) {
  // Minimal markdown renderer
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:var(--surface);padding:1px 4px;border-radius:3px">$1</code>')
    .replace(/\n/g, '<br>');
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input?.value.trim();
  if (!msg) return;
  input.value = '';

  appendChatMsg('user', msg);

  // Typing indicator
  const container = document.getElementById('chat-messages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-msg ai';
  typingDiv.id = 'typing-indicator';
  typingDiv.innerHTML = '<span class="pulse">🌾 Thinking...</span>';
  container?.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const result = await API.post('/api/chat', { message: msg, farm_id: 1 });
    typingDiv.remove();
    appendChatMsg('ai', result.response, result.source);
  } catch (e) {
    typingDiv.remove();
    appendChatMsg('ai', "Sorry, I encountered an error. Please try again.", 'Error');
  }
}

function useSuggestion(text) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = text;
    sendChat();
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setProgress(id, pct, reverse = false) {
  const el = document.getElementById(id);
  if (!el) return;
  const fill = el.querySelector('.progress-fill');
  if (fill) {
    setTimeout(() => { fill.style.width = `${pct}%`; }, 100);
  }
}

function formatINR(n) {
  if (!n && n !== 0) return '0';
  const abs = Math.abs(n);
  if (abs >= 100000) return (n / 100000).toFixed(1) + 'L';
  if (abs >= 1000) return (n / 1000).toFixed(1) + 'K';
  return Math.round(n).toLocaleString('en-IN');
}

function renderScoreRing(id, score, color = '#4ade80') {
  const el = document.getElementById(id);
  if (!el) return;
  const r = 54, cx = 70, cy = 70;
  const circumference = 2 * Math.PI * r;
  const dashOffset = circumference - (score / 100) * circumference;

  el.innerHTML = `
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--surface2)" stroke-width="10"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="10"
        stroke-dasharray="${circumference}" stroke-dashoffset="${dashOffset}"
        stroke-linecap="round" transform="rotate(-90 ${cx} ${cy})"
        style="transition:stroke-dashoffset 1.5s ease"/>
      <text x="${cx}" y="${cy - 4}" text-anchor="middle" font-size="28" font-weight="900" fill="${color}">${score}</text>
      <text x="${cx}" y="${cy + 16}" text-anchor="middle" font-size="11" fill="var(--text-muted)">/ 100</text>
    </svg>
  `;
}

function showLoading(page) {
  // Could show skeleton; for now just log
}

function showError(page, msg) {
  console.warn(page, msg);
  showToast(msg, 'warning');
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed;bottom:90px;left:50%;transform:translateX(-50%);
    background:${type === 'error' ? 'var(--accent4)' : type === 'warning' ? 'var(--accent3)' : 'var(--accent)'};
    color:${type === 'success' ? '#0a1a0f' : '#fff'};
    padding:10px 20px;border-radius:8px;font-size:13px;font-weight:600;
    z-index:500;animation:fadeIn 0.3s ease;white-space:nowrap;
    box-shadow:0 4px 20px rgba(0,0,0,0.4)
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Navigation
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    el.addEventListener('click', () => navigateTo(el.dataset.page));
  });

  // Chat enter key
  document.getElementById('chat-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });

  // Setup components
  setupDiseaseDetection();
  setupWhatIf();

  // Load initial page
  navigateTo('dashboard');

  // Run initial whatif with defaults
  setTimeout(runWhatIf, 500);

  // Mobile sidebar toggle
  document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
    document.querySelector('.sidebar')?.classList.toggle('open');
  });
});
