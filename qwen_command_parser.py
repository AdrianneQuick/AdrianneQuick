import ollama

SYSTEM_PROMPT = """
You are a command parser for a Raspberry Pi LED control system.

Valid outputs ONLY:
- on <color>
- off <color>
- mode hardware
- mode manual

Valid colors:
super_red, red, yellow, green, blue

Do not explain. Do not add extra text.
"""

def parse_command(user_text):
    response = ollama.chat(
        model="qwen2.5:0.5b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return response["message"]["content"].strip()

if __name__ == "__main__":
    while True:
        text = input("AI> ")
        cmd = parse_command(text)
        print("Parsed:", cmd)
