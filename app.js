/* NL Defence Speaking Trainer
 * - Service selection: Landmacht / Luchtmacht / Marine
 * - Modes: classification-only, classification + naming
 * - Classification-only uses Next (keeps feedback visible)
 * - Responsive images + click-to-zoom fullscreen
 */

const SERVICES = [
  { id: 'landmacht', label: 'Landmacht' },
  { id: 'luchtmacht', label: 'Luchtmacht' },
  { id: 'marine', label: 'Marine' },
];

let DATA = null;

const state = {
  service: null,
  mode: null,
  queue: [],
  idx: 0,
  streak: 0,
  bestStreak: 0,
  correct: 0,
  answered: 0,
  // per-question
  stage: 'class', // 'class' or 'name' (only in combo mode)
  locked: false,
  pendingReveal: false,
  pickedClass: null,
};

// Older versions used <div id="app">. Current HTML uses <section id="screen">.
// Fall back safely so the app doesn't crash if the markup differs.
const elApp = document.getElementById('app') || document.getElementById('screen') || document.body;
const elTheoryModal = document.getElementById('theoryModal');
const elTheoryContent = document.getElementById('theoryContent');
const elImageModal = document.getElementById('imageModal');
const elZoomImg = document.getElementById('zoomImg');

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pickN(pool, n, mustInclude = null) {
  const a = pool.slice();
  if (mustInclude != null) {
    const idx = a.indexOf(mustInclude);
    if (idx >= 0) a.splice(idx, 1);
  }
  const picked = shuffle(a).slice(0, Math.max(0, n - (mustInclude != null ? 1 : 0)));
  if (mustInclude != null) picked.push(mustInclude);
  return shuffle(picked);
}

function serviceLabel(id) {
  return (SERVICES.find(s => s.id === id) || {}).label || id;
}

