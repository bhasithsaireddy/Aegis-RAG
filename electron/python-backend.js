const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

const API_PORT = 8000;
const HEALTH_CHECK_INTERVAL = 500;
const MAX_HEALTH_CHECKS = 240; // 120 seconds max wait

let pythonProcess = null;

function resolvePythonExecutable(projectRoot) {
  const isWin = process.platform === 'win32';
  const candidates = [];

  if (process.env.AEGIS_RAG_PYTHON) {
    candidates.push(process.env.AEGIS_RAG_PYTHON);
  }

  if (process.env.VIRTUAL_ENV) {
    candidates.push(
      path.join(process.env.VIRTUAL_ENV, isWin ? 'Scripts\\python.exe' : 'bin/python3'),
      path.join(process.env.VIRTUAL_ENV, 'bin/python')
    );
  }

  for (const dir of ['venv', '.venv']) {
    candidates.push(
      path.join(projectRoot, dir, isWin ? 'Scripts\\python.exe' : 'bin/python3'),
      path.join(projectRoot, dir, 'bin/python')
    );
  }

  for (const candidate of candidates) {
    if (candidate && path.isAbsolute(candidate) && fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return isWin ? 'python' : 'python3';
}

/**
 * Check if the backend is healthy
 */
function checkHealth() {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${API_PORT}/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Wait for backend to be ready
 */
async function waitForBackend() {
  for (let i = 0; i < MAX_HEALTH_CHECKS; i++) {
    if (await checkHealth()) {
      return true;
    }
    await new Promise(r => setTimeout(r, HEALTH_CHECK_INTERVAL));
  }
  return false;
}

/**
 * Start the Python FastAPI backend
 */
async function startPythonBackend() {
  // Check if already running
  if (await checkHealth()) {
    console.log('Backend already running');
    return null;
  }

  const projectRoot = path.join(__dirname, '..');

  // Prefer venv Python if available
  const pythonCmd = resolvePythonExecutable(projectRoot);

  // Start uvicorn
  pythonProcess = spawn(pythonCmd, [
    '-m', 'uvicorn',
    'src.api.main:app',
    '--host', '127.0.0.1',
    '--port', String(API_PORT),
    '--log-level', 'info'
  ], {
    cwd: projectRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1'
    }
  });

  // Log output
  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  pythonProcess.on('error', (error) => {
    console.error('Failed to start Python backend:', error);
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python backend exited with code ${code}`);
    pythonProcess = null;
  });

  // Wait for backend to be ready
  const ready = await waitForBackend();
  if (!ready) {
    throw new Error('Backend failed to start within timeout');
  }

  return pythonProcess;
}

/**
 * Stop the Python backend
 */
function stopPythonBackend(childProcess) {
  if (childProcess) {
    console.log('Stopping Python backend...');

    if (process.platform === 'win32') {
      // On Windows, use taskkill to terminate the process tree
      spawn('taskkill', ['/pid', childProcess.pid, '/f', '/t']);
    } else {
      childProcess.kill('SIGTERM');

      // Force kill after 5 seconds
      setTimeout(() => {
        if (childProcess && !childProcess.killed) {
          childProcess.kill('SIGKILL');
        }
      }, 5000);
    }
  }
}

module.exports = {
  startPythonBackend,
  stopPythonBackend,
  checkHealth
};
