from litellm import completion 

tools = [{"googleSearch": {}}] # 👈 ADD GOOGLE SEARCH

resp = completion(
    model="vertex_ai/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Who won the world cup?"}],
    tools=tools,
)

print(resp)