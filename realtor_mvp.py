#!/usr/bin/env python3
"""
Real Estate Agent AI MVP
Generates beautiful MLS listings descriptions using claude-cli-agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import asyncio
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

# CLI Wrapper Proxy URL (configurable via environment)
CLI_WRAPPER_URL = os.getenv(
    "CLI_WRAPPER_URL",
    "http://localhost:8001/v1/chat/completions"
)

async def call_claude(prompt: str) -> str:
    """Call Claude via CLI wrapper, with fallback to Claude CLI directly"""
    try:
        # Try CLI wrapper proxy first
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                CLI_WRAPPER_URL,
                json={
                    "model": "claude",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
    except:
        pass

    # Fallback to Claude CLI directly
    try:
        result = subprocess.run(
            ["claude", "message", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass

    # If all else fails, return error
    raise Exception("Unable to reach Claude API")

async def generate_description(listing_data: dict) -> str:
    """Generate MLS listing description using Claude"""

    prompt = f"""You are a professional real estate copywriter. Write a compelling MLS listing description.

Property Details:
- Address: {listing_data.get('address', 'N/A')}
- Bedrooms: {listing_data.get('bedrooms', 'N/A')}
- Bathrooms: {listing_data.get('bathrooms', 'N/A')}
- Square Feet: {listing_data.get('sqft', 'N/A')}
- Price: ${listing_data.get('price', 'N/A'):,.0f}
- Year Built: {listing_data.get('year_built', 'N/A')}
- Lot Size: {listing_data.get('lot_size', 'N/A')}
- Features: {listing_data.get('features', 'N/A')}
- Condition: {listing_data.get('condition', 'N/A')}
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


