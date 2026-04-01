const { App } = require('@slack/bolt');
const axios = require('axios');
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
require('dotenv').config();

// ─── MQL analysis config ─────────────────────────────────────────────────────
const PYTHON  = 'C:\\Python314\\pythonw.exe';
const SCRIPTS = {
  mql:    'C:\\Users\\aless\\Documents\\skills\\mql-scripts\\analyze_mql.py',
  funnel: 'C:\\Users\\aless\\Documents\\skills\\mql-scripts\\analyze_funnel.py',
};
const OUTPUT_DIR = 'C:\\Users\\aless\\Documents\\skills\\mql-scripts\\outputs';

// Pending analysis state: userId -> { type, channel }
const pendingAnalysis = new Map();

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  appToken: process.env.SLACK_APP_TOKEN,
  socketMode: true,
});

const HUBSPOT_TOKEN = process.env.HUBSPOT_API_KEY;

// Solo estos pipelines — el resto se ignora
const TARGET_PIPELINES = ['corporate', 'enterprise', 'mid market', 'small users', 'outbound', 'micro'];

// Etapas que cuentan como "cerrado/ganado"
const WON_STAGES = ['ready to buy', 'closed won', 'won'];

// Etapas que se excluyen del "Rest of Pipeline"
const EXCLUDE_FROM_REST = ['ready to buy', 'closed won', 'won', 'closed lost', 'lost'];

// ─── Date range parser ──────────────────────────────────────────────────────────
function parseDateRange(text) {
  if (!text) return { start: null, end: null, label: 'All time' };

  const t = text.trim().toLowerCase().replace(/_/g, ' ');
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();

  const startOf = (year, month) => new Date(Date.UTC(year, month, 1, 0, 0, 0));
  const endOf   = (year, month) => new Date(Date.UTC(year, month + 1, 0, 23, 59, 59, 999));
  const qStart  = (year, q)     => startOf(year, q * 3);
  const qEnd    = (year, q)     => endOf(year, q * 3 + 2);
  const currentQ = Math.floor(m / 3);

  if (t === 'this month')   return { start: startOf(y, m), end: endOf(y, m), label: 'This month' };
  if (t === 'last month') {
    const lm = m === 0 ? 11 : m - 1, ly = m === 0 ? y - 1 : y;
    return { start: startOf(ly, lm), end: endOf(ly, lm), label: 'Last month' };
  }
  if (t === 'this quarter') return { start: qStart(y, currentQ), end: qEnd(y, currentQ), label: 'This quarter' };
  if (t === 'last quarter') {
    const lq = currentQ === 0 ? 3 : currentQ - 1, ly = currentQ === 0 ? y - 1 : y;
    return { start: qStart(ly, lq), end: qEnd(ly, lq), label: 'Last quarter' };
  }
  if (t === 'this year')    return { start: new Date(Date.UTC(y, 0, 1)), end: new Date(Date.UTC(y, 11, 31, 23, 59, 59, 999)), label: 'This year' };
  if (t === 'last year')    return { start: new Date(Date.UTC(y-1, 0, 1)), end: new Date(Date.UTC(y-1, 11, 31, 23, 59, 59, 999)), label: 'Last year' };
  if (t === 'next month') {
    const nm = m === 11 ? 0 : m + 1, ny = m === 11 ? y + 1 : y;
    return { start: startOf(y, m), end: endOf(ny, nm), label: 'Next month' };
  }
  if (t === 'next quarter') {
    const nq = currentQ === 3 ? 0 : currentQ + 1, ny = currentQ === 3 ? y + 1 : y;
    return { start: qStart(y, currentQ), end: qEnd(ny, nq), label: 'Next quarter' };
  }

  const d = new Date(text.trim() + 'T23:59:59Z');
  if (!isNaN(d)) return { start: null, end: d, label: `Close date ≤ ${text.trim()}` };

  return { start: null, end: null, label: 'All time' };
}

// ─── HubSpot helpers ────────────────────────────────────────────────────────────
async function fetchPipelineMap() {
  const res = await axios.get('https://api.hubapi.com/crm/v3/pipelines/deals', {
    headers: { Authorization: `Bearer ${HUBSPOT_TOKEN}` },
  });
  const map = {};
  for (const pipeline of res.data.results) {
    // Solo incluir pipelines que estén en TARGET_PIPELINES
    if (!TARGET_PIPELINES.some(t => matchesPipeline(pipeline.label, t))) continue;

    const stages = {};
    for (const stage of pipeline.stages) {
      stages[stage.id] = {
        label: stage.label,
        probability: parseFloat(stage.metadata?.probability ?? 0),
      };
    }
    map[pipeline.id] = { label: pipeline.label, stages };
  }
  return map;
}

