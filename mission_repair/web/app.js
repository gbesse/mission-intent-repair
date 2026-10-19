const messages = {
  fr: {
    eyebrow: 'LABORATOIRE DE PLANIFICATION · SCÉNARIO SYNTHÉTIQUE',
    title: 'Une liaison perdue.\nUne mission à sauver.',
    lede: 'Coupez un relais, réduisez la batterie et recalculez le meilleur plan possible. Le passé reste figé ; chaque réparation est vérifiée par un rejeu indépendant.',
    inject: 'Injecter un imprévu',
    outage: 'Le relais principal est indisponible',
    battery: 'Capacité de la batterie',
    freeze:
      'Les tâches commencées avant t=4 sont figées. Une unité vaut ici 10 minutes ; énergie et données sont simplifiées.',
    solve: 'Réparer la mission →',
    input: 'Inspecter le scénario JSON',
    custom: 'Calculer ce JSON',
    timeline: 'Le plan après réparation',
    utility: 'utilité déclarée',
    edits: 'tâches modifiées',
    replay: 'rejeu indépendant',
    resources: 'Réserve d’énergie',
    units: 'unités arbitraires · pas de modèle orbital',
    changes: 'Ce qui change',
    download: 'Exporter la preuve JSON',
    limit:
      'Prototype de recherche : modèle discret synthétique, sans matériel ni commandes de vol. L’optimalité ne concerne que les contraintes et valeurs fournies. PlanDev et OR-Tools résolvent déjà des problèmes de planification ; ce lab explore la réparation avec passé figé et preuve indépendante.',
    busy: 'Recherche du plan…',
    optimal: 'OPTIMALITÉ DÉMONTRÉE',
    feasible: 'PLAN FAISABLE',
    infeasible: 'Aucun plan faisable sous ces hypothèses.',
    unknown: 'Limite de calcul atteinte sans plan.',
    valid: 'valide',
    none: 'Aucune modification nécessaire.',
    removed: 'retiré',
    added: 'ajouté',
    error: 'Entrée non valide ou serveur indisponible.',
    frozen: 'figé',
    ready: 'Plan calculé et rejoué.',
    noProof: 'Aucune preuve disponible.',
  },
  en: {
    eyebrow: 'PLANNING LAB · SYNTHETIC SCENARIO',
    title: 'One lost link.\nA mission to recover.',
    lede: 'Cut a relay, reduce the battery, and recompute the best possible plan. The past stays frozen; an independent replay checks every repair.',
    inject: 'Inject a disruption',
    outage: 'The primary relay is unavailable',
    battery: 'Battery capacity',
    freeze:
      'Tasks started before t=4 are frozen. One tick is 10 minutes; energy and data are simplified.',
    solve: 'Repair the mission →',
    input: 'Inspect the JSON scenario',
    custom: 'Solve this JSON',
    timeline: 'The repaired plan',
    utility: 'declared utility',
    edits: 'changed tasks',
    replay: 'independent replay',
    resources: 'Energy reserve',
    units: 'arbitrary units · no orbital model',
    changes: 'What changes',
    download: 'Export JSON evidence',
    limit:
      'Research prototype: a synthetic discrete model, without hardware or flight commands. Optimality applies only to the supplied constraints and values. PlanDev and OR-Tools already solve planning problems; this lab explores repair with a frozen past and independent evidence.',
    busy: 'Searching for a plan…',
    optimal: 'OPTIMALITY PROVEN',
    feasible: 'FEASIBLE PLAN',
    infeasible: 'No feasible plan under these assumptions.',
    unknown: 'Computation limit reached without a plan.',
    valid: 'valid',
    none: 'No changes needed.',
    removed: 'removed',
    added: 'added',
    error: 'Invalid input or server unavailable.',
    frozen: 'frozen',
    ready: 'Plan computed and replayed.',
    noProof: 'No evidence available.',
  },
  es: {
    eyebrow: 'LABORATORIO DE PLANIFICACIÓN · ESCENARIO SINTÉTICO',
    title: 'Un enlace perdido.\nUna misión que recuperar.',
    lede: 'Corta un relé, reduce la batería y calcula el mejor plan posible. El pasado queda fijo; una reproducción independiente comprueba cada reparación.',
    inject: 'Introducir un imprevisto',
    outage: 'El relé principal no está disponible',
    battery: 'Capacidad de la batería',
    freeze:
      'Las tareas iniciadas antes de t=4 quedan fijas. Cada paso son 10 minutos; energía y datos están simplificados.',
    solve: 'Reparar la misión →',
    input: 'Inspeccionar el escenario JSON',
    custom: 'Calcular este JSON',
    timeline: 'El plan reparado',
    utility: 'utilidad declarada',
    edits: 'tareas modificadas',
    replay: 'reproducción independiente',
    resources: 'Reserva de energía',
    units: 'unidades arbitrarias · sin modelo orbital',
    changes: 'Qué cambia',
    download: 'Exportar prueba JSON',
    limit:
      'Prototipo de investigación: modelo discreto sintético, sin hardware ni comandos de vuelo. La optimalidad solo abarca las restricciones y valores proporcionados. PlanDev y OR-Tools ya resuelven problemas de planificación; este laboratorio explora la reparación con pasado fijo y pruebas independientes.',
    busy: 'Buscando un plan…',
    optimal: 'OPTIMALIDAD DEMOSTRADA',
    feasible: 'PLAN FACTIBLE',
    infeasible: 'No hay un plan factible bajo estas hipótesis.',
    unknown: 'Límite de cálculo alcanzado sin plan.',
    valid: 'válido',
    none: 'No se necesitan cambios.',
    removed: 'retirado',
    added: 'añadido',
    error: 'Entrada no válida o servidor no disponible.',
    frozen: 'fijo',
    ready: 'Plan calculado y reproducido.',
    noProof: 'No hay pruebas disponibles.',
  },
};
const lang = new URLSearchParams(location.search).get('lang') || 'en';
const m = messages[lang] || messages.en;
document.documentElement.lang = messages[lang] ? lang : 'en';
document.querySelectorAll('[data-i18n]').forEach((el) => (el.textContent = m[el.dataset.i18n]));
document.querySelectorAll('nav a').forEach((a) => {
  if (a.textContent.toLowerCase() === document.documentElement.lang)
    a.setAttribute('aria-current', 'page');
});
const $ = (id) => document.getElementById(id);
let original, currentCase, evidence;
const elem = (tag, text, cls) => {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
};
function render(caseData, report) {
  evidence = { case: caseData, report };
  $('timeline').replaceChildren();
  $('changes').replaceChildren();
  $('chart').replaceChildren();
  const ok = report.plan !== null;
  $('utility').textContent = ok ? report.utility : '—';
  $('edits').textContent = ok ? report.changes.length : '—';
  $('replay').textContent = ok && report.replay.valid ? m.valid : '—';
  $('proof').textContent =
    report.status === 'OPTIMAL' ? m.optimal : ok ? m.feasible : report.status;
  $('status').textContent = ok
    ? m.ready
    : report.status === 'INFEASIBLE'
      ? m.infeasible
      : m.unknown;
  $('digest').textContent = report.input_sha256;
  for (const task of caseData.tasks) {
    const row = elem('div', undefined, 'task-row');
    row.append(elem('span', task.id, 'task-label'));
    const track = elem('div', undefined, 'track');
    const prior = caseData.previous?.[task.id];
    const addBar = (start, cls) => {
      const bar = elem('div', undefined, cls);
      bar.style.left = `${(100 * start) / caseData.horizon}%`;
      bar.style.width = `${(100 * task.duration) / caseData.horizon}%`;
      track.append(bar);
    };
    if (prior !== undefined) addBar(prior, 'bar old');
    if (ok && task.id in report.plan)
      addBar(report.plan[task.id], prior < (caseData.freeze_before || 0) ? 'bar frozen' : 'bar');
    row.append(track);
    $('timeline').append(row);
  }
  if (ok) {
    const points = report.replay.trace
      .map(
        (t) =>
          `${15 + (610 * t.tick) / caseData.horizon},${135 - (120 * t.battery) / Math.max(1, caseData.battery_capacity)}`,
      )
      .join(' ');
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    poly.setAttribute('points', points);
    poly.setAttribute('fill', 'none');
    poly.setAttribute('stroke', '#8ef0cc');
    poly.setAttribute('stroke-width', '2.5');
    $('chart').append(poly);
    for (const c of report.changes) {
      const row = elem('div', undefined, 'change');
      row.append(
        elem('span', c.task),
        elem('span', `${c.before ?? m.added} → ${c.after ?? m.removed}`),
      );
      $('changes').append(row);
    }
    if (!report.changes.length) $('changes').append(elem('p', m.none, 'hint'));
  } else {
    $('changes').append(elem('p', m.infeasible, 'hint'));
    for (const id of report.required_conflict || []) $('changes').append(elem('code', id));
  }
}
async function solve(custom = false) {
  $('solve').disabled = true;
  $('custom').disabled = true;
  $('status').textContent = m.busy;
  try {
    const caseData = custom ? JSON.parse($('case').value) : structuredClone(original);
    if (!custom) {
      caseData.battery_capacity = Number($('capacity').value);
      if ($('outage').checked) caseData.tasks.find((t) => t.id === 'relay-primary').windows = [];
      $('case').value = JSON.stringify(caseData, null, 2);
    }
    const res = await fetch('/api/repair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
    });
    if (!res.ok) throw Error();
    const report = await res.json();
    currentCase = caseData;
    render(caseData, report);
  } catch {
    evidence = null;
    $('status').textContent = m.error;
  } finally {
    $('solve').disabled = false;
    $('custom').disabled = false;
  }
}
$('capacity').addEventListener('input', () => {
  $('capacity-value').value = $('capacity').value;
});
$('solve').addEventListener('click', () => solve());
$('custom').addEventListener('click', () => solve(true));
$('download').addEventListener('click', () => {
  if (!evidence) {
    $('status').textContent = m.noProof;
    return;
  }
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(evidence, null, 2)], { type: 'application/json' }),
  );
  const a = elem('a');
  a.href = url;
  a.download = 'mission-repair-evidence.json';
  a.click();
  URL.revokeObjectURL(url);
});
try {
  const res = await fetch('/api/demo');
  if (!res.ok) throw Error();
  const data = await res.json();
  original = data.case;
  await solve();
} catch {
  $('status').textContent = m.error;
}
