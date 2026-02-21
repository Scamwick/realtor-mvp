#!/usr/bin/env python3
"""
Realtor AI MVP - Production Version
Uses Claude API directly (no CLI wrapper dependency)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import os
import subprocess

app = FastAPI(title="Realtor AI MVP")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def call_claude(prompt: str) -> str:
    """Call Claude via subprocess (claude CLI)"""
    try:
        result = subprocess.run(
            ["claude", "message", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ}
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"Claude CLI error: {e}")
        raise

async def generate_description(listing_data: dict) -> str:
    """Generate MLS listing description"""
    prompt = f"""You are a professional real estate copywriter. Write a compelling MLS listing description.

Property Details:
- Address: {listing_data.get('address', 'N/A')}
- Bedrooms: {listing_data.get('bedrooms', 'N/A')}
- Bathrooms: {listing_data.get('bathrooms', 'N/A')}
- Square Feet: {listing_data.get('sqft', 'N/A')}
- Price: ${listing_data.get('price', 'N/A'):,.0f}
- Year Built: {listing_data.get('year_built', 'N/A')}
- Features: {listing_data.get('features', 'N/A')}
- Neighborhood: {listing_data.get('neighborhood', 'N/A')}

Write a captivating 3-4 paragraph listing description that:
1. Opens with an engaging hook
2. Highlights key features and benefits
3. Paints a picture of lifestyle
4. Creates urgency/appeal

Make it persuasive, professional, and perfect for MLS."""

    try:
        return await call_claude(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate description: {str(e)}")

async def generate_cma(comparable_sales: list) -> str:
    """Generate Comparative Market Analysis"""
    comparables_text = "\n".join([
        f"- {comp['address']}: ${comp['price']:,.0f} ({comp['sqft']} sqft, {comp['beds']} bed, {comp['baths']} bath)"
        for comp in comparable_sales
    ])

    prompt = f"""You are a professional real estate appraiser. Analyze these comparable sales and provide a market analysis report.

COMPARABLE SALES:
{comparables_text}

Provide a brief CMA report that includes:
1. Average Price Per Square Foot
2. Market Trends (up/down/stable)
3. Recommended Price Range (with reasoning)
4. Key Market Factors
5. Investment Opportunity Assessment

Make it professional and suitable for MLS presentation."""

    try:
        return await call_claude(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CMA: {str(e)}")

async def generate_followup_email(agent_name: str, buyer_profile: dict) -> str:
    """Generate personalized follow-up email"""
    prompt = f"""You are a professional real estate agent. Write a personalized follow-up email.

Agent Name: {agent_name}
Buyer Profile:
- Interests: {buyer_profile.get('interests', 'N/A')}
- Budget: ${buyer_profile.get('budget', 'N/A'):,.0f}
- Timeline: {buyer_profile.get('timeline', 'N/A')}
- Previous Inquiries: {buyer_profile.get('previous_inquiries', 'N/A')}

Write a warm, personalized follow-up email that:
1. References previous interaction
2. Shows genuine interest
3. Offers value (market insights, new listings)
4. Includes soft call-to-action
5. Professional but conversational tone

