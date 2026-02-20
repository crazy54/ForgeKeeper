// ForgeKeeper Setup Wizard — Flow A (pre-build) + Flow B (in-portal first-run)
// Detects which mode it's running in via window.FORGEKEEPER_SETUP_MODE

const MODE = window.FORGEKEEPER_SETUP_MODE || 'prebuild'; // 'prebuild' | 'portal'

// Use the page's own origin so the wizard works regardless of hostname/IP.
const API_BASE = MODE === 'portal' ? '' : window.location.origin;

// ── Cinematic intro sequence ──────────────────────────────────────────────────
// Timeline:
//  0.0s  logo fades in with glow
//  1.6s  line 1 starts typing: "Welcome to ForgeKeeper."
//  ~3.4s typing done → cursor blinks 3× → line fades out
//  4.8s  line 2 starts typing: "Let's customize your container in the Forge."
//  ~7.2s typing done → cursor blinks 3× → cursor stops
//  8.6s  intro overlay fades out, bg logo dims to 50%, wizard slides up

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function typeText(el, text, speed = 48) {
  for (const ch of text) {
    el.textContent += ch;
    await sleep(speed);
  }
}

async function blinkCursor(cursorEl, times = 3, interval = 420) {
  for (let i = 0; i < times * 2; i++) {
    cursorEl.style.opacity = i % 2 === 0 ? '0' : '1';
    await sleep(interval);
  }
  cursorEl.style.opacity = '1';
}

async function runIntro() {
  const intro      = document.getElementById('intro');
  const introLogo  = document.getElementById('intro-logo');
  const introLine  = document.getElementById('intro-line');
  const introTyped = document.getElementById('intro-typed');
  const introCursor = document.getElementById('intro-cursor');
  const bgLogo     = document.querySelector('.bg-logo');
  const wizardWrap = document.getElementById('wizard-wrap');

  // 1. Logo fades in
  await sleep(300);
  introLogo.classList.add('revealed');
  await sleep(1300);

  // 2. Show text line, type line 1
  introLine.classList.add('visible');
  await typeText(introTyped, 'Welcome to ForgeKeeper.', 52);
  await sleep(200);
  await blinkCursor(introCursor, 3);

  // 3. Fade out line 1, clear, type line 2
  introLine.classList.add('fade-out');
  await sleep(500);
  introTyped.textContent = '';
  introLine.classList.remove('fade-out');
  await sleep(100);

  await typeText(introTyped, "Let's customize your container in the Forge.", 44);
  await sleep(200);
  await blinkCursor(introCursor, 3);

  // 4. Stop cursor, pause, then dismiss intro
  introCursor.classList.add('stopped');
  await sleep(700);

  // 5. Fade out intro overlay, reveal bg logo + wizard simultaneously
  intro.classList.add('done');
  bgLogo.classList.add('visible');
  wizardWrap.removeAttribute('aria-hidden');
  await sleep(200); // slight stagger so wizard appears as intro fades
  wizardWrap.classList.add('revealed');

  // 6. Remove intro from DOM after transition completes
  await sleep(1000);
  intro.remove();
}

runIntro();

const LANGS = [
  { id: 'python', name: 'Python',     devicon: 'devicon-python-plain colored',     emoji: '🐍', size: '~4 GB' },
  { id: 'node',   name: 'Node.js',    devicon: 'devicon-nodejs-plain colored',     emoji: '🟩', size: '~1.2 GB' },
  { id: 'go',     name: 'Go',         devicon: 'devicon-go-plain colored',         emoji: '🐹', size: '~600 MB' },
  { id: 'rust',   name: 'Rust',       devicon: 'devicon-rust-plain',               emoji: '🦀', size: '~2 GB' },
  { id: 'java',   name: 'Java / JVM', devicon: 'devicon-java-plain colored',       emoji: '☕', size: '~800 MB' },
  { id: 'dotnet', name: '.NET / C#',  devicon: 'devicon-csharp-plain colored',     emoji: '💜', size: '~900 MB' },
  { id: 'ruby',   name: 'Ruby',       devicon: 'devicon-ruby-plain colored',       emoji: '💎', size: '~300 MB' },
  { id: 'php',    name: 'PHP',        devicon: 'devicon-php-plain colored',        emoji: '🐘', size: '~200 MB' },
  { id: 'swift',  name: 'Swift',      devicon: 'devicon-swift-plain colored',      emoji: '🍎', size: '~1.5 GB' },
  { id: 'dart',   name: 'Dart',       devicon: 'devicon-dart-plain colored',       emoji: '🎯', size: '~400 MB' },
];

