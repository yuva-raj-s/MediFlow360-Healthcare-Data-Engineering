import os
import json

base_dir = r"c:\Users\Yuvaraj s\Desktop\Hobby_Healthcare_Complex"
output_file = os.path.join(base_dir, "MediFlow360_Interactive_Guide.html")

ignore_dirs = ['.git', '.gemini', 'node_modules']
docs_data = {}
total_files = 0

valid_extensions = {
    '.md': '',
    '.py': 'python',
    '.sql': 'sql',
    '.json': 'json',
    '.ps1': 'powershell'
}

for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    rel_path = os.path.relpath(root, base_dir)
    folder_name = "00_Root" if rel_path == '.' else rel_path.replace('\\', '/')
        
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in valid_extensions and file != "MediFlow360_Interactive_Guide.html":
            total_files += 1
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()
            
            # Wrap raw code files in markdown blocks for proper rendering
            if ext != '.md':
                lang = valid_extensions[ext]
                content = f"```{lang}\n{raw_content}\n```"
            else:
                content = raw_content

            if folder_name not in docs_data:
                docs_data[folder_name] = []
                
            docs_data[folder_name].append({
                "title": file,  # Keep extension for accurate representation
                "content": content
            })

sorted_folders = sorted(docs_data.keys())
sorted_docs_data = {k: sorted(docs_data[k], key=lambda x: x['title']) for k in sorted_folders}
import base64
json_data_raw = json.dumps(sorted_docs_data)
json_data_b64 = base64.b64encode(json_data_raw.encode('utf-8')).decode('ascii')