Make it compelling and personal."""

    try:
        return await call_claude(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Realtor AI - MLS Generator</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            h1 {
                grid-column: 1 / -1;
                color: white;
                margin-bottom: 20px;
                font-size: 2.5em;
            }
            .card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            .card h2 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.4em;
            }
            .form-group {
                margin-bottom: 12px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            input, textarea, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
            }
            textarea {
                resize: vertical;
                min-height: 80px;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                width: 100%;
                margin-top: 10px;
            }
            button:hover {
                opacity: 0.9;
            }
            .output {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 6px;
                margin-top: 15px;
                max-height: 300px;
                overflow-y: auto;
                white-space: pre-wrap;
                word-break: break-word;
                font-size: 13px;
                line-height: 1.5;
                display: none;
            }
            .output.active {
                display: block;
            }
            .loading {
                display: none;
                color: #667eea;
                font-size: 14px;
            }
            .loading.active {
                display: block;
            }
            .error {
                background: #fee;
                color: #c33;
                padding: 10px;
                border-radius: 4px;
                margin-top: 10px;
                display: none;
            }
            .error.active {
                display: block;
            }
            @media (max-width: 768px) {
                .container { grid-template-columns: 1fr; }
                h1 { font-size: 1.8em; }
            }
        </style>
    </head>
    <body>
        <h1>🏠 Realtor AI MVP</h1>

        <div class="container">
            <div class="card">
                <h2>📝 MLS Description Generator</h2>
                <form onsubmit="generateDescription(event)">
                    <div class="form-group">
                        <label>Address</label>
                        <input type="text" id="desc_address" placeholder="123 Main St, City, State" required>
                    </div>
                    <div class="form-group">
                        <label>Bedrooms</label>
                        <input type="number" id="desc_bedrooms" placeholder="3" required>
                    </div>
                    <div class="form-group">
                        <label>Bathrooms</label>
                        <input type="number" id="desc_bathrooms" placeholder="2" step="0.5" required>
                    </div>
                    <div class="form-group">
                        <label>Square Feet</label>
                        <input type="number" id="desc_sqft" placeholder="2400" required>
                    </div>
                    <div class="form-group">
                        <label>Price</label>
                        <input type="number" id="desc_price" placeholder="500000" required>
                    </div>
                    <div class="form-group">
                        <label>Year Built</label>
                        <input type="number" id="desc_year_built" placeholder="2020" required>
                    </div>
                    <div class="form-group">
                        <label>Features (comma separated)</label>
                        <textarea id="desc_features" placeholder="Updated kitchen, hardwood floors, garden"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Neighborhood</label>
                        <input type="text" id="desc_neighborhood" placeholder="Downtown, Suburbs, etc." required>
                    </div>
                    <button type="submit">Generate Description</button>
                    <div class="loading" id="desc_loading">Generating...</div>
                    <div class="error" id="desc_error"></div>
                    <div class="output" id="desc_output"></div>
                </form>
            </div>

            <div class="card">
                <h2>📊 CMA Report Generator</h2>
                <form onsubmit="generateCMA(event)">
                    <div class="form-group">
                        <label>Comparables (JSON format)</label>
                        <textarea id="cma_comparables" placeholder='[{"address":"456 Pine St","price":1300000,"sqft":2500,"beds":3,"baths":2}]' required>[{"address":"456 Pine St","price":1300000,"sqft":2500,"beds":3,"baths":2}]</textarea>
                    </div>
                    <button type="submit">Generate CMA</button>
                    <div class="loading" id="cma_loading">Generating...</div>
                    <div class="error" id="cma_error"></div>
                    <div class="output" id="cma_output"></div>
                </form>
            </div>

            <div class="card">
                <h2>💌 Follow-up Email Generator</h2>
                <form onsubmit="generateEmail(event)">
                    <div class="form-group">
                        <label>Agent Name</label>
                        <input type="text" id="email_agent_name" placeholder="Your Name" required>
                    </div>
                    <div class="form-group">
                        <label>Buyer Profile (JSON)</label>
                        <textarea id="email_buyer_profile" placeholder='{"interests":["Modern homes"],"budget":500000,"timeline":"3 months","previous_inquiries":"Viewed 3 properties"}' required>{"interests":["Modern homes"],"budget":500000,"timeline":"3 months","previous_inquiries":"Viewed 3 properties"}</textarea>
                    </div>
                    <button type="submit">Generate Email</button>
                    <div class="loading" id="email_loading">Generating...</div>
                    <div class="error" id="email_error"></div>
                    <div class="output" id="email_output"></div>
                </form>
            </div>
        </div>

        <script>
            async function generateDescription(e) {
                e.preventDefault();
                const output = document.getElementById('desc_output');
                const loading = document.getElementById('desc_loading');
                const error = document.getElementById('desc_error');

                loading.classList.add('active');
                error.classList.remove('active');
                output.classList.remove('active');

                try {
                    const response = await fetch('/api/generate-description', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            address: document.getElementById('desc_address').value,
                            bedrooms: parseInt(document.getElementById('desc_bedrooms').value),
                            bathrooms: parseFloat(document.getElementById('desc_bathrooms').value),
                            sqft: parseInt(document.getElementById('desc_sqft').value),
                            price: parseInt(document.getElementById('desc_price').value),
                            year_built: parseInt(document.getElementById('desc_year_built').value),
                            features: document.getElementById('desc_features').value.split(',').map(f => f.trim()),
                            neighborhood: document.getElementById('desc_neighborhood').value
                        })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.textContent = data.description;
                        output.classList.add('active');
                    } else {
                        error.textContent = data.detail || 'Error generating description';
                        error.classList.add('active');
                    }
                } catch (err) {
                    error.textContent = 'Error: ' + err.message;
                    error.classList.add('active');
                } finally {
                    loading.classList.remove('active');
                }
            }

            async function generateCMA(e) {
                e.preventDefault();
                const output = document.getElementById('cma_output');
                const loading = document.getElementById('cma_loading');
                const error = document.getElementById('cma_error');

                loading.classList.add('active');
                error.classList.remove('active');
                output.classList.remove('active');

                try {
                    const response = await fetch('/api/generate-cma', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            comparable_sales: JSON.parse(document.getElementById('cma_comparables').value)
                        })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.textContent = data.cma;
                        output.classList.add('active');
                    } else {
                        error.textContent = data.detail || 'Error generating CMA';
                        error.classList.add('active');
                    }
                } catch (err) {
                    error.textContent = 'Error: ' + err.message;
                    error.classList.add('active');
                } finally {
                    loading.classList.remove('active');
                }
            }

            async function generateEmail(e) {
                e.preventDefault();
                const output = document.getElementById('email_output');
                const loading = document.getElementById('email_loading');
                const error = document.getElementById('email_error');

                loading.classList.add('active');
                error.classList.remove('active');
                output.classList.remove('active');

                try {
                    const response = await fetch('/api/generate-email', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            agent_name: document.getElementById('email_agent_name').value,
                            buyer_profile: JSON.parse(document.getElementById('email_buyer_profile').value)
                        })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.textContent = data.email;
                        output.classList.add('active');
                    } else {
                        error.textContent = data.detail || 'Error generating email';
                        error.classList.add('active');
                    }
                } catch (err) {
                    error.textContent = 'Error: ' + err.message;
                    error.classList.add('active');
                } finally {
                    loading.classList.remove('active');
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/generate-description")
async def api_generate_description(request: dict):
    """Generate listing description"""
    description = await generate_description(request)
    return JSONResponse({"description": description})

@app.post("/api/generate-cma")
async def api_generate_cma(request: dict):
    """Generate CMA report"""
    cma = await generate_cma(request.get("comparable_sales", []))
    return JSONResponse({"cma": cma})

@app.post("/api/generate-email")
async def api_generate_email(request: dict):
    """Generate follow-up email"""
    email = await generate_followup_email(
        request.get("agent_name", "Agent"),
        request.get("buyer_profile", {})
    )
    return JSONResponse({"email": email})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