let currentStep = 1;
const TOTAL_STEPS = MODE === 'prebuild' ? 4 : 3; // no build step in portal mode
let selectedLangs = new Set();
let buildLogInterval = null;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const stepLabel   = document.getElementById('step-label');
const backBtn     = document.getElementById('back-btn');
const nextBtn     = document.getElementById('next-btn');
const buildBtn    = document.getElementById('build-btn');
const buildLog    = document.getElementById('build-log');
const buildLogWrap = document.getElementById('build-log-wrap');
const buildDone   = document.getElementById('build-done');
const summaryBox  = document.getElementById('summary-box');

// ── Language grid ─────────────────────────────────────────────────────────────
function renderLangGrid() {
  const grid = document.getElementById('lang-grid');
  grid.innerHTML = '';
  for (const lang of LANGS) {
    const card = document.createElement('div');
    card.className = 'lang-card' + (selectedLangs.has(lang.id) ? ' selected' : '');
    card.dataset.id = lang.id;
    card.innerHTML = `
      <div class="lang-icon">
        <i class="${lang.devicon}" aria-hidden="true"></i>
        <span class="lang-emoji" aria-hidden="true">${lang.emoji}</span>
      </div>
      <div class="lang-name">${lang.name}</div>
      <div class="lang-size">${lang.size}</div>
    `;
    card.addEventListener('click', () => {
      if (selectedLangs.has(lang.id)) {
        selectedLangs.delete(lang.id);
        card.classList.remove('selected');
      } else {
        selectedLangs.add(lang.id);
        card.classList.add('selected');
      }
    });
    grid.appendChild(card);
  }

  // After render, check if devicons actually loaded. If the <i> has zero width
  // (font not loaded), show the emoji fallback instead.
  requestAnimationFrame(() => {
    grid.querySelectorAll('.lang-icon i').forEach(el => {
      if (el.getBoundingClientRect().width === 0) {
        el.style.display = 'none';
        el.nextElementSibling.style.display = 'block';
      }
    });
  });
}

// ── Step navigation ───────────────────────────────────────────────────────────
function showStep(n, direction = 'forward') {
  const viewport = document.getElementById('step-viewport');
  const outgoing = document.querySelector('.step.active');
  const incoming = document.getElementById(`step-${n}`);
  if (!incoming || outgoing === incoming) return;

  const outClass = direction === 'forward' ? 'slide-out-left'  : 'slide-out-right';
  const inClass  = direction === 'forward' ? 'slide-in-right'  : 'slide-in-left';

  // Lock viewport height to current step so card doesn't resize mid-animation
  viewport.style.height = outgoing.offsetHeight + 'px';

  // Outgoing: make absolute so incoming can take normal flow
  outgoing.classList.remove('active');
  outgoing.classList.add(outClass);
  outgoing.addEventListener('animationend', () => {
    outgoing.classList.remove(outClass);
    outgoing.style.display = 'none';
  }, { once: true });

  // Incoming: start off-screen (handled by keyframe), animate in
  incoming.style.display = 'block';
  incoming.classList.add(inClass);
  incoming.addEventListener('animationend', () => {
    incoming.classList.remove(inClass);
    incoming.classList.add('active');
    // Release locked height once incoming is settled
    viewport.style.height = '';
  }, { once: true });

  // Update step dots and labels
  document.querySelectorAll('.step-dot').forEach(dot => {
    const s = parseInt(dot.dataset.step);
    dot.classList.remove('active', 'done');
    if (s < n) dot.classList.add('done');
    else if (s === n) dot.classList.add('active');
  });

  stepLabel.textContent = `Step ${n} of ${TOTAL_STEPS} — ${stepNames[n]}`;
  backBtn.style.visibility = n === 1 ? 'hidden' : 'visible';

  const isLastStep = n === TOTAL_STEPS;
  nextBtn.style.display = isLastStep ? 'none' : 'inline-flex';
  if (isLastStep) {
    renderSummary();
    if (MODE === 'prebuild') setBuildState('idle');
  }
}

