const services = [
  // ── IDEs & Editors ──────────────────────────────────────────────────────────
  {
    category: 'IDEs & Editors',
    name: 'VS Code Server',
    port: 8080,
    url: 'http://localhost:8080',
    description: 'Full VS Code accessible from any browser.',
    icon: '🛠️',
  },
  {
    category: 'IDEs & Editors',
    name: 'OpenVSCode Server',
    port: 3000,
    url: 'http://localhost:3000',
    description: 'Lightweight VS Code build direct from Microsoft sources.',
    icon: '🧭',
  },

  // ── Terminals ───────────────────────────────────────────────────────────────
  {
    category: 'Terminals',
    name: 'ttyd Terminal',
    port: 7681,
    url: 'http://localhost:7681',
    description: 'Browser-based zsh/tmux session with personalized MOTD.',
    icon: '💻',
  },
  {
    category: 'Terminals',
    name: 'Wetty Terminal',
    port: 3002,
    url: 'http://localhost:3002',
    description: 'SSH-over-HTTP terminal — full shell in a browser tab.',
    icon: '🖥️',
  },

  // ── Data & ML ────────────────────────────────────────────────────────────────
  {
    category: 'Data & ML',
    name: 'JupyterLab',
    port: 8888,
    url: 'http://localhost:8888',
    description: 'Data notebooks with ForgeKeeper kernels baked in.',
    icon: '📓',
  },
  {
    category: 'Data & ML',
    name: 'MLflow UI',
    port: 5000,
    url: 'http://localhost:5000',
    description: 'Track experiments, parameters, and metrics.',
    icon: '📈',
  },
  {
    category: 'Data & ML',
    name: 'TensorBoard',
    port: 6006,
    url: 'http://localhost:6006',
    description: 'Visualize training runs and scalars.',
    icon: '🧠',
  },

  // ── Database UIs ─────────────────────────────────────────────────────────────
  {
    category: 'Database UIs',
    name: 'pgAdmin',
    port: 5050,
    url: 'http://localhost:5050',
    description: 'Full-featured PostgreSQL administration and query tool.',
    icon: '🐘',
  },
  {
    category: 'Database UIs',
    name: 'Adminer',
    port: 8082,
    url: 'http://localhost:8082',
    description: 'Lightweight DB admin for PostgreSQL, MySQL, SQLite, and more.',
    icon: '🗄️',
  },
  {
    category: 'Database UIs',
    name: 'RedisInsight',
    port: 8001,
    url: 'http://localhost:8001',
    description: 'Visual browser and profiler for Redis data structures.',
    icon: '🔴',
  },
  {
    category: 'Database UIs',
    name: 'Mongo Express',
    port: 8081,
    url: 'http://localhost:8081',
    description: 'Web-based MongoDB admin interface.',
    icon: '🍃',
  },

  // ── Observability ────────────────────────────────────────────────────────────
  {
    category: 'Observability',
    name: 'Grafana',
    port: 3001,
    url: 'http://localhost:3001',
    description: 'Dashboards for metrics, logs, and traces from any source.',
    icon: '📊',
  },
  {
    category: 'Observability',
    name: 'Prometheus',
    port: 9090,
    url: 'http://localhost:9090',
    description: 'Metrics scraping and alerting — query with PromQL.',
    icon: '🔥',
  },
  {
    category: 'Observability',
    name: 'Jaeger UI',
    port: 16686,
    url: 'http://localhost:16686',
    description: 'Distributed tracing — visualize request flows across services.',
    icon: '🔭',
  },
  {
    category: 'Observability',
    name: 'Netdata',
    port: 19999,
    url: 'http://localhost:19999',
    description: 'Real-time system performance: CPU, memory, disk, network.',
    icon: '⚡',
  },

  // ── Container & Infra ────────────────────────────────────────────────────────
  {
    category: 'Container & Infra',
    name: 'Portainer',
    port: 9000,
    url: 'http://localhost:9000',
    description: 'Docker container management — start, stop, inspect, and log.',
    icon: '🐳',
  },

  // ── API & Docs ───────────────────────────────────────────────────────────────
  {
    category: 'API & Docs',
    name: 'Swagger UI',
    port: 8083,
    url: 'http://localhost:8083',
    description: 'Interactive OpenAPI documentation and live API testing.',
    icon: '📋',
  },
  {
    category: 'API & Docs',
    name: 'MkDocs',
    port: 8084,
    url: 'http://localhost:8084',
    description: 'Live preview of your project documentation site.',
    icon: '📚',
  },

  // ── AI & LLMs ────────────────────────────────────────────────────────────────
  {
    category: 'AI & LLMs',
    name: 'Open WebUI',
    port: 8085,
    url: 'http://localhost:8085',
    description: 'ChatGPT-style UI for Ollama and any OpenAI-compatible API.',
    icon: '🤖',
  },
  {
    category: 'AI & LLMs',
    name: 'Ollama',
    port: 11434,
    url: 'http://localhost:11434',
    description: 'Local LLM runtime — run Llama 3, Mistral, CodeLlama and more offline.',
    icon: '🦙',
  },
  {
    category: 'AI & LLMs',
    name: 'AnythingLLM',
    port: 3003,
    url: 'http://localhost:3003',
    description: 'RAG-powered chat over your own documents and codebase.',
    icon: '📂',
  },
  {
    category: 'AI & LLMs',
    name: 'Flowise',
    port: 3004,
    url: 'http://localhost:3004',
    description: 'Visual drag-and-drop LLM workflow and agent builder.',
    icon: '🔗',
  },
  {
    category: 'AI & LLMs',
    name: 'LiteLLM Proxy',
    port: 4000,
    url: 'http://localhost:4000',
    description: 'Unified API gateway for OpenAI, Anthropic, Bedrock, Ollama and more.',
    icon: '🔀',
  },

  // ── Portal ───────────────────────────────────────────────────────────────────
  {
    category: 'Portal',
    name: 'ForgeKeeper Portal',
    port: 7000,
    url: 'http://localhost:7000',
    description: 'You are here — bookmark for all hosted tooling.',
    icon: '🔥',
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

  // Group by category
  const grouped = services.reduce((acc, svc) => {
    (acc[svc.category] = acc[svc.category] || []).push(svc);
    return acc;
  }, {});

  for (const [category, items] of Object.entries(grouped)) {
    const section = document.createElement('div');
    section.className = 'service-category';

    const heading = document.createElement('h3');
    heading.className = 'category-heading';
    heading.textContent = category;
    section.appendChild(heading);

    const grid = document.createElement('div');
    grid.className = 'category-grid';

    for (const svc of items) {
      const card = document.createElement('article');
      card.className = 'service-card';
      card.innerHTML = `
        <div class="service-logo-tag">
          <img src="logo/Forge.png" alt="ForgeKeeper emblem" />
        </div>
        <div class="service-icon">${svc.icon}</div>
        <h4>${svc.name}</h4>
        <p class="service-desc">${svc.description}</p>
        <div class="service-meta">
          <span>Port ${svc.port}</span>
          <a href="${svc.url}" target="_blank" rel="noreferrer">Open →</a>
        </div>
      `;
      grid.appendChild(card);
    }

    section.appendChild(grid);
    serviceGrid.appendChild(section);
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
