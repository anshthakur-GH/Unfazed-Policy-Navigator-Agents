import os
import requests
from flask import Flask, request, send_from_directory, jsonify, Response

app = Flask(__name__, static_folder='.')

# Configurable Webhook Endpoints
TARGET_URLS = {
    "process_doc": "https://n8n.cognigenai.in/webhook/0577d629-452d-45d5-ba0a-260934fcc50e",
    "eligibility": "https://test-n8n.zynd.ai/webhook/299f8076-3169-4b30-99d7-66b25015088b",
    "other_policies": "https://test-n8n.zynd.ai/webhook/1cf41349-c5de-4ed3-8be9-e764406dc28e/pay"
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

@app.route('/proxy', methods=['POST', 'OPTIONS'])
def proxy():
    if request.method == 'OPTIONS':
        return Response(status=204)

    target_key = request.args.get('target', 'eligibility')
    target_url = TARGET_URLS.get(target_key, TARGET_URLS["eligibility"])
    
    # Forward query parameters (except 'target')
    forward_params = {k: v for k, v in request.args.items() if k != 'target'}
    
    # Get original headers, filter out restricted ones
    headers = {k: v for k, v in request.headers if k.lower().startswith('x-')}
    headers['Content-Type'] = request.content_type

    print(f"✦ Forwarding {target_key} -> {target_url}")

    try:
        # We use stream=True for large docs, but standard POST for eligibility
        resp = requests.post(
            target_url,
            params=forward_params,
            data=request.get_data(),
            headers=headers,
            timeout=60
        )
        
        # Exclude hop-by-hop headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        resp_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                       if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, resp_headers)
        
    except requests.exceptions.RequestException as e:
        print(f"  [Proxy Error] {str(e)}")
        return jsonify({"error": "Failed to reach backend agent", "details": str(e)}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    app.run(host='0.0.0.0', port=port)
