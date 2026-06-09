#!/usr/bin/env python3
import json, subprocess, os, sys, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

C25_HOME = os.path.expanduser("/data/data/com.termux/files/home")
AGENT_PATHS = {
    'pathos': os.path.join(C25_HOME, 'PaTHos', 'pathos_router.py'),
    'earth': os.path.join(C25_HOME, 'planetary_agents', 'earth_agent.py'),
    'mars': os.path.join(C25_HOME, 'sovereign_gtp', 'mars_deploy.py'),
    'jupiter': os.path.join(C25_HOME, 'PlanetaryAgents', 'jupiter_optimize.py'),
    'venus': os.path.join(C25_HOME, 'AiMetaverse', 'venus_ui.py'),
    'mercury': os.path.join(C25_HOME, 'c25_store', 'mercury_comm.py'),
    'sun': os.path.join(C25_HOME, 'c25_store', 'sun_orchestrator.py'),
    'moon': os.path.join(C25_HOME, 'c25_store', 'moon_scheduler.py'),
    'saturn': os.path.join(C25_HOME, 'c25_store', 'saturn_deploy.py'),
    'uranus': os.path.join(C25_HOME, 'c25_store', 'uranus_rnd.py'),
    'neptune': os.path.join(C25_HOME, 'c25_store', 'neptune_finance.py'),
    'pluto': os.path.join(C25_HOME, 'c25_store', 'pluto_risk.py'),
    'ceres': os.path.join(C25_HOME, 'c25_store', 'ceres_data.py'),
    'europa': os.path.join(C25_HOME, 'c25_store', 'europa_research.py'),
    'ganymede': os.path.join(C25_HOME, 'c25_store', 'ganymede_storage.py'),
    'callisto': os.path.join(C25_HOME, 'c25_store', 'callisto_reliability.py'),
    'titan': os.path.join(C25_HOME, 'c25_store', 'titan_expansion.py'),
    'io': os.path.join(C25_HOME, 'c25_store', 'io_infra.py'),
    'haumea': os.path.join(C25_HOME, 'c25_store', 'haumea_design.py'),
    'makemake': os.path.join(C25_HOME, 'c25_store', 'makemake_content.py'),
    'eris': os.path.join(C25_HOME, 'c25_store', 'eris_governance.py'),
    'chronos': os.path.join(C25_HOME, 'c25_store', 'chronos_scheduler.py'),
    'recon': os.path.join(C25_HOME, 'c25_store', 'recon_recon.py'),
    'cicd': os.path.join(C25_HOME, 'c25_store', 'cicd_deploy.py'),
    'alfai': os.path.join(C25_HOME, 'c25_store', 'alfai_legal.py')
}

class C25BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence default logging

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/health':
            active_agents = sum(1 for path in AGENT_PATHS.values() if os.path.exists(path))
            self._send_json({
                'status': 'healthy',
                'timestamp': time.time(),
                'active_agents': active_agents,
                'total_agents': len(AGENT_PATHS),
                'uptime': time.time() - getattr(self.server, 'start_time', time.time())
            })
        
        elif parsed.path == '/api/agents':
            available = [name for name, path in AGENT_PATHS.items() if os.path.exists(path)]
            self._send_json({
                'agents': available,
                'total': len(available),
                'all_known': list(AGENT_PATHS.keys())
            })
        
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode() if content_len > 0 else '{}'
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({'error': 'Invalid JSON'}, 400)
            return
        
        if parsed.path == '/api/chat':
            agent = data.get('agent', 'pathos')
            prompt = data.get('prompt', '')
            
            if agent not in AGENT_PATHS:
                self._send_json({'error': f'Agent not found: {agent}'}, 404)
                return
            
            script_path = AGENT_PATHS[agent]
            if not os.path.exists(script_path):
                self._send_json({'error': f'Agent script not found: {script_path}'}, 404)
                return
            
            try:
                result = subprocess.run(
                    [sys.executable, script_path, '--prompt', prompt, '--agent', agent],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=os.path.dirname(script_path)
                )
                
                response = {
                    'success': result.returncode == 0,
                    'agent': agent,
                    'prompt': prompt,
                    'response': result.stdout.strip(),
                    'error': result.stderr.strip() if result.returncode != 0 else None,
                    'exit_code': result.returncode,
                    'execution_time': round(time.time() - (time.time() - result.returncode/1000), 2)
                }
                
                self._send_json(response)
                
            except subprocess.TimeoutExpired:
                self._send_json({
                    'success': False,
                    'agent': agent,
                    'error': 'Agent timed out after 120 seconds',
                    'response': '⏱️ Agent processing timeout - check script performance'
                }, 500)
            except Exception as e:
                self._send_json({
                    'success': False,
                    'agent': agent,
                    'error': str(e),
                    'response': f'❌ Agent execution error: {str(e)}'
                }, 500)
        
        elif parsed.path == '/api/deploy':
            project = data.get('project', 'test')
            target = data.get('target', 'vercel')
            
            # Try to find deploy script for project
            deploy_script = None
            possible_paths = [
                os.path.join(C25_HOME, project, 'deploy.sh'),
                os.path.join(C25_HOME, project, 'scripts', 'deploy.sh'),
                os.path.join(C25_HOME, project, 'c25_deploy.sh'),
                os.path.join(C25_HOME, 'c25-deploy', f'{project}_deploy.sh')
            ]
            
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    deploy_script = path
                    break
            
            if not deploy_script:
                # Fallback: try to use your Arty deployer
                try:
                    arty_script = os.path.join(C25_HOME, '.c25_artifacts', 'arty.sh')
                    if os.path.exists(arty_script):
                        result = subprocess.run([
                            'bash', arty_script, 'queue',
                            os.path.join(C25_HOME, project, 'dist'),
                            target, '9'
                        ], capture_output=True, text=True, timeout=60)
                        
                        if result.returncode == 0:
                            # Process the queue
                            subprocess.run(['bash', arty_script, 'process'], timeout=120)
                            
                            self._send_json({
                                'success': True,
                                'message': f'Deploy queued via Arty: {project} → {target}',
                                'project': project,
                                'target': target
                            })
                            return
                except:
                    pass
                
                self._send_json({
                    'success': False,
                    'error': f'No deploy script found for {project}',
                    'available_projects': [p for p in os.listdir(C25_HOME) if os.path.isdir(os.path.join(C25_HOME, p)) and os.path.exists(os.path.join(C25_HOME, p, 'deploy.sh'))]
                }, 404)
                return
            
            # Execute deploy script
            try:
                result = subprocess.run(
                    ['bash', deploy_script],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute deploy timeout
                    env={**os.environ, 'DEPLOY_TARGET': target, 'PROJECT_NAME': project}
                )
                
                self._send_json({
                    'success': result.returncode == 0,
                    'project': project,
                    'target': target,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'exit_code': result.returncode
                })
                
            except subprocess.TimeoutExpired:
                self._send_json({
                    'success': False,
                    'error': 'Deploy timed out after 300 seconds',
                    'project': project
                }, 500)
        
        else:
            self._send_json({'error': 'Not found'}, 404)

def run_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), C25BridgeHandler)
    server.start_time = time.time()
    print(f'🚀 C25 Bridge running on http://localhost:{port}')
    print(f'   Health check: GET /health')
    print(f'   Chat: POST /api/chat')
    print(f'   Deploy: POST /api/deploy')
    server.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