const stepNames = {
  1: 'Identity',
  2: 'Languages',
  3: 'Credentials',
  4: MODE === 'prebuild' ? 'Build' : 'Confirm',
};

function collectConfig() {
  return {
    handle:        document.getElementById('handle')?.value.trim() || 'forgekeeper',
    email:         document.getElementById('email')?.value.trim() || 'dev@example.com',
    workspace:     document.getElementById('workspace')?.value.trim() || 'workspace',
    git_name:      document.getElementById('git_name')?.value.trim() || '',
    git_email:     document.getElementById('git_email')?.value.trim() || '',
    github_token:  document.getElementById('github_token')?.value.trim() || '',
    openai_key:    document.getElementById('openai_key')?.value.trim() || '',
    anthropic_key: document.getElementById('anthropic_key')?.value.trim() || '',
    aws_region:    document.getElementById('aws_region')?.value.trim() || 'us-east-1',
    languages:     [...selectedLangs],
  };
}

function renderSummary() {
  const cfg = collectConfig();
  const langList = cfg.languages.length
    ? cfg.languages.map(l => LANGS.find(x => x.id === l)?.name || l).join(', ')
    : 'None selected (base image only)';
  const creds = [
    cfg.openai_key    ? '✓ OpenAI'    : '',
    cfg.anthropic_key ? '✓ Anthropic' : '',
    cfg.github_token  ? '✓ GitHub'    : '',
    cfg.aws_region    ? `✓ AWS (${cfg.aws_region})` : '',
  ].filter(Boolean).join(' · ') || 'None';

  summaryBox.innerHTML = `
    <strong>Handle:</strong> ${cfg.handle}<br/>
    <strong>Email:</strong> ${cfg.email}<br/>
    <strong>Workspace:</strong> ${cfg.workspace}<br/>
    <strong>Languages:</strong> ${langList}<br/>
    <strong>Credentials:</strong> ${creds}
  `;
}