html_template = f"""<!DOCTYPE html>
<html lang="en" class="dark scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediFlow360 | Tech Architecture & Setup Guide</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                        display: ['Outfit', 'sans-serif'],
                        mono: ['Fira Code', 'monospace'],
                    }},
                    colors: {{
                        cyber: {{ 100: '#ccfcff', 200: '#99f8ff', 300: '#66f4ff', 400: '#00f0ff', 500: '#00c3ff', 600: '#0095ff', 700: '#0077cc', 800: '#005599', 900: '#003366' }},
                        neon: {{ 400: '#ff003c', 500: '#d90033' }}
                    }},
                    animation: {{
                        'gradient-x': 'gradient-x 15s ease infinite',
                        'float': 'float 6s ease-in-out infinite',
                        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'scanline': 'scanline 4s linear infinite',
                    }},
                    keyframes: {{
                        'gradient-x': {{
                            '0%, 100%': {{ 'background-size': '200% 200%', 'background-position': 'left center' }},
                            '50%': {{ 'background-size': '200% 200%', 'background-position': 'right center' }},
                        }},
                        'float': {{
                            '0%, 100%': {{ transform: 'translateY(0)' }},
                            '50%': {{ transform: 'translateY(-20px)' }},
                        }},
                        'pulse-glow': {{
                            '0%, 100%': {{ opacity: 1, transform: 'scale(1)' }},
                            '50%': {{ opacity: .6, transform: 'scale(1.05)' }},
                        }},
                        'scanline': {{
                            '0%': {{ transform: 'translateY(-100%)' }},
                            '100%': {{ transform: 'translateY(1000%)' }}
                        }}
                    }}
                }}
            }}
        }}
    </script>
    
    <style>
        body {{ background-color: #050a15; color: #f8fafc; overflow-x: hidden; }}
        
        .glass-panel {{
            background: rgba(10, 15, 30, 0.85);
            backdrop-filter: blur(20px); border: 1px solid rgba(0, 240, 255, 0.15);
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(0, 240, 255, 0.05);
        }}
        
        .glass-card {{
            background: linear-gradient(145deg, rgba(15, 25, 45, 0.9), rgba(5, 10, 20, 0.9));
            border: 1px solid rgba(0, 240, 255, 0.1); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        
        .glass-card:hover {{
            transform: translateY(-8px) scale(1.01); border-color: rgba(0, 240, 255, 0.6);
            box-shadow: 0 20px 40px -15px rgba(0, 240, 255, 0.4), 0 0 20px rgba(0, 240, 255, 0.2); z-index: 50;
        }}

        .bg-grid {{
            background-size: 50px 50px;
            background-image: linear-gradient(to right, rgba(0, 240, 255, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(0, 240, 255, 0.05) 1px, transparent 1px);
            mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
            -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
        }}
        
        .hide-scroll::-webkit-scrollbar {{ display: none; }}
        .hide-scroll {{ -ms-overflow-style: none; scrollbar-width: none; }}
        .custom-scrollbar::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        .custom-scrollbar::-webkit-scrollbar-track {{ background: transparent; }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{ background: rgba(0, 240, 255, 0.2); border-radius: 3px; }}
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {{ background: rgba(0, 240, 255, 0.5); }}

        .tech-node {{
            position: absolute; transform: translate(-50%, -50%);
            background: rgba(10, 20, 35, 0.95); border: 2px solid rgba(0, 240, 255, 0.3);
            border-radius: 12px; padding: 15px; width: 160px; text-align: center;
            cursor: pointer; transition: all 0.3s ease; box-shadow: 0 0 20px rgba(0, 0, 0, 0.8), inset 0 0 15px rgba(0, 240, 255, 0.1); z-index: 20; overflow: hidden;
        }}
        
        .tech-node::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: #00f0ff; box-shadow: 0 0 10px #00f0ff; opacity: 0.5; animation: scanline 3s linear infinite; z-index: -1; }}
        .tech-node:hover {{ border-color: #00f0ff; box-shadow: 0 0 30px rgba(0, 240, 255, 0.5), inset 0 0 20px rgba(0, 240, 255, 0.2); transform: translate(-50%, -50%) scale(1.1); z-index: 30; }}
        .tech-node-title {{ font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 4px; line-height: 1.2; }}
        .tech-node-desc {{ font-family: 'Inter', sans-serif; font-size: 11px; color: #94a3b8; }}

        .radar-pulse {{ position: absolute; transform: translate(-50%, -50%); width: 200px; height: 200px; border-radius: 50%; border: 1px solid rgba(0, 240, 255, 0.8); animation: radar 3s ease-out infinite; z-index: 10; pointer-events: none; }}
        @keyframes radar {{ 0% {{ transform: translate(-50%, -50%) scale(0.5); opacity: 1; }} 100% {{ transform: translate(-50%, -50%) scale(2); opacity: 0; }} }}

        .data-pipe {{ fill: none; stroke: rgba(0, 240, 255, 0.1); stroke-width: 2; stroke-linecap: round; }}
        .data-flow {{ fill: none; stroke: #00f0ff; stroke-width: 2.5; stroke-linecap: round; stroke-dasharray: 8, 30; animation: flow 3s linear infinite; filter: drop-shadow(0 0 5px #00f0ff); }}
        .data-flow-alert {{ fill: none; stroke: #ff003c; stroke-width: 2.5; stroke-linecap: round; stroke-dasharray: 10, 40; animation: flow 2s linear infinite reverse; filter: drop-shadow(0 0 8px #ff003c); }}

        @keyframes flow {{ 0% {{ stroke-dashoffset: 100; }} 100% {{ stroke-dashoffset: 0; }} }}

        .text-gradient {{ background: linear-gradient(to right, #00f0ff, #0095ff, #8b5cf6); -webkit-background-clip: text; background-clip: text; color: transparent; background-size: 200% auto; animation: gradient-x 5s linear infinite; }}


        .timeline-line {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: #00f0ff; transform: translateX(-50%); box-shadow: 0 0 15px #00f0ff, 0 0 30px rgba(0, 240, 255, 0.3); opacity: 0.4; }}
        .timeline-node {{ width: 44px; height: 44px; border-radius: 50%; background: #050a15; border: 2px solid #00f0ff; position: absolute; left: 50%; transform: translateX(-50%); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(0,240,255,0.6); z-index: 10; transition: all 0.3s ease; }}
        .timeline-node:hover {{ transform: translateX(-50%) scale(1.2); box-shadow: 0 0 30px #00f0ff; }}
        .code-snippet {{ font-family: 'Fira Code', monospace; font-size: 12px; background: #0b1120; padding: 12px; border-radius: 8px; border: 1px solid #1e293b; color: #00f0ff; overflow-x: auto; }}
        
        .prose pre {{ background: #0b1120; border: 1px solid rgba(0,240,255,0.2); padding: 1rem; border-radius: 0.5rem; }}
        .prose code {{ color: #00f0ff; font-family: 'Fira Code', monospace; font-weight: 500; }}

        /* Tab panel layout - absolute so they never fight with the nav */
        #view-container {{ position: relative; flex: 1 1 0%; overflow: hidden; }}
        .view-panel {{ position: absolute; inset: 0; overflow-y: auto; display: none; scrollbar-width: thin; scrollbar-color: rgba(0,240,255,0.2) transparent; }}
        #view-docs {{ flex-direction: column; }}
        .view-panel::-webkit-scrollbar {{ width: 6px; }}
        .view-panel::-webkit-scrollbar-track {{ background: transparent; }}
        .view-panel::-webkit-scrollbar-thumb {{ background: rgba(0, 240, 255, 0.2); border-radius: 3px; }}

        /* Office Mode specific: Dossier Feel */
        .dossier-card {{ position: relative; background: rgba(10, 20, 40, 0.6); border: 1px solid rgba(0, 240, 255, 0.1); border-left: 4px solid #00f0ff; overflow: hidden; transition: all 0.3s ease; }}
        .dossier-card:hover {{ border-color: #00f0ff; background: rgba(0, 240, 255, 0.05); transform: translateX(10px); }}
        .dossier-id {{ font-family: 'Fira Code', monospace; font-size: 10px; color: rgba(0, 240, 255, 0.5); text-transform: uppercase; letter-spacing: 2px; }}
        .dossier-scan {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to bottom, transparent, rgba(0, 240, 255, 0.05), transparent); transform: translateY(-100%); pointer-events: none; }}
        .dossier-card:hover .dossier-scan {{ animation: scanline 2s linear infinite; }}

        /* Setup Mode specific: Init Log */
        .init-log {{ background: #020617; border: 1px solid #1e293b; border-radius: 4px; padding: 10px; font-family: 'Fira Code', monospace; font-size: 11px; color: #94a3b8; margin-top: 15px; position: relative; }}
        .init-log::before {{ content: 'LOG OUTPUT'; position: absolute; top: -8px; left: 10px; background: #020617; padding: 0 5px; font-size: 9px; color: #00f0ff; border: 1px solid #1e293b; }}
        .log-line {{ margin-bottom: 2px; border-left: 2px solid transparent; padding-left: 8px; transition: all 0.2s; }}
        .log-line:hover {{ border-left-color: #00f0ff; background: rgba(0, 240, 255, 0.05); color: #f8fafc; }}
        .status-tag {{ font-weight: bold; color: #00f0ff; margin-right: 8px; }}
    </style>
</head>
<body style="display:flex;flex-direction:column;height:100vh;overflow:hidden;background:#050a15;color:#f8fafc;font-family:'Inter',sans-serif;">

    <div class="fixed inset-0 bg-grid" style="z-index:-1;pointer-events:none;"></div>
    <div class="fixed top-[-20%] left-[-10%] w-[800px] h-[800px] bg-cyber-600/10 rounded-full blur-[120px] animate-float" style="z-index:-1;pointer-events:none;"></div>
    <div class="fixed bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[100px] animate-float" style="z-index:-1;pointer-events:none;animation-delay:-3s;"></div>

    <!-- Top Navigation -->
    <nav style="position:relative;z-index:9999;flex-shrink:0;height:64px;" class="glass-panel flex items-center justify-between px-6 lg:px-12 border-b border-cyber-500/20">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-500 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.4)] border border-cyber-400/50">
                <i data-lucide="cpu" class="text-white w-5 h-5"></i>
            </div>
            <div>
                <h1 class="font-display font-bold text-xl text-white tracking-tight leading-none">MediFlow<span class="text-cyber-400">360</span></h1>
                <p class="text-[10px] text-cyber-400 uppercase tracking-widest font-mono mt-0.5">Systems Online</p>
            </div>
        </div>
        
        <div class="flex gap-2 lg:gap-6 h-full">
            <button onclick="switchMode('learning')" id="btn-learning" class="nav-btn h-full flex items-center gap-2 text-xs lg:text-sm font-mono font-semibold transition-all px-2">
                <i data-lucide="monitor" class="w-4 h-4"></i> SYS.DASHBOARD
            </button>
            <button onclick="switchMode('setup')" id="btn-setup" class="nav-btn h-full flex items-center gap-2 text-xs lg:text-sm font-mono font-semibold transition-all px-2">
                <i data-lucide="layers" class="w-4 h-4"></i> SETUP.SEQUENCE
            </button>
            <button onclick="switchMode('office')" id="btn-office" class="nav-btn h-full flex items-center gap-2 text-xs lg:text-sm font-mono font-semibold transition-all px-2">
                <i data-lucide="users" class="w-4 h-4"></i> OFFICE.SQUAD
            </button>
            <button onclick="switchMode('docs')" id="btn-docs" class="nav-btn h-full flex items-center gap-2 text-xs lg:text-sm font-mono font-semibold transition-all px-2">
                <i data-lucide="terminal" class="w-4 h-4"></i> RAW.CODEBASE ({total_files})
            </button>
            <button onclick="switchMode('masterclass')" id="btn-masterclass" class="nav-btn h-full flex items-center gap-2 text-xs lg:text-sm font-mono font-semibold transition-all px-2">
                <i data-lucide="graduation-cap" class="w-4 h-4"></i> PROJECT.MASTERCLASS
            </button>
        </div>
        
        <div class="hidden lg:flex items-center gap-3">
            <span class="px-3 py-1 text-xs font-mono font-bold bg-slate-900 text-green-400 rounded border border-green-500/50 shadow-[0_0_10px_rgba(74,222,128,0.2)] flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div> FREE TIER COMPLIANT
            </span>
        </div>
    </nav>

    <!-- ===== VIEW CONTAINER: all panels live here, absolute positioned ===== -->
    <div id="view-container">

    <!-- ========================================== -->
    <!-- MODE 1: LEARNING JOURNEY (TECHY)           -->
    <!-- ========================================== -->
    <div id="view-learning" class="view-panel active">
        <!-- Hero Section -->
        <section class="min-h-[70vh] flex flex-col items-center justify-center px-6 relative border-b border-cyber-500/10">
            <div class="inline-flex items-center gap-2 px-5 py-2 rounded-full glass-panel border-cyber-500/50 text-cyber-400 text-xs font-mono mb-8 shadow-[0_0_20px_rgba(0,240,255,0.2)]">
                <i data-lucide="activity" class="w-4 h-4"></i> INITIALIZING PIPELINE...
            </div>
            <h2 class="text-5xl md:text-7xl font-display font-extrabold text-white text-center tracking-tight leading-tight max-w-5xl drop-shadow-2xl">
                Master the Art of <br/>
                <span class="text-gradient">Enterprise Data Engineering</span>
            </h2>
            <p class="mt-6 text-lg font-mono text-slate-400 text-center max-w-3xl leading-relaxed">
                > TARGET: Healthcare Domain <br/>
                > PROTOCOL: Medallion Architecture (Bronze/Silver/Gold) <br/>
                > STATUS: 7 Heterogeneous Sources Synchronized.
            </p>
        </section>

        <!-- Techy Interactive Architecture Diagram -->
        <section id="sec-architecture" class="py-20 px-10 max-w-[1500px] mx-auto overflow-visible">
            <div class="text-center mb-16">
                <h3 class="text-4xl font-display font-extrabold text-white mb-4">System Topology</h3>
                <p class="text-cyber-400 font-mono text-sm uppercase tracking-widest animate-pulse">Click core nodes to access source code.</p>
            </div>

            <div class="relative glass-panel rounded-3xl p-10 min-h-[650px] border-cyber-500/30 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                <div class="absolute inset-0 opacity-10" style="background-image: linear-gradient(#00f0ff 1px, transparent 1px), linear-gradient(90deg, #00f0ff 1px, transparent 1px); background-size: 30px 30px;"></div>
                
                <svg width="100%" height="100%" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid meet" class="absolute inset-0 z-0 overflow-visible">
                    <!-- Source to ADF -->
                    <path class="data-pipe" d="M 150 60 C 250 60, 250 300, 400 300" />
                    <path class="data-pipe" d="M 150 138 C 250 138, 250 300, 400 300" />
                    <path class="data-pipe" d="M 150 216 C 250 216, 250 300, 400 300" />
                    <path class="data-pipe" d="M 150 300 L 400 300" />
                    <path class="data-pipe" d="M 150 384 C 250 384, 250 300, 400 300" />
                    <path class="data-pipe" d="M 150 462 C 250 462, 250 300, 400 300" />
                    <path class="data-pipe" d="M 150 540 C 250 540, 250 300, 400 300" />

                    <!-- ADF to Processing -->
                    <path class="data-pipe" d="M 400 300 L 600 150" />
                    <path class="data-pipe" d="M 600 150 L 800 150" />
                    <path class="data-pipe" d="M 800 150 C 700 300, 700 300, 600 300" />
                    <path class="data-pipe" d="M 600 300 L 800 300" />
                    <path class="data-pipe" d="M 800 300 C 700 450, 700 450, 600 450" />
                    <path class="data-pipe" d="M 600 450 L 800 450" />

                    <!-- Serving & Presentation -->
                    <path class="data-pipe" d="M 800 450 C 950 450, 950 228, 1050 228" />
                    <path class="data-pipe" d="M 1050 228 L 1050 90" />
                    <path class="data-pipe" d="M 800 300 C 950 300, 950 372, 1050 372" />

                    <!-- ALERTING PATHS (Centralized Monitoring) -->
                    <path class="data-pipe" stroke="rgba(255,0,60,0.3)" stroke-dasharray="4" d="M 400 300 C 500 550, 900 550, 1050 510" /> <!-- ADF to Logic App -->
                    <path class="data-pipe" stroke="rgba(255,0,60,0.3)" stroke-dasharray="4" d="M 800 150 C 900 150, 1000 500, 1050 510" /> <!-- Bronze to Logic App -->
                    <path class="data-pipe" stroke="rgba(255,0,60,0.3)" stroke-dasharray="4" d="M 800 300 C 900 300, 1000 500, 1050 510" /> <!-- Silver to Logic App -->
                    <path class="data-pipe" stroke="rgba(255,0,60,0.3)" stroke-dasharray="4" d="M 800 450 C 900 450, 1000 500, 1050 510" /> <!-- Gold to Logic App -->

                    <path class="data-flow" d="M 150 60 C 250 60, 250 300, 400 300" />
                    <path class="data-flow" d="M 150 138 C 250 138, 250 300, 400 300" style="animation-delay: -0.3s;" />
                    <path class="data-flow" d="M 150 216 C 250 216, 250 300, 400 300" style="animation-delay: -0.6s;" />
                    <path class="data-flow" d="M 150 300 L 400 300" style="animation-delay: -0.9s;" />
                    <path class="data-flow" d="M 150 384 C 250 384, 250 300, 400 300" style="animation-delay: -1.2s;" />
                    <path class="data-flow" d="M 150 462 C 250 462, 250 300, 400 300" style="animation-delay: -1.5s;" />
                    <path class="data-flow" d="M 150 540 C 250 540, 250 300, 400 300" style="animation-delay: -1.8s;" />

                    <path class="data-flow" d="M 400 300 L 600 150" />
                    <path class="data-flow" d="M 600 150 L 800 150" />
                    <path class="data-flow" d="M 800 150 C 700 300, 700 300, 600 300" />
                    <path class="data-flow" d="M 600 300 L 800 300" />
                    <path class="data-flow" d="M 800 300 C 700 450, 700 450, 600 450" />
                    <path class="data-flow" d="M 600 450 L 800 450" />
                    <path class="data-flow" d="M 800 450 C 950 450, 950 228, 1050 228" />
                    <path class="data-flow" d="M 1050 228 L 1050 90" />
                    <path class="data-flow" d="M 800 300 C 950 300, 950 372, 1050 372" />
                    <path class="data-flow-alert" d="M 400 300 C 500 550, 900 550, 1050 510" /> 
                    <path class="data-flow-alert" d="M 800 150 C 900 150, 1000 500, 1050 510" style="animation-delay: -0.5s;" />
                    <path class="data-flow-alert" d="M 800 300 C 900 300, 1000 500, 1050 510" style="animation-delay: -1s;" />
                </svg>

                <div class="tech-node" style="left: 12.5%; top: 10%; padding: 8px; width: 140px;" onclick="openDoc('03_data_dictionary', 'Source_to_Bronze_Mapping.md')">
                    <i data-lucide="database" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S1: MYSQL</div><div class="tech-node-desc" style="font-size: 9px;">SHIR Connected</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 23%; padding: 8px; width: 140px;" onclick="openDoc('15_incidents_and_struggles', 'INC-007_REST_API_OAuth2_Token_Change.md')">
                    <i data-lucide="globe" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S2: REST API</div><div class="tech-node-desc" style="font-size: 9px;">OAuth2 Paged</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 36%; padding: 8px; width: 140px;" onclick="openDoc('15_incidents_and_struggles', 'INC-008_BOM_in_CSV.md')">
                    <i data-lucide="file-spreadsheet" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S3: SFTP</div><div class="tech-node-desc" style="font-size: 9px;">Blob Event</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 50%; padding: 8px; width: 140px;" onclick="openDoc('03_data_dictionary', 'Source_to_Bronze_Mapping.md')">
                    <i data-lucide="server" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S4: COSMOSDB</div><div class="tech-node-desc" style="font-size: 9px;">JSON Docs</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 64%; padding: 8px; width: 140px;" onclick="openDoc('03_data_dictionary', 'Source_to_Bronze_Mapping.md')">
                    <i data-lucide="database" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S5: POSTGRES</div><div class="tech-node-desc" style="font-size: 9px;">Logical CDC</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 77%; padding: 8px; width: 140px;" onclick="openDoc('03_data_dictionary', 'Source_to_Bronze_Mapping.md')">
                    <i data-lucide="file-text" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S6: SHAREPOINT</div><div class="tech-node-desc" style="font-size: 9px;">Excel Roster</div>
                </div>
                <div class="tech-node" style="left: 12.5%; top: 90%; padding: 8px; width: 140px;" onclick="openDoc('03_data_dictionary', 'Source_to_Bronze_Mapping.md')">
                    <i data-lucide="activity" class="w-4 h-4 text-cyber-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="font-size: 11px;">S7: IOT HUB</div><div class="tech-node-desc" style="font-size: 9px;">Vitals Stream</div>
                </div>

                <div class="radar-pulse" style="left: 33.3%; top: 50%;"></div>
                <div class="tech-node" style="left: 33.3%; top: 50%; border-color: #8b5cf6;" onclick="openDoc('09_adf_pipelines/pipeline_configs', 'PL_Master_Orchestrator.json')">
                    <i data-lucide="git-commit" class="w-8 h-8 text-purple-400 mx-auto mb-2"></i>
                    <div class="tech-node-title" style="color: #a78bfa;">AZURE ADF</div><div class="tech-node-desc">Orchestrator Core</div>
                </div>

                <div class="tech-node" style="left: 50%; top: 25%; border-color: #d97706;" onclick="openDoc('08_sql_scripts/ddl', '01_create_bronze_tables.sql')">
                    <i data-lucide="hard-drive" class="w-5 h-5 text-amber-500 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#fbbf24;">UC: BRONZE</div><div class="tech-node-desc">Raw ABFSS</div>
                </div>
                <div class="tech-node" style="left: 50%; top: 50%; border-color: #94a3b8;" onclick="openDoc('03_data_dictionary', 'SCD_Design_Document.md')">
                    <i data-lucide="hard-drive" class="w-5 h-5 text-slate-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#cbd5e1;">UC: SILVER</div><div class="tech-node-desc">Delta Tables</div>
                </div>
                <div class="tech-node" style="left: 50%; top: 75%; border-color: #fbbf24;" onclick="openDoc('08_sql_scripts/ddl', '03_create_gold_tables.sql')">
                    <i data-lucide="hard-drive" class="w-5 h-5 text-yellow-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#fde047;">UC: GOLD</div><div class="tech-node-desc">Delta Tables</div>
                </div>

                <div class="radar-pulse" style="left: 66.6%; top: 50%; border-color: rgba(255, 0, 60, 0.5);"></div>
                <div class="tech-node" style="left: 66.6%; top: 25%; border-color: #3b82f6;" onclick="openDoc('07_notebooks', '01_Bronze_Ingestion_NB.py')">
                    <i data-lucide="terminal" class="w-5 h-5 text-blue-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#60a5fa;">DBX: BRONZE</div><div class="tech-node-desc">PII Mask & Hash</div>
                </div>
                <div class="tech-node" style="left: 66.6%; top: 50%; border-color: #3b82f6;" onclick="openDoc('07_notebooks', '02b_Silver_SCD2_NB.py')">
                    <i data-lucide="terminal" class="w-5 h-5 text-blue-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#60a5fa;">DBX: SILVER</div><div class="tech-node-desc">SCD Type 1/2 MERGE</div>
                </div>
                <div class="tech-node" style="left: 66.6%; top: 75%; border-color: #3b82f6;" onclick="openDoc('07_notebooks', '03_Gold_Aggregation_NB.py')">
                    <i data-lucide="terminal" class="w-5 h-5 text-blue-400 mx-auto mb-1"></i>
                    <div class="tech-node-title" style="color:#60a5fa;">DBX: GOLD</div><div class="tech-node-desc">Fact Aggregation</div>
                </div>

                <div class="tech-node" style="left: 87.5%; top: 15%; border-color: #eab308;" onclick="openDoc('19_power_bi', 'Dashboard_Specs.md')">
                    <i data-lucide="pie-chart" class="w-6 h-6 text-yellow-400 mx-auto mb-2"></i>
                    <div class="tech-node-title" style="color:#fde047;">POWER BI</div><div class="tech-node-desc">Exec Dashboards</div>
                </div>
                <div class="tech-node" style="left: 87.5%; top: 38%; border-color: #06b6d4;" onclick="openDoc('11_infrastructure', 'Synapse_Deployment.md')">
                    <i data-lucide="network" class="w-6 h-6 text-cyan-400 mx-auto mb-2"></i>
                    <div class="tech-node-title" style="color:#67e8f9;">AZURE SYNAPSE</div><div class="tech-node-desc">Dedicated SQL Pool</div>
                </div>
                <div class="tech-node" style="left: 87.5%; top: 62%; border-color: #8b5cf6;" onclick="openDoc('08_sql_scripts/ddl', '03_create_gold_tables.sql')">
                    <i data-lucide="server" class="w-6 h-6 text-purple-400 mx-auto mb-2"></i>
                    <div class="tech-node-title" style="color:#a78bfa;">AZURE SQL</div><div class="tech-node-desc">Audit & Config</div>
                </div>
                <div class="tech-node" style="left: 87.5%; top: 85%; border-color: #ff003c; box-shadow: 0 0 20px rgba(255,0,60,0.5);" onclick="openDoc('07_notebooks', '05_Data_Quality_NB.py')">
                    <i data-lucide="alert-triangle" class="w-6 h-6 text-red-500 mx-auto mb-2"></i>
                    <div class="tech-node-title" style="color:#fca5a5;">LOGIC APP</div><div class="tech-node-desc">Centralized Alerting</div>
                </div>
            </div>
        </section>

        <!-- Carousel -->
        <section class="py-24 px-6 lg:px-12 border-t border-cyber-500/20 bg-slate-900/50">
            <div class="max-w-[1400px] mx-auto">
                <h3 class="text-3xl font-display font-bold text-white mb-2">Training Modules</h3>
                <p class="text-cyber-400 font-mono text-sm mb-10">> INITIATING DATA ENGINEERING CURRICULUM</p>
                
                <div class="flex overflow-x-auto gap-8 pb-8 hide-scroll snap-x">
                    <div class="glass-card min-w-[340px] max-w-[340px] p-8 rounded-2xl shrink-0 snap-start flex flex-col relative overflow-hidden group">
                        <div class="w-14 h-14 bg-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center mb-6 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.3)]"><i data-lucide="file-code-2" class="w-7 h-7"></i></div>
                        <h4 class="text-xl font-bold text-white mb-3 font-display">1. The Mandate</h4>
                        <p class="text-slate-400 text-sm mb-6 flex-1 font-mono leading-relaxed">Extract from BRD: CIO requires zero-budget architecture. Analyze Free Tier constraints and data mapping.</p>
                        <button onclick="openDoc('01_business_requirements', 'BRD_MediFlow360_v2.0.md')" class="w-full py-3 bg-slate-800 text-white rounded-lg text-sm font-mono font-bold transition-all border border-slate-700 hover:border-blue-500 hover:text-blue-400">EXECUTE -> BRD.md</button>
                    </div>

                    <div class="glass-card min-w-[340px] max-w-[340px] p-8 rounded-2xl shrink-0 snap-start flex flex-col relative overflow-hidden group">
                        <div class="w-14 h-14 bg-emerald-500/20 text-emerald-400 rounded-xl flex items-center justify-center mb-6 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.3)]"><i data-lucide="shield-check" class="w-7 h-7"></i></div>
                        <h4 class="text-xl font-bold text-white mb-3 font-display">2. Governance</h4>
                        <p class="text-slate-400 text-sm mb-6 flex-1 font-mono leading-relaxed">Enforce DPDP Act compliance. Review Python SHA-256 hashing and PII regex masking algorithms.</p>
                        <button onclick="openDoc('05_data_governance', 'DPDP_Compliance_Checklist.md')" class="w-full py-3 bg-slate-800 text-white rounded-lg text-sm font-mono font-bold transition-all border border-slate-700 hover:border-emerald-500 hover:text-emerald-400">EXECUTE -> DPDP.md</button>
                    </div>

                    <div class="glass-card min-w-[340px] max-w-[340px] p-8 rounded-2xl shrink-0 snap-start flex flex-col relative overflow-hidden group border-red-500/30 shadow-[0_0_20px_rgba(255,0,60,0.1)]">
                        <div class="w-14 h-14 bg-red-500/20 text-red-500 rounded-xl flex items-center justify-center mb-6 border border-red-500/50 animate-pulse"><i data-lucide="flame" class="w-7 h-7"></i></div>
                        <h4 class="text-xl font-bold text-red-400 mb-3 font-display">3. The War Room</h4>
                        <p class="text-slate-400 text-sm mb-6 flex-1 font-mono leading-relaxed">! CRITICAL FAILURES. Review Incident Reports for broken SCD loops, silent API changes, and missing BOMs.</p>
                        <button onclick="openDoc('15_incidents_and_struggles', 'INC-005_SCD2_Broke_Incremental.md')" class="w-full py-3 bg-red-900/40 text-red-300 rounded-lg text-sm font-mono font-bold transition-all border border-red-500/50 hover:bg-red-500/40 hover:text-white">DEBUG -> INC-005.md</button>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- ========================================== -->
    <!-- MODE 2: SETUP SEQUENCE (TUTORIAL)          -->
    <!-- ========================================== -->
    <div id="view-setup" class="view-panel">
        <div class="py-16 px-10 lg:px-20 max-w-[1400px] mx-auto">
            <div class="text-center mb-24">
                <h2 class="text-4xl font-display font-extrabold text-white mb-4">Deployment Sequence</h2>
                <p class="text-cyber-400 font-mono text-sm">> FOLLOW PROTOCOL TO REPLICATE MEDIFLOW360 ENVIRONMENT.</p>
            </div>

            <!-- Vertical Timeline Line -->
            <div class="timeline-line"></div>

            <!-- Timeline Items -->
            <div class="space-y-24 relative">
                
                <!-- STEP 1 -->
                <div class="relative w-full flex justify-end">
                    <div class="timeline-node top-0"><i data-lucide="shield" class="w-5 h-5 text-cyber-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left">
                        <div class="absolute top-6 -left-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-r-[20px] border-r-[rgba(0,240,255,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-cyber-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 01 // FOUNDATION</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B01]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Foundation & Networking</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Establish the secure backbone. Provision the Resource Group, Virtual Network (VNet), and Subnets.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[EXEC]</span> az group create --name mrhs-rg-mediflow360</div>
                            <div class="log-line"><span class="status-tag">[WAIT]</span> provisioning private_endpoints...</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> connectivity established.</div>
                        </div>

                        <button onclick="openDoc('11_infrastructure', 'VNet_Architecture.md')" class="mt-6 text-xs font-mono text-cyber-400 hover:text-white border-b border-cyber-400 flex items-center gap-2 w-fit"><i data-lucide="external-link" class="w-3 h-3"></i> ACCESS NETWORK TOPOLOGY</button>
                    </div>
                </div>

                <!-- STEP 2 -->
                <div class="relative w-full flex justify-start">
                    <div class="timeline-node top-0"><i data-lucide="layers" class="w-5 h-5 text-purple-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(168,85,247,0.3);">
                        <div class="absolute top-6 -right-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-l-[20px] border-l-[rgba(168,85,247,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-purple-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 02 // GOVERNANCE</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B02]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Governance & Storage</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Initialize ADLS Gen2 with Hierarchical Namespace and bind to Unity Catalog.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[EXEC]</span> ./create_dirs.ps1 --target-adls</div>
                            <div class="log-line"><span class="status-tag">[SYNC]</span> unity_catalog_metastore::assign(workspace_id)</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> schemas created: bronze, silver, gold.</div>
                        </div>

                        <button onclick="openDoc('00_Root', 'create_dirs.ps1')" class="mt-6 text-xs font-mono text-purple-400 hover:text-white border-b border-purple-400 flex items-center gap-2 w-fit"><i data-lucide="terminal" class="w-3 h-3"></i> EXECUTE STORAGE SCRIPT</button>
                    </div>
                </div>

                <!-- STEP 3 -->
                <div class="relative w-full flex justify-end">
                    <div class="timeline-node top-0"><i data-lucide="key" class="w-5 h-5 text-blue-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(59,130,246,0.3);">
                        <div class="absolute top-6 -left-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-r-[20px] border-r-[rgba(59,130,246,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-blue-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 03 // SECURITY</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B03]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Security & Connectivity</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Vault initialization and SHIR (Self-Hosted Integration Runtime) deployment.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[AUTH]</span> keyvault_scope::create(mediflow-secrets)</div>
                            <div class="log-line"><span class="status-tag">[NODE]</span> shir-chennai-node-01 :: STATUS=ONLINE</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> hybrid data link secured.</div>
                        </div>

                        <button onclick="openDoc('02_solution_design', 'Security_Architecture.md')" class="mt-6 text-xs font-mono text-blue-400 hover:text-white border-b border-blue-400 flex items-center gap-2 w-fit"><i data-lucide="shield-check" class="w-3 h-3"></i> VIEW SECURITY SPECS</button>
                    </div>
                </div>

                <!-- STEP 4 -->
                <div class="relative w-full flex justify-start">
                    <div class="timeline-node top-0"><i data-lucide="database" class="w-5 h-5 text-emerald-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(16,185,129,0.3);">
                        <div class="absolute top-6 -right-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-l-[20px] border-l-[rgba(16,185,129,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-emerald-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 04 // TELEMETRY</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B04]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Operational Metadata</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Seed the Watermark and Audit tables in Azure SQL DB.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[SQL]</span> EXEC ddl.initialize_watermarks;</div>
                            <div class="log-line"><span class="status-tag">[SEED]</span> INSERT INTO config.source_registry (7 rows)</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> telemetry engine ready.</div>
                        </div>

                        <button onclick="openDoc('08_sql_scripts/ddl', '05_create_watermark_table.sql')" class="mt-6 text-xs font-mono text-emerald-400 hover:text-white border-b border-emerald-400 flex items-center gap-2 w-fit"><i data-lucide="database" class="w-3 h-3"></i> INITIALIZE DDL</button>
                    </div>
                </div>

                <!-- STEP 5 -->
                <div class="relative w-full flex justify-end">
                    <div class="timeline-node top-0"><i data-lucide="git-branch" class="w-5 h-5 text-cyan-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(6,182,212,0.3);">
                        <div class="absolute top-6 -left-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-r-[20px] border-r-[rgba(6,182,212,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-cyan-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 05 // INGESTION</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B05]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Ingestion Orchestration</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">ADF pipeline deployment with dynamic metadata mapping.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[JSON]</span> pipeline.deploy(MasterOrchestrator)</div>
                            <div class="log-line"><span class="status-tag">[LOOP]</span> ForEach(source in source_list)</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> active ingestion loops initialized.</div>
                        </div>

                        <button onclick="openDoc('09_adf_pipelines/pipeline_configs', 'PL_Master_Orchestrator.json')" class="mt-6 text-xs font-mono text-cyan-400 hover:text-white border-b border-cyan-400 flex items-center gap-2 w-fit"><i data-lucide="git-merge" class="w-3 h-3"></i> REVIEW PIPELINES</button>
                    </div>
                </div>

                <!-- STEP 6 -->
                <div class="relative w-full flex justify-start">
                    <div class="timeline-node top-0"><i data-lucide="code-2" class="w-5 h-5 text-orange-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(251,146,60,0.3);">
                        <div class="absolute top-6 -right-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-l-[20px] border-l-[rgba(251,146,60,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-orange-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 06 // PROCESSING</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B06]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Medallion Processing</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">PySpark logic for SCD Type 2 and data quality gating.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[PY]</span> databricks.notebook.run(02b_Silver_SCD2)</div>
                            <div class="log-line"><span class="status-tag">[UC]</span> MERGE INTO silver.patients USING updates...</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> high-fidelity historical state active.</div>
                        </div>

                        <button onclick="openDoc('07_notebooks', '02b_Silver_SCD2_NB.py')" class="mt-6 text-xs font-mono text-orange-400 hover:text-white border-b border-orange-400 flex items-center gap-2 w-fit"><i data-lucide="code" class="w-3 h-3"></i> DEPLOY NOTEBOOKS</button>
                    </div>
                </div>

                <!-- STEP 7 -->
                <div class="relative w-full flex justify-end">
                    <div class="timeline-node top-0"><i data-lucide="zap" class="w-5 h-5 text-pink-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(236,72,153,0.3);">
                        <div class="absolute top-6 -left-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-r-[20px] border-r-[rgba(236,72,153,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-pink-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 07 // SERVING</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B07]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Enterprise Serving</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Synapse Dedicated Pool initialization and PolyBase loading.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[DW]</span> provisioning dw100c_pool...</div>
                            <div class="log-line"><span class="status-tag">[COPY]</span> FROM adls.gold TO dedicated_pool;</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> analytics layer synchronized.</div>
                        </div>

                        <button onclick="openDoc('11_infrastructure', 'Synapse_Deployment.md')" class="mt-6 text-xs font-mono text-pink-400 hover:text-white border-b border-pink-400 flex items-center gap-2 w-fit"><i data-lucide="database" class="w-3 h-3"></i> SYNAPSE DEPLOY GUIDE</button>
                    </div>
                </div>

                <!-- STEP 8 -->
                <div class="relative w-full flex justify-start">
                    <div class="timeline-node top-0"><i data-lucide="bell" class="w-5 h-5 text-red-400"></i></div>
                    <div class="w-[45%] glass-card p-8 rounded-2xl relative text-left" style="border-color: rgba(248,113,113,0.3);">
                        <div class="absolute top-6 -right-[20px] w-0 h-0 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent border-l-[20px] border-l-[rgba(248,113,113,0.2)]"></div>
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-red-400 font-mono text-sm font-bold uppercase tracking-widest">PHASE 08 // OBSERVABILITY</div>
                            <span class="text-[10px] font-mono text-slate-500">[0x7F4B08]</span>
                        </div>
                        <h4 class="text-2xl font-display font-bold text-white mb-4">Observability & Alerts</h4>
                        <p class="text-slate-400 text-sm mb-4 leading-relaxed">Logic App router configuration and Teams integration.</p>
                        
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[PUSH]</span> webhook::trigger(failure_alert)</div>
                            <div class="log-line"><span class="status-tag">[TEAMS]</span> post_message(pipeline_failed_prod)</div>
                            <div class="log-line"><span class="status-tag">[DONE]</span> monitoring system ONLINE.</div>
                        </div>

                        <button onclick="openDoc('07_notebooks', '00_Helper_NB.py')" class="mt-6 text-xs font-mono text-red-400 hover:text-white border-b border-red-400 flex items-center gap-2 w-fit"><i data-lucide="bell-ring" class="w-3 h-3"></i> ALERT DISPATCHER</button>
                    </div>
                </div>

            </div>
            
            <div class="text-center mt-24 pb-20">
                <div class="inline-block p-4 rounded-full border-2 border-cyber-400 bg-[#050a15] shadow-[0_0_30px_rgba(0,240,255,0.5)]">
                    <i data-lucide="check" class="w-8 h-8 text-cyber-400"></i>
                </div>
                <h3 class="text-2xl font-display font-bold text-white mt-4">DEPLOYMENT COMPLETE</h3>
            </div>
            
        </div>
    </div>

    <!-- ========================================== -->
    <!-- MODE 3: OFFICE SQUAD                       -->
    <!-- ========================================== -->
    <div id="view-office" class="view-panel">
        <section class="py-16 px-6 lg:px-12">
            <div class="max-w-[1400px] mx-auto">
                <div class="text-center mb-14">
                    <div class="inline-flex items-center gap-2 px-5 py-2 rounded-full glass-panel border-purple-500/50 text-purple-400 text-xs font-mono mb-6">
                        <i data-lucide="users" class="w-4 h-4"></i> OFFICE.SQUAD — INTERNAL DIRECTORY
                    </div>
                    <h2 class="text-5xl font-display font-extrabold text-white tracking-tight mb-4">Meet the <span style="background:linear-gradient(to right,#a855f7,#ec4899);-webkit-background-clip:text;background-clip:text;color:transparent;">Team</span></h2>
                    <p class="text-slate-400 font-mono text-sm">The real people behind MediFlow360 — roles, struggles, and office dynamics.</p>
                </div>

                <!-- Team Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">

                    <div class="dossier-card p-6 rounded-r-2xl cursor-pointer" onclick="openDoc('00_project_charter','RACI_Matrix.md')">
                        <div class="dossier-scan"></div>
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white border-2 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.5)]" style="background:linear-gradient(135deg,#7c3aed,#4f46e5);">PS</div>
                            <div>
                                <div class="dossier-id">OPERATIVE: DE-001 // LEAD</div>
                                <div class="text-white font-bold font-display text-lg">Priya Sharma</div>
                                <div class="text-slate-500 text-[10px] font-mono mt-0.5">LOCATION: CHENNAI_DC</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-4 border-l border-purple-500/30 pl-3">Architecture lead. Discovered the INC-005 SCD watermark loop. Protocol enforced: No hardcoded credentials.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-[10px] font-mono border border-purple-500/20">PYSPARK_ENGINE</span>
                            <span class="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-[10px] font-mono border border-purple-500/20">MEDALLION_CTRL</span>
                        </div>
                    </div>

                    <div class="dossier-card p-6 rounded-r-2xl cursor-pointer" style="border-left-color: #3b82f6;" onclick="openDoc('09_adf_pipelines/pipeline_configs','PL_Master_Orchestrator.json')">
                        <div class="dossier-scan"></div>
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white border-2 border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]" style="background:linear-gradient(135deg,#2563eb,#0284c7);">AP</div>
                            <div>
                                <div class="dossier-id">OPERATIVE: DE-002 // ADF</div>
                                <div class="text-white font-bold font-display text-lg">Arjun Patel</div>
                                <div class="text-slate-500 text-[10px] font-mono mt-0.5">LOCATION: ON_PREM_SHIR</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-4 border-l border-blue-500/30 pl-3">ADF orchestrator. Resolved the 1-based API pagination bug. Currently managing the OAuth2 Token refresh logic.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded text-[10px] font-mono border border-blue-500/20">ORCHESTRATOR_JSON</span>
                            <span class="px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded text-[10px] font-mono border border-blue-500/20">SHIR_CONNECT</span>
                        </div>
                    </div>

                    <div class="dossier-card p-6 rounded-r-2xl cursor-pointer" style="border-left-color: #06b6d4;" onclick="openDoc('07_notebooks','02b_Silver_SCD2_NB.py')">
                        <div class="dossier-scan"></div>
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white border-2 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.5)]" style="background:linear-gradient(135deg,#0891b2,#0e7490);">KR</div>
                            <div>
                                <div class="dossier-id">OPERATIVE: DE-003 // DBX</div>
                                <div class="text-white font-bold font-display text-lg">Kavitha Rajan</div>
                                <div class="text-slate-500 text-[10px] font-mono mt-0.5">LOCATION: COIMBATORE_REMOTE</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-4 border-l border-cyan-500/30 pl-3">Notebook engineer. Identified the BOM character bug in legacy CSVs. Lead for SCD-2 Delta Lake implementation.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded text-[10px] font-mono border border-cyan-500/20">DELTA_LAKE_CORE</span>
                            <span class="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded text-[10px] font-mono border border-cyan-500/20">SCD_2_LOGIC</span>
                        </div>
                    </div>

                    <div class="glass-card p-6 rounded-2xl border border-green-500/20 hover:border-green-400/60 transition-all hover:-translate-y-2 cursor-pointer" onclick="openDoc('12_testing','Unit_Test_Cases.md')">
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background:linear-gradient(135deg,#16a34a,#15803d);">MF</div>
                            <div>
                                <div class="text-white font-bold font-display">Mohammed Farhan</div>
                                <div class="text-green-400 text-xs font-mono">DE-004 · Junior DE – SQL & QA</div>
                                <div class="text-slate-500 text-xs mt-0.5">Chennai Office</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-3">Writes the SQL scripts and test cases. Accidentally caused INC-003 (Aadhaar in Gold layer) as a learning moment. Now owns DQ checks.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-green-500/20 text-green-300 rounded text-xs font-mono">SQL</span>
                            <span class="px-2 py-0.5 bg-green-500/20 text-green-300 rounded text-xs font-mono">pytest</span>
                            <span class="px-2 py-0.5 bg-green-500/20 text-green-300 rounded text-xs font-mono">QA</span>
                        </div>
                    </div>

                    <div class="glass-card p-6 rounded-2xl border border-yellow-500/20 hover:border-yellow-400/60 transition-all hover:-translate-y-2 cursor-pointer" onclick="openDoc('19_power_bi','DAX_Measures_Library.md')">
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background:linear-gradient(135deg,#d97706,#b45309);">RN</div>
                            <div>
                                <div class="text-white font-bold font-display">Rahul Nair</div>
                                <div class="text-yellow-400 text-xs font-mono">DA-001 · Senior Data Analyst</div>
                                <div class="text-slate-500 text-xs mt-0.5">Madurai (WFH)</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-3">Power BI maestro. Proved billing team's Excel had 800 duplicates (LOG-003). Built the RLS hospital filter that made CMO smile.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs font-mono">Power BI</span>
                            <span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs font-mono">DAX</span>
                            <span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs font-mono">RLS</span>
                        </div>
                    </div>

                    <div class="glass-card p-6 rounded-2xl border border-pink-500/20 hover:border-pink-400/60 transition-all hover:-translate-y-2 cursor-pointer" onclick="openDoc('00_project_charter','Stakeholder_Register.md')">
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background:linear-gradient(135deg,#db2777,#9d174d);">SI</div>
                            <div>
                                <div class="text-white font-bold font-display">Sneha Iyer</div>
                                <div class="text-pink-400 text-xs font-mono">PM-001 · Project Manager</div>
                                <div class="text-slate-500 text-xs mt-0.5">Chennai Office</div>
                            </div>
                        </div>
                        <p class="text-slate-400 text-xs leading-relaxed font-mono mb-3">Keeps CIO happy and DEs unblocked. Translates "the dashboard is wrong" into actionable Jira tickets. Negotiated CR-001 mid-sprint.</p>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded text-xs font-mono">Stakeholders</span>
                            <span class="px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded text-xs font-mono">Jira</span>
                            <span class="px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded text-xs font-mono">BRD</span>
                        </div>
                    </div>

                </div>

                <!-- Stakeholder Section -->
                <h3 class="text-2xl font-display font-bold text-white mb-2">Stakeholder Roster</h3>
                <p class="text-purple-400 font-mono text-sm mb-8">> THE PEOPLE WE REPORT TO — HANDLE WITH CARE.</p>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
                    <div class="glass-card p-5 rounded-xl border border-slate-700 hover:border-red-400/50 transition-all cursor-pointer" onclick="openDoc('00_project_charter','Stakeholder_Register.md')">
                        <div class="text-red-400 font-mono text-xs font-bold mb-1">STK-004 · PROJECT SPONSOR</div>
                        <div class="text-white font-bold">Ms. Divya Anand</div>
                        <div class="text-slate-400 text-xs">CIO, MRHS</div>
                        <div class="mt-3 text-xs text-slate-500 font-mono">"Make it free tier or else." Weekly check-ins. Approves all Azure spend &gt; $0.</div>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-slate-700 hover:border-yellow-400/50 transition-all cursor-pointer" onclick="openDoc('16_change_requests','CR-001_Add_Fraud_Detection.md')">
                        <div class="text-yellow-400 font-mono text-xs font-bold mb-1">STK-003 · FINANCE</div>
                        <div class="text-white font-bold">Mr. Balaji Venkatesh</div>
                        <div class="text-slate-400 text-xs">CFO, MRHS</div>
                        <div class="mt-3 text-xs text-slate-500 font-mono">Added fraud detection mid-sprint (CR-001). Claims denial rate must be &lt;8%. Very precise about numbers.</div>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-slate-700 hover:border-green-400/50 transition-all cursor-pointer" onclick="openDoc('16_change_requests','CR-002_KPI_Redefinition.md')">
                        <div class="text-green-400 font-mono text-xs font-bold mb-1">STK-002 · CLINICAL</div>
                        <div class="text-white font-bold">Dr. Meena Krishnaswamy</div>
                        <div class="text-slate-400 text-xs">CMO, MRHS</div>
                        <div class="mt-3 text-xs text-slate-500 font-mono">Changed readmission threshold from 7% to 5% (CR-002). Needs drill-down by physician. iPad user.</div>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-slate-700 hover:border-blue-400/50 transition-all cursor-pointer" onclick="openDoc('11_infrastructure','Azure_Cost_Optimization.md')">
                        <div class="text-blue-400 font-mono text-xs font-bold mb-1">STK-009 · IT INFRA</div>
                        <div class="text-white font-bold">Mr. Anand Subramaniam</div>
                        <div class="text-slate-400 text-xs">IT Head, MRHS</div>
                        <div class="mt-3 text-xs text-slate-500 font-mono">Caused INC-002 (firewall blocked port 443). Now whitelists ADF IPs after every patch cycle.</div>
                    </div>
                </div>

                <!-- Office Dynamics / Struggles -->
                <h3 class="text-2xl font-display font-bold text-white mb-2">Real Office Struggles</h3>
                <p class="text-red-400 font-mono text-sm mb-8">> WHAT THEY DON'T TEACH IN TUTORIALS.</p>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-16">
                    <div class="glass-card p-5 rounded-xl border border-red-500/30 hover:border-red-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','INC-005_SCD2_Broke_Incremental.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="alert-triangle" class="w-5 h-5 text-red-400"></i><span class="text-red-400 font-mono text-xs font-bold">INC-005 · P1 WAR ROOM</span></div>
                        <div class="text-white font-bold mb-1">SCD-2 Infinite Loop</div>
                        <p class="text-slate-400 text-xs font-mono">Silver watermark was updating on every SCD run, causing the next run to pick up all SCD-modified rows as "new". 54,000 fake patients appeared.</p>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-orange-500/30 hover:border-orange-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','INC-007_REST_API_OAuth2_Token_Change.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="lock" class="w-5 h-5 text-orange-400"></i><span class="text-orange-400 font-mono text-xs font-bold">INC-007 · SILENT AUTH FAIL</span></div>
                        <div class="text-white font-bold mb-1">OAuth2 Token URL Changed</div>
                        <p class="text-slate-400 text-xs font-mono">Insurance API vendor migrated token endpoint with zero notice. Pipeline failed silently for 14 hours returning empty datasets.</p>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-yellow-500/30 hover:border-yellow-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','LOG-004_HR_Excel_Merged_Cells.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="table" class="w-5 h-5 text-yellow-400"></i><span class="text-yellow-400 font-mono text-xs font-bold">LOG-004 · ONGOING</span></div>
                        <div class="text-white font-bold mb-1">HR Refuses to Fix Excel</div>
                        <p class="text-slate-400 text-xs font-mono">HR's Excel roster has merged header cells. PySpark can't parse it. HR said "the format is approved by management." Still unresolved.</p>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-purple-500/30 hover:border-purple-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','LOG-002_Azure_Cost_Overrun.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="dollar-sign" class="w-5 h-5 text-purple-400"></i><span class="text-purple-400 font-mono text-xs font-bold">LOG-002 · COST OVERRUN</span></div>
                        <div class="text-white font-bold mb-1">$47 Weekend Burn</div>
                        <p class="text-slate-400 text-xs font-mono">Someone forgot to terminate the Databricks cluster on a Friday. $47 burned over the weekend. Auto-terminate policy created same day.</p>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-cyan-500/30 hover:border-cyan-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','INC-001_Madurai_Date_Format.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="calendar" class="w-5 h-5 text-cyan-400"></i><span class="text-cyan-400 font-mono text-xs font-bold">INC-001 · DATA FORMAT</span></div>
                        <div class="text-white font-bold mb-1">Madurai Sends MM-DD-YYYY</div>
                        <p class="text-slate-400 text-xs font-mono">Every other hospital uses DD-MM-YYYY. Madurai HIS doesn't. Lost 3 days debugging NULL dates before the normalize function was built.</p>
                    </div>
                    <div class="glass-card p-5 rounded-xl border border-green-500/30 hover:border-green-400 transition-all cursor-pointer" onclick="openDoc('15_incidents_and_struggles','LOG-003_Patient_Count_Discrepancy.md')">
                        <div class="flex items-center gap-2 mb-3"><i data-lucide="users" class="w-5 h-5 text-green-400"></i><span class="text-green-400 font-mono text-xs font-bold">LOG-003 · STAKEHOLDER PANIC</span></div>
                        <div class="text-white font-bold mb-1">"Dashboard Count is Wrong!"</div>
                        <p class="text-slate-400 text-xs font-mono">Billing's Excel showed 19,200 patients. Our dashboard showed 18,400. Turns out UPMI correctly deduped 800 cross-hospital duplicates. We were right.</p>
                    </div>
                </div>

                <!-- Meeting Notes & Sprint History -->
                <h3 class="text-2xl font-display font-bold text-white mb-2">Office Timeline</h3>
                <p class="text-slate-400 font-mono text-sm mb-8">> SPRINT HISTORY, STANDUPS AND WAR ROOMS.</p>
                <div class="flex gap-4 overflow-x-auto pb-6 hide-scroll">
                    <div class="glass-card min-w-[260px] p-5 rounded-xl border border-slate-700 hover:border-cyber-400/50 transition-all cursor-pointer shrink-0" onclick="openDoc('17_meeting_notes','2024_01_15_Sprint1_Planning.md')">
                        <div class="text-cyber-400 font-mono text-xs mb-1">JAN 15, 2024</div>
                        <div class="text-white font-bold mb-2">Sprint 1 Kickoff</div>
                        <p class="text-slate-400 text-xs font-mono">Arjun flags Claims API uses OAuth2. Priya sets "Aadhaar hash only" rule. Suresh promises SHIR by Tuesday.</p>
                    </div>
                    <div class="glass-card min-w-[260px] p-5 rounded-xl border border-slate-700 hover:border-cyber-400/50 transition-all cursor-pointer shrink-0" onclick="openDoc('17_meeting_notes','2024_02_12_Sprint2_Retro.md')">
                        <div class="text-cyber-400 font-mono text-xs mb-1">FEB 12, 2024</div>
                        <div class="text-white font-bold mb-2">Sprint 2 Retro</div>
                        <p class="text-slate-400 text-xs font-mono">Hit INC-001 date bug. Decision: handle data quality defensively. Hospitals don't coordinate schema changes.</p>
                    </div>
                    <div class="glass-card min-w-[260px] p-5 rounded-xl border border-red-500/30 hover:border-red-400 transition-all cursor-pointer shrink-0" onclick="openDoc('17_meeting_notes','2024_03_14_War_Room_INC005.md')">
                        <div class="text-red-400 font-mono text-xs mb-1">MAR 14, 2024 — WAR ROOM</div>
                        <div class="text-white font-bold mb-2">The SCD Loop Crisis</div>
                        <p class="text-slate-400 text-xs font-mono">"Why does the dashboard show 54,000 patients?" The watermark loop was discovered live on a call with Sneha.</p>
                    </div>
                    <div class="glass-card min-w-[260px] p-5 rounded-xl border border-green-500/30 hover:border-green-400 transition-all cursor-pointer shrink-0" onclick="openDoc('17_meeting_notes','2024_03_05_CMO_Demo.md')">
                        <div class="text-green-400 font-mono text-xs mb-1">MAR 5, 2024</div>
                        <div class="text-white font-bold mb-2">CMO Dashboard Demo</div>
                        <p class="text-slate-400 text-xs font-mono">Dr. Meena approved the readmission chart but changed the threshold to 5%. "Can we drill by physician?" → CR-002 born.</p>
                    </div>
                    <div class="glass-card min-w-[260px] p-5 rounded-xl border border-slate-700 hover:border-cyber-400/50 transition-all cursor-pointer shrink-0" onclick="openDoc('18_sprint_artifacts','Definition_of_Done.md')">
                        <div class="text-cyber-400 font-mono text-xs mb-1">ONGOING</div>
                        <div class="text-white font-bold mb-2">Definition of Done</div>
                        <p class="text-slate-400 text-xs font-mono">A story is Done only when: code merged, tests pass, Gold data validated, and governance signs off on PII.</p>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- ========================================== -->
    <!-- MODE 4: PROJECT MASTERCLASS (Step-by-Step) -->
    <!-- ========================================== -->
    <div id="view-masterclass" class="view-panel">
        <div class="max-w-6xl mx-auto py-12 px-6">
            <header class="mb-12 border-b border-cyber-500/30 pb-8">
                <h2 class="text-4xl font-display font-bold text-white mb-2 tracking-tight">MediFlow<span class="text-cyber-400">360</span> Masterclass</h2>
                <p class="text-cyber-400 font-mono text-sm uppercase tracking-widest">> THE COMPLETE GUIDE TO BUILDING AN ENTERPRISE HEALTHCARE DATA PLATFORM.</p>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <!-- Navigation / Progress -->
                <div class="lg:col-span-3 space-y-4">
                    <div class="sticky top-8">
                        <h4 class="text-xs font-mono text-slate-500 uppercase mb-4 tracking-tighter">Course Modules</h4>
                        <div class="space-y-1">
                            <a href="#m1" class="block p-3 rounded bg-cyber-500/10 border-l-2 border-cyber-400 text-white text-xs font-mono">01. BLUEPRINT & GOVERNANCE</a>
                            <a href="#m2" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">02. RESOURCE CREATION (IaC)</a>
                            <a href="#m3" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">03. INGESTION (ADF & BRONZE)</a>
                            <a href="#m4" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">04. PROCESSING (SILVER & SCD)</a>
                            <a href="#m5" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">05. SERVING (SYNAPSE & GOLD)</a>
                            <a href="#m6" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">06. ANALYTICS (POWER BI)</a>
                            <a href="#m7" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">07. MONITORING & ALERTING</a>
                            <a href="#m8" class="block p-3 rounded hover:bg-slate-800 text-slate-400 text-xs font-mono transition-colors">08. CI/CD & DEVOPS</a>
                        </div>
                    </div>
                </div>

                <!-- Main Guide Content -->
                <div class="lg:col-span-9 space-y-16 pb-32">
                    
                    <!-- Module 1 -->
                    <section id="m1" class="space-y-6">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">01</span>
                            <h3 class="text-2xl font-display font-bold text-white">Blueprint & Clinical Governance</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">In healthcare data engineering, we don't just deal with "strings" and "integers." We deal with **Clinical Standards** like **ICD-10** (Diagnosis), **CPT/HCPCS** (Procedures), and **HL7/FHIR** (Interoperability). Our blueprint must account for the complexity of these codes. A mistake in a procedure code transformation could lead to a rejected claim worth lakhs.</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="glass-card p-4 rounded border border-cyber-500/10 bg-slate-900/40">
                                <h6 class="text-xs font-bold text-cyber-400 mb-2">PII CLASSIFICATION</h6>
                                <p class="text-[10px] text-slate-500 leading-relaxed">We classify data into: 
                                <br>1. **Public** (Hospital names)
                                <br>2. **Internal** (Staff IDs)
                                <br>3. **Confidential/PII** (Aadhaar, Phone)
                                <br>4. **Highly Sensitive/PHI** (Diagnosis, Genetic history)</p>
                            </div>
                            <div class="glass-card p-4 rounded border border-cyber-500/10 bg-slate-900/40">
                                <h6 class="text-xs font-bold text-cyber-400 mb-2">SOURCE INVENTORY</h6>
                                <p class="text-[10px] text-slate-500 leading-relaxed">Mapping 7 disparate systems (MySQL, Cosmos, REST) into a unified Medallion schema. This is the hardest part of the project.</p>
                            </div>
                        </div>
                    </section>

                    <!-- Module 2 -->
                    <section id="m2" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">02</span>
                            <h3 class="text-2xl font-display font-bold text-white">Enterprise IaC & Security</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">Setting up resources is about more than just `terraform apply`. We implement a **Zero-Trust Security Model**. This means:
                        <br>1. **Private Endpoints**: Data never travels over the public internet.
                        <br>2. **Managed Identities**: No passwords stored in ADF; resources talk to each other via Entra ID (Azure AD) tokens.
                        <br>3. **Key Vault RBAC**: Only the ADF service principal can "get" secrets; even the developer can't see them in production.</p>
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[IAC]</span> Creating Private Link Service for ADLS...</div>
                            <div class="log-line"><span class="status-tag">[IAC]</span> Configuring Key Vault Access Policies for Managed Identity...</div>
                            <div class="log-line text-green-400"><span class="status-tag">[IAC]</span> Infrastructure Hardening Complete.</div>
                        </div>
                    </section>

                    <!-- Module 3 -->
                    <section id="m3" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">03</span>
                            <h3 class="text-2xl font-display font-bold text-white">Ingestion (Bronze & Schema Drift)</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">When ingesting from 7 sources, the source schema *will* change. We handle this using **Schema Drift** features in ADF and **mergeSchema** in Delta Lake. If a source adds a "Blood Group" column, our pipeline automatically adds it to Bronze without failing.</p>
                        <div class="glass-card p-6 rounded-xl border border-cyber-500/20">
                            <h5 class="text-white text-sm font-bold mb-4">The Watermark Strategy:</h5>
                            <p class="text-xs text-slate-400 mb-4">To avoid re-reading 100GB every day, we use an incremental watermark. We store the <code>MAX(updated_at)</code> for every table in an Azure SQL "Control Table."</p>
                            <div class="code-snippet">
                                SELECT * FROM source_table 
                                WHERE last_modified > '@{pipeline().parameters.last_watermark}'
                            </div>
                        </div>
                    </section>

                    <!-- Module 4 -->
                    <section id="m4" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">04</span>
                            <h3 class="text-2xl font-display font-bold text-white">Processing (Silver & SCD Logic)</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">Silver is the **Source of Truth**. We use **Slowly Changing Dimensions (SCD Type 2)** to maintain a history of patient address changes, insurance plan upgrades, and physician assignments. This allows us to run "Point-in-Time" reports—seeing what the data looked like on any specific date in the past.</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="p-4 bg-slate-800/50 rounded border border-slate-700">
                                <h6 class="text-cyber-400 text-xs font-bold mb-2">UPSERT (MERGE)</h6>
                                <p class="text-[10px] text-slate-400">We use the <code>MERGE INTO</code> command in Delta Lake to efficiently update existing records and insert new ones in a single atomic transaction.</p>
                            </div>
                            <div class="p-4 bg-slate-800/50 rounded border border-slate-700">
                                <h6 class="text-cyber-400 text-xs font-bold mb-2">VACUUM & OPTIMIZE</h6>
                                <p class="text-[10px] text-slate-400">To prevent "Small File Problem," we run <code>OPTIMIZE</code> weekly. To save storage costs, we <code>VACUUM</code> old Delta versions after 7 days.</p>
                            </div>
                        </div>
                    </section>

                    <!-- Module 5 -->
                    <section id="m5" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">05</span>
                            <h3 class="text-2xl font-display font-bold text-white">Serving (Synapse Performance)</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">Synapse is a distributed engine. To make it fly, we use **Distribution Keys**. 
                        <br>— **Hash Distribution**: Use for Fact tables (distribute by PatientID).
                        <br>— **Replicate Distribution**: Use for small Dimension tables (copy to every compute node).
                        <br>— **Round Robin**: Use for staging tables where no clear join key exists.</p>
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[DB]</span> Generating Statistics for Join Columns...</div>
                            <div class="log-line"><span class="status-tag">[DB]</span> Applying Materialized Views for Patient KPI summaries...</div>
                            <div class="log-line text-green-400"><span class="status-tag">[DB]</span> Query Performance Optimized (Sub-second response).</div>
                        </div>
                    </section>

                    <!-- Module 6 -->
                    <section id="m6" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">06</span>
                            <h3 class="text-2xl font-display font-bold text-white">Analytics (Power BI Depth)</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">A good dashboard is 50% visuals and 50% **DAX performance**. We use **DirectQuery** with **Aggregations**. This means simple charts use a fast "Import" summary, while deep drill-throughs trigger a live SQL query to Synapse. This gives the best of both worlds: speed and real-time detail.</p>
                        <div class="glass-card p-6 rounded-xl border border-yellow-500/20 bg-yellow-500/5">
                            <h6 class="text-xs font-bold text-yellow-400 mb-2">ADVANCED DAX: LFL Growth</h6>
                            <code>LFL_Growth = DIVIDE([Current Admissions] - [Prev Year Admissions], [Prev Year Admissions])</code>
                        </div>
                    </section>

                    <!-- Module 7 -->
                    <section id="m7" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">07</span>
                            <h3 class="text-2xl font-display font-bold text-white">Monitoring & KQL Logs</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">We pipe all ADF and Databricks logs to **Log Analytics**. Using **Kusto Query Language (KQL)**, we create custom dashboards that track "Data Freshness"—telling us if any table hasn't been updated in 24 hours. We also monitor **Databricks Cluster Utilization** to downscale and save costs during idle night hours.</p>
                        <div class="code-snippet">
                            # KQL Example: Find Failed Pipeline Runs
                            ADFPipelineRun | where Status == "Failed" 
                            | project PipelineName, Start, ErrorMessage
                        </div>
                    </section>

                    <!-- Module 8 -->
                    <section id="m8" class="space-y-6 border-t border-slate-800 pt-16">
                        <div class="flex items-center gap-4">
                            <span class="text-4xl font-display font-bold text-cyber-500/20">08</span>
                            <h3 class="text-2xl font-display font-bold text-white">DevOps & Release Gates</h3>
                        </div>
                        <p class="text-slate-400 leading-relaxed">In an enterprise setting, we never "Publish" directly from the ADF UI to PROD. We use **Release Gates**. Before code moves to PROD:
                        <br>1. **Unit Tests** must pass in Databricks.
                        <br>2. **Data Quality (DQ) Validation** must confirm zero nulls in Primary Keys.
                        <br>3. **Security Approval**: A scan confirms no raw Aadhaar numbers exist in the Silver layer.</p>
                        <div class="init-log">
                            <div class="log-line"><span class="status-tag">[GATE]</span> Waiting for QA Approval... OK</div>
                            <div class="log-line"><span class="status-tag">[GATE]</span> Checking DQ Scorecard... [Score: 99.8%] OK</div>
                            <div class="log-line text-green-400"><span class="status-tag">[GATE]</span> Promotion to PRODUCTION Authorized.</div>
                        </div>
                    </section>

                </div>
            </div>
        </div>
    </div>

    <!-- ========================================== -->
    <!-- MODE 5: DOCS HUB (Terminal Style)          -->
    <!-- ========================================== -->
    <div id="view-docs" class="view-panel">
        <div style="display:flex;height:100%;width:100%;">
            <aside class="w-80 flex-shrink-0 flex flex-col glass-panel h-full z-20 border-r border-cyber-500/30">
                <div class="p-4 border-b border-cyber-500/30 bg-slate-900/50">
                    <div class="relative">
                        <i data-lucide="search" class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-cyber-500"></i>
                        <input type="text" id="searchInput" placeholder="grep search {total_files} files..." class="w-full bg-[#050a15] border border-cyber-500/30 text-xs font-mono rounded pl-9 pr-4 py-2.5 focus:outline-none focus:border-cyber-400 focus:shadow-[0_0_10px_rgba(0,240,255,0.3)] text-cyber-100 placeholder-cyber-500/50 transition-all">
                    </div>
                </div>
                <div class="flex-1 overflow-y-auto py-4 px-2 custom-scrollbar" id="sidebar-content"></div>
            </aside>

            <main class="flex-1 flex flex-col h-full relative z-10 bg-[#050a15]/90 backdrop-blur-md">
                <header class="h-12 bg-[#050a15] border-b border-cyber-500/30 flex items-center px-8 justify-between shrink-0 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
                    <div class="flex items-center gap-2 text-xs font-mono text-cyber-500/70" id="breadcrumb">
                        <span>WAITING FOR INPUT</span>
                    </div>
                    <div class="flex items-center gap-4">
                        <button onclick="copyContent()" class="text-xs font-mono text-cyber-400 hover:text-white flex items-center gap-1 bg-cyber-500/10 px-3 py-1 rounded border border-cyber-500/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.3)] transition-all">
                            <i data-lucide="copy" class="w-3 h-3"></i> YANK
                        </button>
                    </div>
                </header>
                <div class="flex-1 overflow-y-auto p-8 lg:p-12 custom-scrollbar" id="scroll-container">
                    <div class="max-w-5xl mx-auto">
                        <article id="markdown-content" class="prose prose-invert max-w-none bg-[#0a0f1c] p-10 lg:p-16 rounded border border-cyber-500/20 shadow-[0_0_30px_rgba(0,0,0,0.8)]">
                            <div class="text-center py-32 text-cyber-500/30">
                                <i data-lucide="terminal-square" class="w-20 h-20 mx-auto mb-6 opacity-50"></i>
                                <p class="font-mono text-sm tracking-widest">> AWAITING FILE SELECTION_</p>
                            </div>
                        </article>
                    </div>
                </div>
            </main>
        </div>
    </div><!-- /view-container -->

    <!-- JSON data as base64 - completely safe, no </script> injection possible -->
    <script id="docs-data-store" type="application/x-b64json">{json_data_b64}</script>

    <script>
        const docsData = JSON.parse(atob(document.getElementById('docs-data-store').textContent.trim()));
        let currentRawContent = "";

        function switchMode(mode) {{
            const modes = ['learning','setup','office','docs','masterclass'];
            // JavaScript-managed CSS approach: Remove relying on fragile CSS class toggling
            modes.forEach(function(m) {{
                var v = document.getElementById('view-' + m);
                var b = document.getElementById('btn-' + m);
                if(v) {{
                    v.style.display = 'none';
                }}
                if(b) {{
                    b.style.color = '#94a3b8';
                    b.style.borderBottom = 'none';
                    b.style.textShadow = 'none';
                }}
            }});
            
            // Activate the chosen panel and button directly via styles
            var target = document.getElementById('view-' + mode);
            var btn = document.getElementById('btn-' + mode);
            if(target) {{
                if (mode === 'docs') {{
                    target.style.display = 'flex';
                }} else {{
                    target.style.display = 'block';
                }}
            }}
            if(btn) {{
                btn.style.color = '#00f0ff';
                btn.style.borderBottom = '2px solid #00f0ff';
                btn.style.textShadow = '0 0 10px rgba(0,240,255,0.5)';
            }}
        }}

        window.openDoc = function(folder, fileTitle) {{
            switchMode('docs');
            // Give the panel time to become visible before trying to scroll to items
            setTimeout(() => {{
                const folderHeaders = document.querySelectorAll('.folder-header');
                folderHeaders.forEach(h => {{
                    if (h.innerText.trim().includes(formatFolderName(folder))) {{
                        const content = h.nextElementSibling;
                        const isClosed = !content.style.maxHeight || content.style.maxHeight === '0px';
                        if (isClosed) toggleFolder(h);
                    }}
                }});
                loadDocument(folder, fileTitle);
            }}, 50);
        }}

        marked.setOptions({{ highlight: function(code, lang) {{ return hljs.highlight(code, {{ language: hljs.getLanguage(lang)?lang:'plaintext' }}).value; }}, langPrefix: 'hljs language-' }});

        function init() {{ switchMode('learning'); renderSidebar(); setupSearch(); lucide.createIcons(); }}

        function formatFolderName(name) {{ return name === '00_Root' ? 'ROOT' : name.replace(/^[0-9]+_/, '').replace(/_/g, ' ').toUpperCase(); }}
        function formatFileName(name) {{ return name.replace(/_/g, ' '); }}

        function renderSidebar(filterText = '') {{
            const sidebar = document.getElementById('sidebar-content');
            sidebar.innerHTML = '';
            const term = filterText.toLowerCase();

            for (const [folder, files] of Object.entries(docsData)) {{
                const filteredFiles = files.filter(f => f.title.toLowerCase().includes(term) || f.content.toLowerCase().includes(term));
                if (filteredFiles.length === 0) continue;

                const folderDiv = document.createElement('div');
                folderDiv.className = 'mb-1';
                const isOpen = term !== '' || folder === '01_business_requirements';
                
                folderDiv.innerHTML = `
                    <div class="folder-header flex items-center justify-between px-3 py-2 text-xs font-mono font-bold text-cyber-500/80 rounded hover:bg-cyber-500/10 hover:text-cyber-300 select-none cursor-pointer transition-colors ${{isOpen ? 'bg-cyber-500/10 text-cyber-300' : ''}}" onclick="toggleFolder(this)">
                        <div class="flex items-center gap-2">
                            <i data-lucide="${{isOpen ? 'folder-open' : 'folder'}}" class="w-4 h-4 text-cyber-500"></i>
                            <span class="truncate tracking-wider">${{formatFolderName(folder)}}</span>
                        </div>
                        <i data-lucide="chevron-${{isOpen ? 'down' : 'right'}}" class="w-3 h-3 transition-transform text-cyber-500"></i>
                    </div>
                    <div class="folder-content overflow-hidden transition-all duration-300" style="max-height: ${{isOpen ? '2000px' : '0px'}}">
                        <ul class="pt-1 pb-2 space-y-px"></ul>
                    </div>
                `;
                
                const ul = folderDiv.querySelector('ul');
                filteredFiles.forEach(file => {{
                    let iconName = 'file-text';
                    if(file.title.endsWith('.py')) iconName = 'file-code';
                    else if(file.title.endsWith('.sql')) iconName = 'database';
                    else if(file.title.endsWith('.json')) iconName = 'file-json';
                    else if(file.title.endsWith('.ps1')) iconName = 'terminal';

                    const li = document.createElement('li');
                    li.className = 'nav-item text-xs font-mono text-slate-400 pl-9 pr-3 py-1.5 rounded relative flex items-center gap-2 cursor-pointer transition-all hover:bg-cyber-500/10 hover:text-cyber-100 border-l-2 border-transparent hover:border-cyber-400';
                    li.innerHTML = `<i data-lucide="${{iconName}}" class="w-3 h-3 text-cyber-600"></i><span class="truncate">${{formatFileName(file.title)}}</span>`;
                    li.onclick = () => loadDocument(folder, file.title);
                    li.dataset.folder = folder; li.dataset.file = file.title;
                    ul.appendChild(li);
                }});
                sidebar.appendChild(folderDiv);
            }}
            lucide.createIcons();
        }}

        window.toggleFolder = function(element) {{
            const content = element.nextElementSibling;
            const chevronIconSvg = element.querySelector('.lucide-chevron-right, .lucide-chevron-down');
            const folderIconSvg = element.querySelector('.lucide-folder, .lucide-folder-open');
            
            const isClosed = !content.style.maxHeight || content.style.maxHeight === '0px' || content.style.maxHeight === '0';
            
            if (!isClosed) {{
                content.style.maxHeight = '0px';
                if(chevronIconSvg) chevronIconSvg.outerHTML = '<i data-lucide="chevron-right" class="w-3 h-3 transition-transform text-cyber-500"></i>';
                if(folderIconSvg) folderIconSvg.outerHTML = '<i data-lucide="folder" class="w-4 h-4 text-cyber-500"></i>';
                element.classList.remove('bg-cyber-500/10', 'text-cyber-300');
            }} else {{
                content.style.maxHeight = '2000px';
                if(chevronIconSvg) chevronIconSvg.outerHTML = '<i data-lucide="chevron-down" class="w-3 h-3 transition-transform text-cyber-500"></i>';
                if(folderIconSvg) folderIconSvg.outerHTML = '<i data-lucide="folder-open" class="w-4 h-4 text-cyber-500"></i>';
                element.classList.add('bg-cyber-500/10', 'text-cyber-300');
            }}
            lucide.createIcons();
        }}

        function loadDocument(folder, title) {{
            document.querySelectorAll('.nav-item').forEach(el => {{ el.classList.remove('bg-cyber-500/20', 'text-white', 'border-cyber-400'); el.classList.add('text-slate-400', 'border-transparent'); }});
            const activeEl = document.querySelector(`.nav-item[data-folder="${{folder}}"][data-file="${{title}}"]`);
            if(activeEl) {{ activeEl.classList.remove('text-slate-400', 'border-transparent'); activeEl.classList.add('bg-cyber-500/20', 'text-white', 'border-cyber-400'); }}

            const file = docsData[folder].find(f => f.title === title);
            if (!file) return;

            // Extract content (removing markdown code fences if it's a code file, for raw copy)
            let rawForCopy = file.content;
            if (title.endsWith('.py') || title.endsWith('.sql') || title.endsWith('.json') || title.endsWith('.ps1')) {{
                rawForCopy = file.content.replace(/^```[a-z]*\\n/, '').replace(/\\n```$/, '');
            }}
            currentRawContent = rawForCopy;

            document.getElementById('breadcrumb').innerHTML = `<span class="opacity-50">~/${{formatFolderName(folder)}}/</span><span class="text-cyber-300 font-bold">${{title}}</span>`;

            const contentDiv = document.getElementById('markdown-content');
            contentDiv.style.opacity = 0;
            setTimeout(() => {{
                contentDiv.innerHTML = marked.parse(file.content);
                
                // Add tech styling
                contentDiv.querySelectorAll('h1, h2, h3').forEach(h => h.classList.add('font-display', 'text-cyber-100'));
                contentDiv.querySelectorAll('code').forEach(c => c.classList.add('font-mono', 'text-cyber-400'));
                contentDiv.querySelectorAll('table').forEach(t => t.classList.add('border-collapse', 'w-full', 'text-sm', 'font-mono', 'my-6'));
                contentDiv.querySelectorAll('th').forEach(th => th.classList.add('border-b-2', 'border-cyber-500', 'text-left', 'p-3', 'text-cyber-300', 'bg-cyber-500/10'));
                contentDiv.querySelectorAll('td').forEach(td => td.classList.add('border-b', 'border-slate-800', 'p-3', 'text-slate-300'));
                
                // Style code blocks specifically
                contentDiv.querySelectorAll('pre').forEach(p => p.classList.add('my-6', 'shadow-[0_0_15px_rgba(0,0,0,0.5)]'));

                contentDiv.style.transition = 'opacity 0.3s';
                contentDiv.style.opacity = 1;
                lucide.createIcons();
            }}, 100);
            document.getElementById('scroll-container').scrollTop = 0;
        }}

        function setupSearch() {{
            const searchInput = document.getElementById('searchInput');
            let timeout = null;
            searchInput.addEventListener('input', (e) => {{ clearTimeout(timeout); timeout = setTimeout(() => {{ renderSidebar(e.target.value); }}, 300); }});
        }}
        
        window.copyContent = function() {{ if(!currentRawContent) return; navigator.clipboard.writeText(currentRawContent).then(() => alert('YANK SUCCESSFUL: File contents copied to clipboard.')); }}
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"Successfully injected Code Files (.py, .sql, .json) into UI: {output_file}")
print(f"Total files processed: {total_files}")
