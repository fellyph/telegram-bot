import json

async def on_fetch(request, env):
    # Parse Telegram Event
    try:
        data = await request.json()
    except Exception:
        return {"status": 400, "message": "Invalid JSON mapping"}
    
    if "message" not in data:
        return {"status": 200, "message": "Not a message update"}
        
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    
    if not text:
        return {"status": 200, "message": "No text provided"}

    # Log to D1 (User Message)
    try:
        await env.DB.prepare(
            "INSERT INTO messages (id, chat_id, role, content) VALUES (?1, ?2, ?3, ?4)"
        ).bind(data["message"]["message_id"], chat_id, "user", text).run()
    except Exception as e:
        print(f"Error logging to D1: {e}")

    # Process AI
    prompt = f"Você é um bot assistente de desenvolvedores para tecnologias da Cloudflare. Responda à pergunta: {text}"
    try:
        ai_response = await env.AI.run("@cf/meta/llama-3-8b-instruct", {
            "messages": [{"role": "user", "content": prompt}]
        })
        reply_text = ai_response["response"]
    except Exception as e:
        reply_text = "Desculpe, ocorreu um erro ao gerar a resposta da IA."

    # Return Payload immediately or HTTPX call (for this mock, we return the fetch Response directly if mapped by a caller proxy 
    # but the usual way in CF Workers Python is using native fetch library which might require Pyodide httpx).
    # Since we lack `requests` in Pyodide safely, we use the `fetch` API.
    # To use `fetch` in pyodide, one can use `js.fetch` natively.
    from js import fetch, Object, JSON
    
    telegram_url = f"https://api.telegram.org/bot{env.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": reply_text
    }
    
    post_opts = Object.fromEntries(
        [
            ["method", "POST"],
            ["headers", Object.fromEntries([["Content-Type", "application/json"]])],
            ["body", JSON.stringify(Object.fromEntries(payload.items()))]
        ]
    )
    
    await fetch(telegram_url, post_opts)

    # Log to D1 (Assistant Message)
    import uuid
    try:
        await env.DB.prepare(
            "INSERT INTO messages (id, chat_id, role, content) VALUES (?1, ?2, ?3, ?4)"
        ).bind(str(uuid.uuid4()), chat_id, "assistant", reply_text).run()
    except Exception as e:
        pass

    import js
    return js.Response.new("OK", status=200)