async function fetchDeals(stageIds, { start, end }) {
  const filters = [{ propertyName: 'dealstage', operator: 'IN', values: stageIds }];
  if (start) filters.push({ propertyName: 'closedate', operator: 'GTE', value: String(start.getTime()) });
  if (end)   filters.push({ propertyName: 'closedate', operator: 'LTE', value: String(end.getTime()) });

  const deals = [];
  let after;
  while (true) {
    const res = await axios.post(
      'https://api.hubapi.com/crm/v3/objects/deals/search',
      {
        filterGroups: [{ filters }],
        properties: ['amount', 'dealstage', 'pipeline', 'closedate', 'hs_forecast_amount'],
        limit: 100,
        ...(after ? { after } : {}),
      },
      { headers: { Authorization: `Bearer ${HUBSPOT_TOKEN}`, 'Content-Type': 'application/json' } }
    );
    deals.push(...res.data.results);
    if (res.data.paging?.next?.after) after = res.data.paging.next.after;
    else break;
  }
  return deals;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────────
const fmt = val =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(parseFloat(val) || 0);

// Normaliza guiones y espacios para comparar: "Mid-Market" == "mid market"
const normalize = s => s.toLowerCase().replace(/[-_]/g, ' ').trim();
const matchesPipeline  = (label, target) => normalize(label).includes(normalize(target));
const matchesWonStage  = label => WON_STAGES.some(s => label.toLowerCase().includes(s));
const isExcludedStage  = label => EXCLUDE_FROM_REST.some(s => label.toLowerCase().includes(s));

const HELP = [
  '*Periodos disponibles:*',
  '`this month`  `last month`  `next month`',
  '`this quarter`  `last quarter`  `next quarter`',
  '`this year`  `last year`',
  '`2026-03-31`  (fecha específica)',
  '_(vacío)_ → todo el tiempo',
].join('\n');

const MAIN_HELP = [
  '*Comandos disponibles:*',
  '',
  '*Pipeline & forecast*',
  '• `/won [periodo]` — deals cerrados/Ready to Buy por pipeline',
  '• `/forecast [periodo]` — forecast ponderado por probabilidad',
  '',
  '*Análisis de MQLs*',
  '• `/mql` — lanza el asistente de análisis de MQLs (sube un CSV de HubSpot)',
  '  - *MQL Analysis* — MQLs estancados (no cualificados por AE)',
  '  - *Funnel MQL* — todos los MQLs: nurturing, Not ICP, SQL/Opportunity',
  '',
  '*Periodos para /won y /forecast:*',
  '`this month`  `last month`  `this quarter`  `last quarter`  `this year`',
].join('\n');

// ─── /won ───────────────────────────────────────────────────────────────────────
app.command('/won', async ({ command, ack, respond }) => {
  await ack();

  const input = command.text?.trim();
  if (input === 'help') return respond({ response_type: 'ephemeral', text: HELP });

  const dateRange = parseDateRange(input);
  await respond({ response_type: 'ephemeral', text: `_Buscando deals (${dateRange.label})..._` });

  try {
    const pipelineMap = await fetchPipelineMap();

    // Solo stage IDs de pipelines target que sean Won/Ready to Buy
    const wonStageIds = [];
    for (const [, pipeline] of Object.entries(pipelineMap))
      for (const [id, stage] of Object.entries(pipeline.stages))
        if (matchesWonStage(stage.label)) wonStageIds.push(id);

    if (!wonStageIds.length)
      return respond({ response_type: 'ephemeral', text: 'No se encontraron etapas Ready to Buy / Won en los pipelines configurados.' });

    const deals = await fetchDeals(wonStageIds, dateRange);

    const totals = {};
    for (const deal of deals) {
      const pipeline = pipelineMap[deal.properties.pipeline];
      if (!pipeline) continue; // ignorar pipelines fuera de los target
      totals[pipeline.label] = (totals[pipeline.label] || 0) + (parseFloat(deal.properties.amount) || 0);
    }

    const lines = [`*Pipeline Summary — Ready to Buy & Won*`, `_${dateRange.label}_`, ''];
    let grandTotal = 0;

    for (const target of TARGET_PIPELINES) {
      const match  = Object.entries(totals).find(([l]) => matchesPipeline(l, target));
      const amount = match?.[1] ?? 0;
      const label  = match?.[0] ?? (target.charAt(0).toUpperCase() + target.slice(1));
      grandTotal  += amount;
      lines.push(`*${label}:* ${fmt(amount)}`);
    }

    lines.push('', `*Total: ${fmt(grandTotal)}*`);
    await respond({ response_type: 'in_channel', text: lines.join('\n') });

  } catch (err) {
    console.error(err?.response?.data || err.message);
    await respond({ response_type: 'ephemeral', text: `Error: ${err.message}` });
  }
});

// ─── /forecast ──────────────────────────────────────────────────────────────────
app.command('/forecast', async ({ command, ack, respond }) => {
  await ack();

  const input = command.text?.trim();
  if (input === 'help') return respond({ response_type: 'ephemeral', text: HELP });

  const dateRange = parseDateRange(input);
  await respond({ response_type: 'ephemeral', text: `_Calculando forecast (${dateRange.label})..._` });

  try {
    const pipelineMap = await fetchPipelineMap();

    // Todos los stage IDs de los pipelines target
    const allStageIds = [];
    for (const [, pipeline] of Object.entries(pipelineMap))
      allStageIds.push(...Object.keys(pipeline.stages));

    if (!allStageIds.length)
      return respond({ response_type: 'ephemeral', text: 'No se encontraron los pipelines configurados.' });

    const deals = await fetchDeals(allStageIds, dateRange);

    // weighted = Won + Ready to Buy (weighted by probability)
    // rest     = stages que NO son Won, Ready to Buy, ni Lost
    // Separar Won/Ready to Buy (100%) del resto del pipeline (×0.40)
    const wonAmounts  = {}; // Won + Ready to Buy → al 100%
    const restAmounts = {}; // otras stages activas → ×0.40

    for (const deal of deals) {
      const pipeline = pipelineMap[deal.properties.pipeline];
      if (!pipeline) continue;
      const stage  = pipeline.stages[deal.properties.dealstage];
      const label  = stage?.label ?? '';
      const amount = parseFloat(deal.properties.amount) || 0;
      const pLabel = pipeline.label;

      if (matchesWonStage(label)) {
        wonAmounts[pLabel] = (wonAmounts[pLabel] || 0) + amount;
      } else if (!isExcludedStage(label)) {
        restAmounts[pLabel] = (restAmounts[pLabel] || 0) + amount;
      }
    }

    const lines = [`*Forecast Summary*`, `_${dateRange.label}_`, ''];
    let totalWon = 0, totalRest = 0, totalForecast = 0;

    for (const target of TARGET_PIPELINES) {
      const matchW  = Object.entries(wonAmounts).find(([l]) => matchesPipeline(l, target));
      const matchR  = Object.entries(restAmounts).find(([l]) => matchesPipeline(l, target));
      const wAmt    = matchW?.[1] ?? 0;
      const rAmt    = matchR?.[1] ?? 0;
      const label   = matchW?.[0] ?? matchR?.[0] ?? (target.charAt(0).toUpperCase() + target.slice(1));
      const forecast = wAmt + (rAmt * 0.40);
      totalWon      += wAmt;
      totalRest     += rAmt;
      totalForecast += forecast;
      lines.push(`*${label}:* ${fmt(forecast)} _(won/rtb: ${fmt(wAmt)}  +  rest×0.40: ${fmt(rAmt * 0.40)})_`);
    }

    lines.push(
      '',
      `*Total Forecast: ${fmt(totalForecast)}*`,
      `_Won + Ready to Buy: ${fmt(totalWon)}  |  Rest ×0.40: ${fmt(totalRest * 0.40)}_`,
    );

    await respond({ response_type: 'in_channel', text: lines.join('\n') });

  } catch (err) {
    console.error(err?.response?.data || err.message);
    await respond({ response_type: 'ephemeral', text: `Error: ${err.message}` });
  }
});

// ─── /help ───────────────────────────────────────────────────────────────────────
app.command('/help', async ({ ack, respond }) => {
  await ack();
  await respond({ response_type: 'ephemeral', text: MAIN_HELP });
});

// ─── /mql — analysis type selector ───────────────────────────────────────────────
app.command('/mql', async ({ command, ack, respond }) => {
  await ack();
  const arg = (command.text || '').trim().toLowerCase();

  if (arg === 'analysis' || arg === 'funnel') {
    const userId = command.user_id;
    const channel = command.channel_id;
    pendingAnalysis.set(userId, { type: arg === 'analysis' ? 'mql' : 'funnel', channel });
    const label = arg === 'analysis' ? 'MQL Analysis (estancados)' : 'Funnel MQL (todos los stages)';
    await respond({ response_type: 'ephemeral', text: `✅ *${label}* seleccionado. Ahora sube el CSV de HubSpot en este canal.` });
  } else {
    await respond({
      response_type: 'ephemeral',
      text: [
        '*¿Qué análisis quieres realizar?*',
        '',
        '• `/mql analysis` — MQLs estancados (no cualificados por AE)',
        '• `/mql funnel` — Todos los MQLs: nurturing, Not ICP, SQL/Opportunity',
        '',
        'Después de seleccionar, sube el CSV exportado de HubSpot.',
      ].join('\n'),
    });
  }
});

// ─── Button handler ───────────────────────────────────────────────────────────────
app.action(/mql_select_/, async ({ body, ack, client }) => {
  await ack();
  const type = body.actions[0].value;
  const userId = body.user.id;
  const channel = body.channel.id;

  pendingAnalysis.set(userId, { type, channel });

  const label = type === 'mql' ? 'MQL Analysis (MQLs estancados)' : 'Funnel MQL (todos los stages)';
  await client.chat.postEphemeral({
    channel,
    user: userId,
    text: `✅ Seleccionado: *${label}*\nAhora sube el CSV de HubSpot en este canal y lo procesaré automáticamente.`,
  });
});

// ─── Helper: send message (ephemeral in channels, normal in DMs) ──────────────────
async function notify(client, channel, userId, text) {
  const isDM = channel.startsWith('D');
  if (isDM) {
    await client.chat.postMessage({ channel: userId, text });
  } else {
    await client.chat.postEphemeral({ channel, user: userId, text });
  }
}

// ─── Shared file processing logic ────────────────────────────────────────────────
async function processUploadedFile(client, userId, channel, fileId) {
  const pending = pendingAnalysis.get(userId);
  if (!pending) return;

  pendingAnalysis.delete(pending ? userId : null);
  const { type } = pending;
  const label = type === 'mql' ? 'MQL Analysis' : 'Funnel MQL';

  try {
    const fileInfo = await client.files.info({ file: fileId });
    const file = fileInfo.file;

    if (!file.name.endsWith('.csv')) {
      return notify(client, channel, userId, '⚠️ El archivo debe ser un CSV. Usa `/mql` para reiniciar.');
    }

    await notify(client, channel, userId, `⏳ Procesando *${file.name}*...`);

    const tmpCsv = path.join(os.tmpdir(), `mql_${Date.now()}.csv`);
    const response = await axios.get(file.url_private_download, {
      headers: { Authorization: `Bearer ${process.env.SLACK_BOT_TOKEN}` },
      responseType: 'arraybuffer',
    });
    fs.writeFileSync(tmpCsv, response.data);

    const scriptPath = SCRIPTS[type];
    await new Promise((resolve, reject) => {
      execFile('C:\\Python314\\python.exe', [scriptPath, tmpCsv, OUTPUT_DIR], (err, stdout, stderr) => {
        if (err) return reject(new Error(stderr || err.message));
        resolve(stdout);
      });
    });

    const files = fs.readdirSync(OUTPUT_DIR)
      .filter(f => f.endsWith('.pdf'))
      .map(f => ({ name: f, mtime: fs.statSync(path.join(OUTPUT_DIR, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime);

    if (!files.length) throw new Error('No se generó ningún PDF.');

    const pdfPath = path.join(OUTPUT_DIR, files[0].name);
    await client.filesUploadV2({
      channel_id: channel,
      file: fs.createReadStream(pdfPath),
      filename: files[0].name,
      initial_comment: `📊 *${label}* completado. Aquí tienes el reporte:`,
    });

    fs.unlinkSync(tmpCsv);
  } catch (err) {
    console.error('MQL analysis error:', err.message);
    await notify(client, channel, userId, `❌ Error al procesar el análisis: ${err.message}`);
  }
}

// ─── File upload handler (channels via file_shared) ──────────────────────────────
app.event('file_shared', async ({ event, client }) => {
  const userId = event.user_id;
  if (!pendingAnalysis.has(userId)) return;
  const channel = event.channel_id || pendingAnalysis.get(userId).channel;
  await processUploadedFile(client, userId, channel, event.file_id);
});

// ─── File upload handler (DMs and group DMs via message) ─────────────────────────
async function handleMessageWithFile(event, client) {
  if (!event.files || event.files.length === 0) return;
  if (event.bot_id) return; // ignore bot messages
  const userId = event.user;
  if (!pendingAnalysis.has(userId)) return;
  const channel = event.channel;
  const fileId = event.files[0].id;
  await processUploadedFile(client, userId, channel, fileId);
}

app.event('message', async ({ event, client }) => {
  if (event.channel_type === 'im' || event.channel_type === 'mpim') {
    await handleMessageWithFile(event, client);
  }
});


// ─── Start ───────────────────────────────────────────────────────────────────────
(async () => {
  await app.start();
  console.log('Bot conectado a Slack via Socket Mode');
})();