// ── Forging overlay quips ─────────────────────────────────────────────────────
const QUIPS = {
  python: [
    "Counting indentation spaces… all 4 of them.",
    "Asking the snake to hold still while we install it.",
    "pip install everything. Yes, everything.",
    "Activating virtual environment. No, the other one.",
    "Python 2 is dead. We don't talk about Python 2.",
    "Teaching the snake new tricks. It's resistant.",
    "import antigravity — still doesn't work in Docker.",
  ],
  node: [
    "Downloading node_modules… estimated 847,000 files.",
    "npm audit found 0 vulnerabilities. Just kidding.",
    "Telling JavaScript it can be a real language someday.",
    "node_modules is now larger than the observable universe.",
    "Callback hell has been replaced with async/await hell.",
    "package-lock.json has been updated. Nobody knows why.",
    "Webpack is thinking. It's always thinking.",
  ],
  go: [
    "Compiling Go. Done. That was fast.",
    "Gopher wrangled. Channels opened.",
    "go build succeeded before you finished reading this.",
    "No generics needed. Wait, they added generics. Nevermind.",
    "Error handling: if err != nil { if err != nil { if err != nil {",
    "The gopher is very small but very fast. Respect the gopher.",
  ],
  rust: [
    "Borrow checker is judging your life choices.",
    "Convincing the compiler you own this memory.",
    "Rust is safe. The compiler just needs to be sure. Very sure.",
    "Rewriting it in Rust. As is tradition.",
    "Lifetime annotations: because 'a is a perfectly normal variable name.",
    "The borrow checker has opinions. Many opinions.",
    "unsafe { /* here be dragons */ } — we left this out.",
  ],
  java: [
    "Warming up the JVM. Should be ready by Tuesday.",
    "Allocating heap space. And more heap. And more.",
    "Enterprise-grade XML config incoming.",
    "AbstractSingletonProxyFactoryBean has entered the chat.",
    "Maven is resolving dependencies from 2009.",
    "Spring Boot is booting. It takes a moment. Or several.",
    "Checked exceptions: because Java cares about your feelings.",
  ],
  dotnet: [
    "NuGet restore: downloading the internet.",
    "C# is just Java with better marketing.",
    "Spinning up the CLR. It's very excited.",
    "Visual Studio would take 45 minutes to do this. We're faster.",
    "LINQ query optimized. Probably.",
    ".NET 9 is here. .NET 10 is already in preview.",
  ],
  ruby: [
    "Bundler is bundling. Gems are gemming.",
    "Matz is probably happy about this.",
    "Installing Ruby. It's elegant, we promise.",
    "Convention over configuration. Mostly.",
    "Rails is magic. Don't look behind the curtain.",
    "Everything is an object. Even nil. Especially nil.",
  ],
  php: [
    "PHP: it works and you know it.",
    "Deploying to /var/www/html like it's 2008.",
    "<?php echo 'almost ready'; ?>",
    "PHP 8 is actually pretty good. We said it.",
    "Composer is composing. Artisan is artisaning.",
    "WordPress not included. You're welcome.",
  ],
  swift: [
    "Xcode not required. You're welcome.",
    "Swift is fast. The installer is… less so.",
    "Cupertino approved this message.",
    "Optionals: because nil should be explicit and painful.",
    "Protocol-oriented programming. It's a whole thing.",
    "SwiftUI is declarative. The errors are not.",
  ],
  dart: [
    "Flutter is watching. Dart is ready.",
    "pub get: fetching packages from the pub.",
    "Dart: because someone had to.",
    "Hot reload incoming. It's the best part.",
    "Dart is typed. Flutter is pretty. Together they're unstoppable.",
  ],
  _default: [
    "Heating up the forge…",
    "Assembling your Dockerfile…",
    "Writing your .env to disk…",
    "Almost there, hammering the last bits into shape.",
    "Sharpening the tools…",
    "Stoking the fire…",
    "The forge doesn't rush. But it is going fast.",
    "Checking the blueprints one more time…",
  ],
};

// Quips that use user-provided variables — populated at runtime
function personalQuips(cfg) {
  const handle    = cfg.handle    || 'friend';
  const workspace = cfg.workspace || 'this project';
  const email     = cfg.email     || 'someone@example.com';
  const gitName   = cfg.git_name  || handle;
  const region    = cfg.aws_region || 'us-east-1';
  const langCount = cfg.languages.length;
  const langWord  = langCount === 1 ? 'language' : 'languages';

  return [
    `TIL: Your name is "${handle}". Does your mom call you that?`,
    `"${workspace}" — bold name. We respect it.`,
    `Sending a postcard to ${email}. Just kidding, we don't do that.`,
    `Hey ${handle}, your container is going to be legendary.`,
    `${gitName} has entered the building. Git blame will never be the same.`,
    `Deploying to ${region}. Classic choice, ${handle}.`,
    langCount === 0
      ? `${handle} chose zero languages. Living dangerously.`
      : `${langCount} ${langWord} selected. ${handle} means business.`,
    `"${workspace}" will be the name they whisper in the halls of engineering.`,
    `${handle}: the developer. The myth. The Dockerfile.`,
    langCount > 3
      ? `${langCount} languages? ${handle}, are you okay?`
      : `Solid picks, ${handle}. Quality over quantity.`,
    `git config user.name "${gitName}" — posterity will know who to blame.`,
    `${handle}'s forge is almost ready. Stand back.`,
  ];
}