# Routes

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
            .card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                grid-column: 1 / -1;
                font-size: 2.5em;
            }
            h2 {
                color: #667eea;
                margin-bottom: 20px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                color: #333;
                font-weight: 600;
                margin-bottom: 5px;
            }
            input, textarea, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-family: inherit;
                font-size: 14px;
            }
            textarea {
                resize: vertical;
                min-height: 80px;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            .output {
                background: #f5f5f5;
                border-left: 4px solid #667eea;
                padding: 20px;
                border-radius: 6px;
                margin-top: 20px;
                max-height: 400px;
                overflow-y: auto;
                white-space: pre-wrap;
                font-size: 14px;
                line-height: 1.6;
            }
            .loading {
                text-align: center;
                color: #667eea;
                font-weight: 600;
            }
            .error {
                background: #fee;
                color: #c00;
                padding: 15px;
                border-radius: 6px;
                margin-top: 10px;
            }
            .success {
                background: #efe;
                color: #080;
                padding: 15px;
                border-radius: 6px;
                margin-top: 10px;
            }
            @media (max-width: 768px) {
                .container {
                    grid-template-columns: 1fr;
                }
                h1 {
                    font-size: 1.8em;
                }
            }
        </style>
    </head>
    <body>
        <h1>🏠 Realtor AI MVP</h1>

        <div class="container">
            <!-- Listing Description Generator -->
            <div class="card">
                <h2>📝 Listing Description</h2>
                <form onsubmit="generateDescription(event)">
                    <div class="form-group">
                        <label>Address</label>
                        <input type="text" id="address" placeholder="123 Main St, City, State" required>
                    </div>
                    <div class="form-group">
                        <label>Bedrooms</label>
                        <input type="number" id="bedrooms" placeholder="4" required>
                    </div>
                    <div class="form-group">
                        <label>Bathrooms</label>
                        <input type="number" id="bathrooms" placeholder="2" step="0.5" required>
                    </div>
                    <div class="form-group">
                        <label>Square Feet</label>
                        <input type="number" id="sqft" placeholder="2500" required>
                    </div>
                    <div class="form-group">
                        <label>Price</label>
                        <input type="number" id="price" placeholder="500000" required>
                    </div>
                    <div class="form-group">
                        <label>Year Built</label>
                        <input type="number" id="year_built" placeholder="2020" required>
                    </div>
                    <div class="form-group">
                        <label>Features (comma separated)</label>
                        <textarea id="features" placeholder="Pool, Hardwood floors, Updated kitchen">Updated kitchen, Granite counters, Pool</textarea>
                    </div>
                    <div class="form-group">
                        <label>Neighborhood</label>
                        <input type="text" id="neighborhood" placeholder="Quiet suburban area" required>
                    </div>
                    <button type="submit">Generate Description ✨</button>
                </form>
                <div id="description-output"></div>
            </div>

            <!-- CMA Generator -->
            <div class="card">
                <h2>📊 CMA Report</h2>
                <div class="form-group">
                    <label>Add Comparable Sales (one per line)</label>
                    <textarea id="comparables" placeholder="123 Oak St: $500k, 2500 sqft, 4 bed, 2 bath
456 Pine Ave: $485k, 2400 sqft, 3 bed, 2 bath
789 Elm Rd: $510k, 2600 sqft, 4 bed, 3 bath">123 Oak St: $500k, 2500 sqft, 4 bed, 2 bath
456 Pine Ave: $485k, 2400 sqft, 3 bed, 2 bath
789 Elm Rd: $510k, 2600 sqft, 4 bed, 3 bath</textarea>
                </div>
                <button onclick="generateCMA()">Generate CMA Report 📈</button>
                <div id="cma-output"></div>
            </div>

            <!-- Follow-up Email Generator -->
            <div class="card">
                <h2>📧 Follow-up Email</h2>
                <form onsubmit="generateEmail(event)">
                    <div class="form-group">
                        <label>Agent Name</label>
                        <input type="text" id="agent_name" placeholder="Your Name" required>
                    </div>
                    <div class="form-group">
                        <label>Buyer Interests</label>
                        <input type="text" id="interests" placeholder="Modern homes, Pool, Near schools" required>
                    </div>
                    <div class="form-group">
                        <label>Budget</label>
                        <input type="number" id="budget" placeholder="500000" required>
                    </div>
                    <div class="form-group">
                        <label>Timeline</label>
                        <select id="timeline" required>
                            <option value="">Select timeline</option>
                            <option value="This month">This month</option>
                            <option value="Next 3 months">Next 3 months</option>
                            <option value="6+ months">6+ months</option>
                        </select>
                    </div>
                    <button type="submit">Generate Email 💌</button>
                </form>
                <div id="email-output"></div>
            </div>

            <!-- Stats -->
            <div class="card">
                <h2>📈 Time Saved</h2>
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 2em; color: #667eea; font-weight: bold;">
                        <span id="time-saved">0</span> hours
                    </div>
                    <p style="color: #666; margin-top: 10px;">Estimated time saved</p>
                    <div style="margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 6px;">
                        <p style="font-size: 12px; color: #666;">
                            Each listing: 20 min → 1 min<br>
                            Each CMA: 30 min → 2 min<br>
                            Each email: 10 min → 1 min
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function generateDescription(e) {
                e.preventDefault();
                const output = document.getElementById('description-output');
                output.innerHTML = '<div class="loading">✨ Generating listing description...</div>';

                try {
                    const response = await fetch('/api/generate-description', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            address: document.getElementById('address').value,
                            bedrooms: parseInt(document.getElementById('bedrooms').value),
                            bathrooms: parseFloat(document.getElementById('bathrooms').value),
                            sqft: parseInt(document.getElementById('sqft').value),
                            price: parseInt(document.getElementById('price').value),
                            year_built: parseInt(document.getElementById('year_built').value),
                            features: document.getElementById('features').value,
                            neighborhood: document.getElementById('neighborhood').value
                        })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.innerHTML = '<div class="success">✅ Generated!</div><div class="output">' + data.description + '</div>';
                        updateTimeSaved();
                    } else {
                        output.innerHTML = '<div class="error">❌ Error: ' + data.detail + '</div>';
                    }
                } catch (err) {
                    output.innerHTML = '<div class="error">❌ Error: ' + err.message + '</div>';
                }
            }

            async function generateCMA() {
                const output = document.getElementById('cma-output');
                output.innerHTML = '<div class="loading">📊 Generating CMA report...</div>';

                try {
                    const comparablesText = document.getElementById('comparables').value;
                    const comps = comparablesText.split('\\n').filter(c => c.trim()).map(c => {
                        const parts = c.split(':');
                        const details = parts[1].split(',');
                        return {
                            address: parts[0].trim(),
                            price: parseInt(details[0].replace('$', '').replace('k', '000')),
                            sqft: parseInt(details[1]),
                            beds: parseInt(details[2]),
                            baths: parseFloat(details[3])
                        };
                    });

                    const response = await fetch('/api/generate-cma', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ comparable_sales: comps })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.innerHTML = '<div class="success">✅ Generated!</div><div class="output">' + data.cma + '</div>';
                        updateTimeSaved();
                    } else {
                        output.innerHTML = '<div class="error">❌ Error: ' + data.detail + '</div>';
                    }
                } catch (err) {
                    output.innerHTML = '<div class="error">❌ Error: ' + err.message + '</div>';
                }
            }

            async function generateEmail(e) {
                e.preventDefault();
                const output = document.getElementById('email-output');
                output.innerHTML = '<div class="loading">💌 Generating email...</div>';

                try {
                    const response = await fetch('/api/generate-email', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            agent_name: document.getElementById('agent_name').value,
                            buyer_profile: {
                                interests: document.getElementById('interests').value,
                                budget: parseInt(document.getElementById('budget').value),
                                timeline: document.getElementById('timeline').value
                            }
                        })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        output.innerHTML = '<div class="success">✅ Generated!</div><div class="output">' + data.email + '</div>';
                        updateTimeSaved();
                    } else {
                        output.innerHTML = '<div class="error">❌ Error: ' + data.detail + '</div>';
                    }
                } catch (err) {
                    output.innerHTML = '<div class="error">❌ Error: ' + err.message + '</div>';
                }
            }

            function updateTimeSaved() {
                const generates = document.querySelectorAll('.output').length;
                const hours = (generates * 0.45).toFixed(1); // ~27 min per generation
                document.getElementById('time-saved').textContent = hours;
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/generate-description")
async def api_generate_description(request: dict):
    """API endpoint for generating listing descriptions"""
    description = await generate_description(request)
    return JSONResponse({"description": description})

@app.post("/api/generate-cma")
async def api_generate_cma(request: dict):
    """API endpoint for generating CMA reports"""
    cma = await generate_cma(request.get("comparable_sales", []))
    return JSONResponse({"cma": cma})

@app.post("/api/generate-email")
async def api_generate_email(request: dict):
    """API endpoint for generating follow-up emails"""
    email = await generate_followup_email(
        request.get("agent_name", "Agent"),
        request.get("buyer_profile", {})
    )
    return JSONResponse({"email": email})

if __name__ == "__main__":
    import uvicorn
    print("""

    🏠 REALTOR AI MVP - STARTING
    ================================

    ✅ Features:
       - MLS Listing Descriptions
       - CMA Reports
       - Follow-up Emails

    📍 Running on: http://localhost:8080

    Make sure these are running:
       - CLI Wrapper Proxy (8001) ✅
       - Backend API (8000) ✅

    """)
    uvicorn.run(app, host="0.0.0.0", port=8080)