async function loadService(serviceId) {
  const url = `data/${serviceId}.json`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Could not load ${url}`);
  DATA = await res.json();
}

function resetRound() {
  state.queue = [];
  state.idx = 0;
  state.stage = 'class';
  state.locked = false;
  state.pendingReveal = false;
  state.pickedClass = null;

  if (!DATA || !Array.isArray(DATA.questions) || DATA.questions.length === 0) {
    return;
  }

  const n = Math.min(DATA.quizLength || 10, DATA.questions.length);
  state.queue = shuffle(DATA.questions).slice(0, n);
}

function resetStats() {
  state.streak = 0;
  state.bestStreak = 0;
  state.correct = 0;
  state.answered = 0;
}

function topBar() {
  const total = (DATA && DATA.quizLength) ? Math.min(DATA.quizLength, (DATA.questions || []).length) : 0;
  const current = state.queue.length ? Math.min(state.idx, state.queue.length) : 0;

  return `
    <header class="topbar">
      <div class="brand">
        <div class="title">NL Defence Speaking Trainer</div>
        <div class="subtitle">${state.service ? `${serviceLabel(state.service)} · ${total} questions` : 'Choose a branch'}</div>
      </div>
      <div class="top-actions">
        <div class="pill">Round: <strong>${current}/${state.queue.length || total}</strong></div>
        <button class="btn" id="btnChange">Change practice</button>
        <button class="btn" id="btnNew">New round</button>
        <button class="btn" id="btnReset">Reset</button>
      </div>
    </header>
  `;
}

function startScreen() {
  const serviceButtons = SERVICES.map(s => {
    const active = state.service === s.id ? 'active' : '';
    return `<button class="btn choice ${active}" data-service="${s.id}">${s.label}</button>`;
  }).join('');

  const modeButtons = `
    <button class="btn choice" data-mode="class">Classification only</button>
    <button class="btn choice" data-mode="combo">Classification + naming</button>
  `;

  return `
    ${topBar()}
    <main class="wrap">
      <section class="card">
        <h2>What do you want to practise today?</h2>
        <p class="muted">Step 1: choose branch. Step 2: choose mode.</p>

        <div class="block">
          <div class="block-title">Branch</div>
          <div class="choices">${serviceButtons}</div>
        </div>

        <div class="block ${state.service ? '' : 'disabled'}">
          <div class="block-title">Mode</div>
          <div class="choices">${modeButtons}</div>
          <p class="tip">Tip: keep speaking while you choose. Use the prompts under the image.</p>
          <div class="actions-row">
            <button class="btn" id="btnTheory">Theory</button>
            <button class="btn primary" id="btnStart" ${state.service ? '' : 'disabled'}>Start</button>
          </div>
        </div>

        <div class="small muted">
          Note: If you open this file via <code>file://</code>, some browsers block loading JSON. Use GitHub Pages or a local web server.
        </div>
      </section>
    </main>
  `;
}

function speakingPrompts() {
  return `
    <div class="prompts">
      <div class="prompts-title">Speak:</div>
      <ul>
        <li>I think it is a ____.</li>
        <li>It looks like ____ because it has ____.</li>
        <li>This platform is used for ____.</li>
      </ul>
    </div>
  `;
}

function renderQuestion() {
  if (!DATA || !state.queue.length) {
    return `
      ${topBar()}
      <main class="wrap"><section class="card"><h2>No items yet.</h2>
        <p class="muted">This branch has no questions loaded yet.</p>
      </section></main>
    `;
  }

  const q = state.queue[state.idx];
  const progress = Math.round((state.idx / state.queue.length) * 100);

  const imgSrc = q.asset ? `images/${q.asset}.jpg` : 'images/missing.jpg';
  const imgAltSrc = q.asset ? `images/${state.service}/${q.asset}.jpg` : null;

  const stepLabel = (state.mode === 'combo')
    ? (state.stage === 'class' ? 'Step: choose the classification.' : 'Step: choose the name.')
    : 'Step: choose the classification.';

  const answersBlock = renderChoices(q);

  const feedback = state.pendingReveal ? `<div class="feedback">${state.pendingReveal}</div>` : '';

  return `
    ${topBar()}
    <main class="wrap">
      <section class="card">
        <div class="progress">
          <div class="progress-label">Progress: ${progress}%</div>
          <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
        </div>

        <div class="media">
          <img id="mainImage" class="zoomable" src="${imgSrc}" data-alt="${imgAltSrc || ''}" alt="${q.answer || 'vehicle'}" onerror="if(this.dataset.alt && !this.dataset.tried){this.dataset.tried='1'; this.src=this.dataset.alt;} else {this.onerror=null; this.src='images/missing.jpg';}" />
        </div>

        <div class="stats">
          <span class="badge">✅ ${state.correct}</span>
          <span class="badge">🔥 Streak ${state.streak} (best ${state.bestStreak})</span>
        </div>

        ${speakingPrompts()}

        <div class="step">${stepLabel}</div>

        ${feedback}

        ${answersBlock}

        <div class="footer">
          <div class="small muted">Correct: ${state.correct}/${state.answered || 0}</div>
          <button class="btn primary" id="btnNext" ${shouldShowNext() ? '' : 'style="display:none"'}>Next</button>
        </div>
      </section>
    </main>
  `;
}

function shouldShowNext() {
  if (state.mode === 'class') {
    return !!state.locked; // after answering, show Next
  }
  // combo mode uses Next only at end-of-round results (existing flow), so hide here
  return false;
}

function renderChoices(q) {
  const optionCount = DATA.mcqOptions || 6;

  if (state.mode === 'combo' && state.stage === 'name') {
    // Name options
    const allNames = (DATA.questions || []).map(x => x.answer).filter(Boolean);
    const options = pickN(allNames, optionCount, q.answer);
    return `
      <div class="grid">
        ${options.map(opt => `<button class="btn option" data-name="${escapeHtml(opt)}">${escapeHtml(opt)}</button>`).join('')}
      </div>
    `;
  }

  // Classification options
  const classes = DATA.vehicleClasses || [];
  const options = pickN(classes, optionCount, q.class);
  return `
    <div class="grid">
      ${options.map(opt => `<button class="btn option" data-class="${escapeHtml(opt)}">${escapeHtml(opt)}</button>`).join('')}
    </div>
  `;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function render() {
  if (!state.service || !state.mode) {
    elApp.innerHTML = startScreen();
    wireStartScreen();
    wireTopButtons();
    return;
  }

  elApp.innerHTML = '';
  elApp.innerHTML = renderQuestion();

  wireTopButtons();
  wireQuestion();
  wireZoom();
}

function wireTopButtons() {
  const btnChange = document.getElementById('btnChange');
  const btnNew = document.getElementById('btnNew');
  const btnReset = document.getElementById('btnReset');

  if (btnChange) {
    btnChange.onclick = async () => {
      state.service = null;
      state.mode = null;
      DATA = null;
      resetRound();
      render();
    };
  }

  if (btnNew) {
    btnNew.onclick = () => {
      resetRound();
      render();
    };
  }

  if (btnReset) {
    btnReset.onclick = () => {
      resetStats();
      resetRound();
      render();
    };
  }
}

function wireStartScreen() {
  document.querySelectorAll('[data-service]').forEach(btn => {
    btn.onclick = async () => {
      const service = btn.getAttribute('data-service');
      state.service = service;
      try {
        await loadService(service);
        // keep mode unset until chosen
      } catch (e) {
        console.error(e);
        alert(`Could not load data for ${service}`);
        state.service = null;
        DATA = null;
      }
      render();
    };
  });

  document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.onclick = () => {
      if (!state.service || !DATA) return;
      state.mode = btn.getAttribute('data-mode') === 'combo' ? 'combo' : 'class';
      // prep new round
      resetRound();
      state.stage = 'class';
      state.locked = false;
      state.pendingReveal = false;
      render();
    };
  });

  const btnStart = document.getElementById('btnStart');
  if (btnStart) {
    btnStart.onclick = () => {
      // no-op; mode buttons start immediately
    };
  }

  const btnTheory = document.getElementById('btnTheory');
  if (btnTheory) {
    btnTheory.onclick = () => {
      showTheory();
    };
  }
}

function showTheory() {
  if (!DATA) return;
  const items = (DATA.vehicleClasses || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');
  elTheoryContent.innerHTML = `
    <h2>Theory: classifications</h2>
    <p>These are the categories you need to know for ${escapeHtml(serviceLabel(state.service))}.</p>
    <ul>${items}</ul>
    <p class="muted">Close this window to start practising.</p>
  `;
  elTheoryModal.style.display = 'flex';
}

function hideTheory() {
  elTheoryModal.style.display = 'none';
}

function wireQuestion() {
  // option buttons
  document.querySelectorAll('[data-class]').forEach(btn => {
    btn.onclick = () => onPickClass(btn.getAttribute('data-class'));
  });
  document.querySelectorAll('[data-name]').forEach(btn => {
    btn.onclick = () => onPickName(btn.getAttribute('data-name'));
  });

  const btnNext = document.getElementById('btnNext');
  if (btnNext) {
    btnNext.onclick = () => {
      if (state.mode !== 'class') return;
      nextQuestion();
    };
  }
}

function lockOptions() {
  document.querySelectorAll('.option').forEach(b => b.disabled = true);
}

function markClassButtons(correctClass, chosenClass) {
  document.querySelectorAll('[data-class]').forEach(btn => {
    const v = btn.getAttribute('data-class');
    btn.classList.remove('correct', 'wrong');
    if (v === correctClass) btn.classList.add('correct');
    if (chosenClass && v === chosenClass && v !== correctClass) btn.classList.add('wrong');
  });
}

function markNameButtons(correctName, chosen) {
  document.querySelectorAll('[data-name]').forEach(btn => {
    const v = btn.getAttribute('data-name');
    btn.classList.remove('correct', 'wrong');
    if (v === correctName) btn.classList.add('correct');
    if (chosen && v === chosen && v !== correctName) btn.classList.add('wrong');
  });
}

function onPickClass(chosen) {
  if (state.locked) return;
  const q = state.queue[state.idx];

  state.answered += 1;
  const correct = chosen === q.class;
  if (correct) {
    state.correct += 1;
    state.streak += 1;
    state.bestStreak = Math.max(state.bestStreak, state.streak);
    state.pendingReveal = `✅ Correct: <strong>${escapeHtml(q.class)}</strong>`;
  } else {
    state.streak = 0;
    state.pendingReveal = `❌ Incorrect. Correct answer: <strong>${escapeHtml(q.class)}</strong>`;
  }

  lockOptions();
  markClassButtons(q.class, chosen);

  if (state.mode === 'combo') {
    // move to naming stage after short pause
    state.locked = true;
    setTimeout(() => {
      state.stage = 'name';
      state.locked = false;
      state.pendingReveal = ''; // naming stage: no extra line
      render();
    }, 550);
    return;
  }

  // classification-only: stay on screen and show Next
  state.locked = true;
  render();
}

function onPickName(chosen) {
  if (state.locked) return;
  const q = state.queue[state.idx];

  const correct = chosen === q.answer;
  if (correct) {
    state.pendingReveal = `✅ Correct name: <strong>${escapeHtml(q.answer)}</strong>`;
  } else {
    state.pendingReveal = `❌ Incorrect. Correct name: <strong>${escapeHtml(q.answer)}</strong>`;
    state.streak = 0;
  }

  lockOptions();
  markNameButtons(q.answer, chosen);
  state.locked = true;

  // proceed to next question after short pause
  setTimeout(() => {
    nextQuestion();
  }, 750);
}

function nextQuestion() {
  state.locked = false;
  state.pendingReveal = '';
  state.stage = 'class';

  state.idx += 1;
  if (state.idx >= state.queue.length) {
    // end of round
    state.idx = 0;
    resetRound();
  }
  render();
}

function wireZoom() {
  const img = document.getElementById('mainImage');
  if (!img) return;
  img.onclick = () => {
    const src = img.getAttribute('src');
    elZoomImg.setAttribute('src', src);
    elImageModal.style.display = 'flex';
  };
}

function hideImageModal() {
  elImageModal.style.display = 'none';
  elZoomImg.setAttribute('src', '');
}

// Modal wiring
(function wireModalsOnce() {
  // theory
  document.getElementById('btnCloseTheory')?.addEventListener('click', hideTheory);
  elTheoryModal?.addEventListener('click', (e) => {
    if (e.target === elTheoryModal) hideTheory();
  });

  // image
  document.getElementById('btnCloseImage')?.addEventListener('click', hideImageModal);
  elImageModal?.addEventListener('click', (e) => {
    if (e.target === elImageModal) hideImageModal();
  });
})();

// boot
resetStats();
render();