function getQuips(langs, cfg) {
  const pool = [...QUIPS._default, ...personalQuips(cfg)];
  for (const l of langs) if (QUIPS[l]) pool.push(...QUIPS[l]);
  // Fisher-Yates shuffle
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool;
}

async function showForgingOverlay(langs, cfg) {
  const overlay = document.getElementById('forging-overlay');
  const quipEl  = document.getElementById('forging-quip');
  overlay.hidden = false;

  const quips = getQuips(langs, cfg);
  let idx = 0;

  quipEl.textContent = quips[idx];

  const interval = setInterval(() => {
    quipEl.style.opacity = '0';
    setTimeout(() => {
      idx = (idx + 1) % quips.length;
      quipEl.textContent = quips[idx];
      quipEl.style.opacity = '1';
    }, 400);
  }, 2200);

  return () => {
    clearInterval(interval);
    overlay.hidden = true;
  };
}

async function submitConfig() {
  const cfg = collectConfig();
  const res = await fetch(`${API_BASE}/setup/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  });
  return res.ok;
}

// ── Build nav state machine ───────────────────────────────────────────────────
// States: idle | building | stopped | done
const cleanupBtn = document.getElementById('cleanup-btn');

function setBuildState(state) {
  const cleanupStatus = document.getElementById('cleanup-status');
  switch (state) {
    case 'idle':
      // Normal step-4 view: Back visible, Next hidden (last step), no cleanup
      backBtn.style.visibility = 'visible';
      backBtn.textContent = '← Back';
      backBtn.classList.remove('danger');
      backBtn.disabled = false;
      backBtn.onclick = null;
      cleanupBtn.style.display = 'none';
      buildBtn.disabled = false;
      break;

    case 'building':
      // Back → Stop, Next hidden, Forge disabled
      backBtn.style.visibility = 'visible';
      backBtn.textContent = '⛔ Stop Build';
      backBtn.classList.add('danger');
      backBtn.disabled = false;
      backBtn.onclick = (e) => { e.stopImmediatePropagation(); doStop(); };
      cleanupBtn.style.display = 'none';
      buildBtn.disabled = true;
      document.getElementById('build-btn-text').textContent = '⏳ Forging…';
      break;

    case 'stopped':
      // Back → normal back, Cleanup appears, Forge re-enables
      backBtn.style.visibility = 'visible';
      backBtn.textContent = '← Back';
      backBtn.classList.remove('danger');
      backBtn.disabled = false;
      backBtn.onclick = null;
      cleanupBtn.style.display = 'inline-flex';
      buildBtn.disabled = false;
      document.getElementById('build-btn-text').textContent = '🔥 Forge Container 🔨';
      break;

    case 'done':
      // Back hidden, Cleanup stays available
      backBtn.style.visibility = 'hidden';
      backBtn.classList.remove('danger');
      backBtn.onclick = null;
      cleanupBtn.style.display = 'inline-flex';
      buildBtn.disabled = true;
      document.getElementById('build-btn-text').textContent = '✅ Forged';
      break;
  }
}

async function doStop() {
  backBtn.disabled = true;
  backBtn.textContent = '⏳ Stopping…';
  clearInterval(buildLogInterval);
  try {
    await fetch(`${API_BASE}/setup/stop`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    buildLog.textContent += '\n[setup] Build stopped by user.';
    buildLog.scrollTop = buildLog.scrollHeight;
  } catch (_) {}
  setBuildState('stopped');
}

cleanupBtn?.addEventListener('click', async () => {
  const cleanupStatus = document.getElementById('cleanup-status');
  cleanupBtn.disabled = true;
  cleanupBtn.textContent = '⏳ Cleaning…';
  cleanupStatus.style.display = 'block';
  cleanupStatus.textContent = 'Running docker system prune on dangling build artifacts…';
  try {
    const res = await fetch(`${API_BASE}/setup/cleanup`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const data = await res.json();
    cleanupStatus.textContent = data.message || 'Cleanup complete.';
    cleanupBtn.textContent = '✅ Cleaned Up';
  } catch (_) {
    cleanupStatus.textContent = 'Cleanup failed — try: docker system prune -f';
    cleanupBtn.disabled = false;
    cleanupBtn.textContent = '🧹 Clean Up';
  }
});

// ── Build (Flow A only) ───────────────────────────────────────────────────────
async function startBuild() {
  setBuildState('building');
  buildLogWrap.style.display = 'block';

  await fetch(`${API_BASE}/setup/build`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });

  buildLogInterval = setInterval(async () => {
    const res = await fetch(`${API_BASE}/setup/build-log`);
    const data = await res.json();
    buildLog.textContent = data.log.join('\n');
    buildLog.scrollTop = buildLog.scrollHeight;
    if (data.done) {
      clearInterval(buildLogInterval);
      const portalUrl = `${window.location.protocol}//${window.location.hostname}:7000`;
      buildDone.innerHTML = `✅ Build complete! Open <a href="${portalUrl}" target="_blank">${portalUrl}</a> to launch the portal.`;
      buildDone.style.display = 'block';
      setBuildState('done');
    }
  }, 1500);
}

