import express, { Request, Response } from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const COMPILER_DIR = path.join(__dirname, 'LoadSheddingCompiler');

app.use(express.json({ limit: '10mb' }));

// API: Compile code
app.post('/api/compile', async (req: Request, res: Response) => {
  const { code } = req.body;
  if (!code || typeof code !== 'string') {
    return res.status(400).json({ error: 'Source code is required.' });
  }

  // Create temporary file
  const tmpFile = path.join('/tmp', `source_${Date.now()}_${Math.random().toString(36).substring(7)}.txt`);
  try {
    await fs.promises.writeFile(tmpFile, code, 'utf-8');

    // Run python3 main.py <tmpFile>
    const pythonScript = path.join(COMPILER_DIR, 'main.py');
    const { stdout, stderr } = await execFileAsync('python3', [pythonScript, tmpFile], {
      cwd: COMPILER_DIR,
      timeout: 10000
    }).catch(err => {
      // Non-zero exit code when compilation stops on errors
      return { stdout: err.stdout || '', stderr: err.stderr || '' };
    });

    const output = stdout.toString();
    const parsedPhases = parseCompilerOutput(output);

    return res.json({
      success: output.includes('Compilation and scheduling succeeded successfully.'),
      rawOutput: output,
      stderr: stderr.toString(),
      phases: parsedPhases
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message || 'Compiler execution error' });
  } finally {
    try {
      if (fs.existsSync(tmpFile)) {
        await fs.promises.unlink(tmpFile);
      }
    } catch (_) {}
  }
});

// API: Get all 9 test cases
app.get('/api/tests', async (_req: Request, res: Response) => {
  try {
    const testsDir = path.join(COMPILER_DIR, 'tests');
    const files = await fs.promises.readdir(testsDir);
    const testList = [];

    for (const f of files.sort()) {
      if (f.endsWith('.txt')) {
        const content = await fs.promises.readFile(path.join(testsDir, f), 'utf-8');
        const lines = content.split('\n');
        const firstLine = lines[0].replace(/^\/\/\s*/, '');
        testList.push({
          id: f.replace('.txt', ''),
          fileName: f,
          expectedSummary: firstLine,
          code: content
        });
      }
    }

    return res.json({ tests: testList });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
});

// API: Download full LoadSheddingCompiler.zip
app.get('/api/download-zip', async (_req: Request, res: Response) => {
  const zipPath = path.join('/tmp', 'LoadSheddingCompiler.zip');
  try {
    // Generate zip using python's built-in zipfile module
    const pythonZipCode = `
import zipfile, os
compiler_dir = '${COMPILER_DIR}'
zip_path = '${zipPath}'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(compiler_dir):
        # Exclude __pycache__ and .git
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.pyc') or file.startswith('.'):
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.join('LoadSheddingCompiler', os.path.relpath(abs_path, compiler_dir))
            z.write(abs_path, rel_path)
print('Zipped successfully')
`;
    await execFileAsync('python3', ['-c', pythonZipCode]);
    res.download(zipPath, 'LoadSheddingCompiler_JUW.zip');
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
});

// Helper to parse sections from CLI stdout
function parseCompilerOutput(output: string) {
  const sections = [
    '=== TOKENS ===',
    '=== AST ===',
    '=== SYMBOL TABLE ===',
    '=== SEMANTIC ===',
    '=== TAC ===',
    '=== OPTIMIZED TAC ===',
    '=== RESULT ==='
  ];

  const result: Record<string, string> = {
    tokens: '',
    ast: '',
    symbolTable: '',
    semantic: '',
    tac: '',
    optimizedTac: '',
    result: ''
  };

  const keys = ['tokens', 'ast', 'symbolTable', 'semantic', 'tac', 'optimizedTac', 'result'];

  for (let i = 0; i < sections.length; i++) {
    const startTag = sections[i];
    const startIndex = output.indexOf(startTag);
    if (startIndex !== -1) {
      const contentStart = startIndex + startTag.length;
      let nextIndex = output.length;
      for (let j = i + 1; j < sections.length; j++) {
        const nextPos = output.indexOf(sections[j], contentStart);
        if (nextPos !== -1 && nextPos < nextIndex) {
          nextIndex = nextPos;
        }
      }
      result[keys[i]] = output.substring(contentStart, nextIndex).trim();
    }
  }

  return result;
}

// Development Vite Middleware setup or static serve
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Load-Shedding Compiler Server running at http://0.0.0.0:${PORT}`);
  });
}

startServer();
