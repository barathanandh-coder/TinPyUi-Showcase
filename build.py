import os
import subprocess
import shutil
import json

def patch_ir():
    ir_path = 'public/app.ir.json'
    if not os.path.exists(ir_path): return
    with open(ir_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Map node texts to actions
    actions_map = {
        "Features": "scrollToFeatures",
        "Showcase": "scrollToShowcase",
        "Reviews": "scrollToReviews",
        "Install": "scrollToInstall",
        "GitHub": "openGithub",
        "Get Started": "scrollToInstall",
        "View Demo": "scrollToShowcase",
        "Star on GitHub": "openGithub",
        "View on npm": "openNpm",
        "Submit Review": "submitReview",
        "-": "decrement",
        "+": "increment"
    }
    
    # Also we want some nodes to look like buttons
    text_map = {}
    for node in data.get('nodes', []):
        if node['op'] == 'SET_TEXT':
            text_map[node['id']] = node.get('value', '')
            
    for node in data.get('nodes', []):
        if node['op'] == 'CREATE_NODE':
            node_id = node['id']
            text = text_map.get(node_id, "")
            if text in actions_map:
                data['nodes'].append({
                    "op": "SET_ATTRIBUTE",
                    "id": node_id,
                    "key": "data-action",
                    "value": actions_map[text]
                })
                # Add cursor pointer style
                data['nodes'].append({
                    "op": "SET_ATTRIBUTE",
                    "id": node_id,
                    "key": "style",
                    "value": "cursor: pointer;"
                })
                
    with open(ir_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def build():
    print("Compiling TinPyUI...")
    result = subprocess.run([r"..\TinUi\tinui.exe", "compile", "src/index.tin"], shell=True)
    if result.returncode != 0:
        print("Compilation failed.")
        return

    print("Patching IR for missing actions...")
    patch_ir()

    print("Restoring framework files to public/...")
    public_dir = "public"
    os.makedirs(public_dir, exist_ok=True)
    
    # Write index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TinPyUI App</title>
    <script src="wasm_exec.js"></script>
    <script>
        const go = new Go();
        WebAssembly.instantiateStreaming(fetch("tinui_engine.wasm"), go.importObject).then((result) => {
            go.run(result.instance);
            
            const fetchAndRenderReviews = () => {
                fetch('/api/reviews').then(res => res.json()).then(reviews => {
                    let container = document.getElementById('reviewsList');
                    if(container) {
                        let html = '';
                        reviews.forEach(r => {
                            let initials = (r.name && r.name.length >= 2) ? r.name.substring(0,2).toUpperCase() : 'AN';
                            html += `
                            <div style="display:flex;flex-direction:column;gap:16px;padding:32px;background:rgba(255,255,255,0.03);border:1px solid rgba(139,92,246,0.1);border-radius:20px;text-align:left;">
                                <div style="display:flex;align-items:center;gap:14px;">
                                    <div style="color:white;background:linear-gradient(45deg, #9b51e0, #00f2fe);padding:12px;border-radius:50%;font-weight:bold;width:24px;height:24px;display:flex;align-items:center;justify-content:center;">${initials}</div>
                                    <div style="display:flex;flex-direction:column;gap:4px;">
                                        <div style="color:white;font-weight:bold;">${r.name}</div>
                                        <div style="color:#6b7280;font-size:0.875rem;">${r.handle}</div>
                                    </div>
                                </div>
                                <div style="color:#eab308;">${r.rating}</div>
                                <div style="color:#d1d5db;font-size:0.875rem;line-height:1.7;">${r.content}</div>
                            </div>
                            `;
                        });
                        container.innerHTML = html;
                    }
                }).catch(e => console.error('Failed to fetch reviews', e));
            };
            
            // Start the TinUI engine with the generated Intermediate Representation
            const bootApp = () => {
                fetch("app.ir.json").then(res => res.text()).then(irString => {
                    try {
                        let ret = BootTinUI(irString);
                        if (ret) {
                            console.log(ret);
                        }
                        
                        setTimeout(fetchAndRenderReviews, 100); // Fetch once UI has booted

                        // Wire up global event listeners for TinUI interactivity
                        document.addEventListener('click', (e) => {
                            let actionElement = e.target.closest ? e.target.closest('[data-action]') : e.target;
                            let action = null;
                            if (actionElement && actionElement.getAttribute) {
                                action = actionElement.getAttribute('data-action');
                            }
                            
                            // Fallback: Check text content if WASM engine dropped data-action
                            if (!action && e.target && e.target.textContent) {
                                let t = e.target.textContent.trim();
                                if (t === 'Features') action = 'scrollToFeatures';
                                else if (t === 'Showcase') action = 'scrollToShowcase';
                                else if (t === 'Reviews') action = 'scrollToReviews';
                                else if (t === 'Install' || t === 'Get Started') action = 'scrollToInstall';
                                else if (t === 'GitHub' || t === 'Star on GitHub') action = 'openGithub';
                                else if (t === 'View Demo') action = 'scrollToShowcase';
                                else if (t === 'View on npm') action = 'openNpm';
                                else if (t === 'Submit Review') action = 'submitReview';
                                else if (t === '-') action = 'decrement';
                                else if (t === '+') action = 'increment';
                            }
                            
                            if (action) {
                                if (action === 'decrement') {
                                    let current = parseInt(window.demoCounter || 42);
                                    window.demoCounter = current - 1;
                                    document.querySelectorAll('[data-bind="counterVal"]').forEach(el => el.textContent = window.demoCounter);
                                } else if (action === 'increment') {
                                    let current = parseInt(window.demoCounter || 42);
                                    window.demoCounter = current + 1;
                                    document.querySelectorAll('[data-bind="counterVal"]').forEach(el => el.textContent = window.demoCounter);
                                } else if (action === 'scrollToFeatures') {
                                    document.getElementById('features').scrollIntoView({behavior: 'smooth'});
                                } else if (action === 'scrollToShowcase') {
                                    document.getElementById('showcase').scrollIntoView({behavior: 'smooth'});
                                } else if (action === 'scrollToReviews') {
                                    document.getElementById('reviews').scrollIntoView({behavior: 'smooth'});
                                } else if (action === 'scrollToInstall') {
                                    document.getElementById('install').scrollIntoView({behavior: 'smooth'});
                                } else if (action === 'openGithub') {
                                    window.open('https://github.com/barathanandh-coder/tinui', '_blank');
                                } else if (action === 'openNpm') {
                                    window.open('https://www.npmjs.com/package/tinpyui', '_blank');
                                } else if (action === 'submitReview') {
                                    // Wait, the WASM engine might have also dropped data-bind on the inputs!
                                    // If so, we need to grab values by placeholder or just tag name since it's a simple form.
                                    // Let's try grabbing by placeholders as a highly robust fallback.
                                    let nameInput = document.querySelector('[data-bind="reviewName"]') || document.querySelector('input[placeholder="Your Name"]');
                                    let handleInput = document.querySelector('[data-bind="reviewHandle"]') || document.querySelector('input[placeholder*="Your Handle"]');
                                    let contentInput = document.querySelector('[data-bind="reviewContent"]') || document.querySelector('input[placeholder*="Write your review"]');
                                    
                                    let name = nameInput?.value || 'Anonymous';
                                    let handle = handleInput?.value || '@user';
                                    let content = contentInput?.value || '';
                                    
                                    if (content.trim() === '') {
                                        alert('Review content cannot be empty!');
                                        return;
                                    }
                                    
                                    fetch('/api/reviews', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ name: name, handle: handle, rating: '★★★★★', content: content })
                                    }).then(res => res.json()).then(data => {
                                        if(data.status === 'success') {
                                            if(contentInput) contentInput.value = '';
                                            fetchAndRenderReviews();
                                        } else {
                                            alert('Failed to submit review');
                                        }
                                    });
                                }

                                if (typeof TinUIDispatch === 'function') {
                                    TinUIDispatch(action);
                                }
                            }
                        });

                        document.addEventListener('input', (e) => {
                            let stateKey = e.target.getAttribute('data-bind');
                            if (stateKey && typeof TinUIMutateState === 'function') {
                                TinUIMutateState(stateKey, e.target.value);
                            }
                        });
                    } catch(e) {
                        console.error("TinUI Boot Error:", e);
                        document.getElementById('tinui-root').innerHTML = "JS Error: " + e.message;
                    }
                }).catch(e => {
                    console.error("Failed to fetch app.ir.json:", e);
                    document.getElementById('tinui-root').innerHTML = "Failed to load app.ir.json";
                });
            };

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', bootApp);
            } else {
                bootApp();
            }
        }).catch((err) => {
            console.error("WASM Boot Error:", err);
            const displayErr = () => {
                document.getElementById('tinui-root').innerHTML = "<div style='padding: 20px; color: #ff5555;'>Failed to start WebAssembly engine: " + err.message + "<br><br><b>Note:</b> You cannot open this file directly in the browser. You MUST use a local web server (e.g. run <code>tinpyui serve</code> or start your Flask app).</div>";
            };
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', displayErr);
            } else {
                displayErr();
            }
        });
    </script>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0b10; color: #ffffff; font-family: 'Inter', sans-serif;">
    <div id="tinui-root"></div>
</body>
</html>"""
    with open(os.path.join(public_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
        
    # Copy wasm files from local TinUi build instead of global npm
    local_bin_dir = r"..\TinUi\tinui-npm\bin"
    
    wasm_exec = os.path.join(local_bin_dir, "wasm_exec.js")
    tinui_engine = os.path.join(local_bin_dir, "tinui_engine.wasm")
    
    if os.path.exists(wasm_exec):
        shutil.copy(wasm_exec, os.path.join(public_dir, "wasm_exec.js"))
    if os.path.exists(tinui_engine):
        shutil.copy(tinui_engine, os.path.join(public_dir, "tinui_engine.wasm"))
        
    print("Build complete! You can now view the app.")

if __name__ == "__main__":
    build()