// ── Portal mode: mark setup complete ─────────────────────────────────────────
async function markSetupComplete(cfg) {
  await fetch('/forgekeeper/setup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  });
}

// ── Event listeners ───────────────────────────────────────────────────────────
let submitting = false;
nextBtn.addEventListener('click', async () => {
  if (submitting) return;

  if (currentStep === TOTAL_STEPS - 1) {
    submitting = true;
    nextBtn.disabled = true;

    const dismissOverlay = await showForgingOverlay([...selectedLangs], collectConfig());
    const ok = await submitConfig();
    dismissOverlay();

    nextBtn.disabled = false;
    submitting = false;

    if (!ok) { alert('Failed to save config. Is the setup server running?'); return; }
  }

  if (currentStep < TOTAL_STEPS) {
    currentStep++;
    showStep(currentStep, 'forward');
  }
});

backBtn.addEventListener('click', () => {
  // During a build the onclick handler on backBtn is set to doStop — let it handle it
  if (backBtn.onclick) return;
  if (currentStep > 1) { currentStep--; showStep(currentStep, 'backward'); }
});

buildBtn?.addEventListener('click', async () => {
  if (MODE === 'prebuild') {
    await startBuild();
  } else {
    // Portal mode — mark complete and redirect
    const cfg = collectConfig();
    await markSetupComplete(cfg);
    window.location.href = '/';
  }
});

// ── Enter key advances from last field in each step ──────────────────────────
function bindEnterKey() {
  // Map of last-input-id → step number it belongs to
  const lastFields = { workspace: 1, aws_region: 3 };
  for (const [id, step] of Object.entries(lastFields)) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && currentStep === step && currentStep < TOTAL_STEPS) {
        e.preventDefault();
        nextBtn.click();
      }
    });
  }
}
bindEnterKey();

// ── Init ──────────────────────────────────────────────────────────────────────
renderLangGrid();
// First step: show directly, no animation
const firstStep = document.getElementById('step-1');
if (firstStep) { firstStep.style.display = 'block'; firstStep.classList.add('active'); }
document.querySelector('.step-dot[data-step="1"]')?.classList.add('active');

if (MODE === 'portal' && buildBtn) {
  document.getElementById('build-btn-text').textContent = '✅ Complete Setup';
}
