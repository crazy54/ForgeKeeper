const services = [
  {
    name: 'VS Code Server',
    port: 8080,
    url: 'http://localhost:8080',
    description: 'Full VS Code accessible from any browser.',
    icon: '🛠️',
  },
  {
    name: 'OpenVSCode Server',
    port: 3000,
    url: 'http://localhost:3000',
    description: 'Lightweight VS Code build direct from Microsoft sources.',
    icon: '🧭',
  },
  {
    name: 'ForgeKeeper Portal',
    port: 7000,
    url: 'http://localhost:7000',
    description: 'You are here—bookmark for all hosted tooling.',
    icon: '🔥',
  },
  {
    name: 'JupyterLab',
    port: 8888,
    url: 'http://localhost:8888',
    description: 'Data notebooks with ForgeKeeper kernels baked in.',
    icon: '📓',
  },
  {
    name: 'ttyd Terminal',
    port: 7681,
    url: 'http://localhost:7681',
    description: 'Browser-based zsh/tmux session with personalized MOTD.',
    icon: '💻',
  },
  {
    name: 'MLflow UI',
    port: 5000,
    url: 'http://localhost:5000',
    description: 'Track experiments, parameters, and metrics.',
    icon: '📈',
  },
  {
    name: 'TensorBoard',
    port: 6006,
    url: 'http://localhost:6006',
    description: 'Visualize training runs and scalars.',
    icon: '🧠',
  },
];

const serviceGrid = document.getElementById('service-grid');
const typewriterEl = document.getElementById('typewriter');
const splashEl = document.getElementById('splash');
const progressFill = document.getElementById('progress-fill');
const shutdownButtons = [
  document.getElementById('shutdown-btn'),
  document.getElementById('shutdown-inline'),
];
const resetBtn = document.getElementById('reset-btn');
const workspaceName = document.getElementById('workspace-name');
const userEmailEl = document.getElementById('user-email');
const yearEl = document.getElementById('year');

const identity = {
  handle: window.FORGEKEEPER_HANDLE || 'forgekeeper',
  workspace: window.FORGEKEEPER_WORKSPACE || 'workspace',
  email: window.FORGEKEEPER_USER_EMAIL || 'ops@forgekeeper.io',
};

workspaceName.textContent = identity.workspace;
userEmailEl.textContent = identity.email;
yearEl.textContent = new Date().getFullYear();

function renderServices() {
  serviceGrid.innerHTML = '';
  for (const svc of services) {
    const card = document.createElement('article');
    card.className = 'service-card';
    card.innerHTML = `
      <div class="service-logo-tag">
        <img src="logo/Forge.png" alt="ForgeKeeper emblem" />
      </div>
      <div class="service-icon">${svc.icon}</div>
      <h3>${svc.name}</h3>
      <p class="service-desc">${svc.description}</p>
      <div class="service-meta">
        <span>Port ${svc.port}</span>
        <a href="${svc.url}" target="_blank" rel="noreferrer">Open →</a>
      </div>
    `;
    serviceGrid.appendChild(card);
  }
}

function typewriter(text, speed = 80) {
  return new Promise((resolve) => {
    let index = 0;
    const loop = () => {
      typewriterEl.textContent = text.slice(0, index);
      if (index < text.length) {
        index += 1;
        setTimeout(loop, speed);
      } else {
        resolve();
      }
    };
    loop();
  });
}

async function runSplashSequence() {
  await typewriter('Welcome to the Forge');
  await animateProgress();
  splashEl.classList.add('hidden');
}

function animateProgress() {
  return new Promise((resolve) => {
    let value = 0;
    const interval = setInterval(() => {
      value += Math.random() * 8;
      if (value >= 100) {
        value = 100;
        clearInterval(interval);
        setTimeout(resolve, 300);
      }
      progressFill.style.width = `${value}%`;
    }, 120);
  });
}

function attachControls() {
  shutdownButtons.forEach((btn) => {
    btn?.addEventListener('click', () => {
      const confirmed = confirm('Power down the ForgeKeeper container?');
      if (!confirmed) return;
      triggerControl('shutdown');
    });
  });

  resetBtn?.addEventListener('click', () => {
    const confirmed = confirm('Reset ForgeKeeper and clear all workspace data?');
    if (!confirmed) return;
    triggerControl('reset');
  });
}

async function triggerControl(action) {
  try {
    const response = await fetch('/forgekeeper/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    if (!response.ok) throw new Error('control endpoint unavailable');
    const result = await response.json();
    alert(result.message || `ForgeKeeper ${action} requested.`);
  } catch (error) {
    console.warn('Control request failed:', error);
    alert('Control endpoint is not wired up yet. Connect /forgekeeper/control to Docker/host orchestration.');
  }
}

renderServices();
attachControls();
runSplashSequence();
