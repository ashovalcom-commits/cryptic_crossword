import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    # נטען את המפתח ממשתנה הסביבה ANTHROPIC_API_KEY (אף פעם לא לשים מפתח בקוד)
    my_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not my_api_key:
        print("שגיאה: משתנה הסביבה ANTHROPIC_API_KEY לא מוגדר.")
        return

    # הקלדנו את השם ידנית כדי לוודא שאין תווים נסתרים
    target_model = "claude-sonnet-5"
    
    print(f"Testing connection to model: [{target_model}]")
    
    client = anthropic.Anthropic(api_key=my_api_key)
    
    try:
        response = client.messages.create(
            model=target_model,
            max_tokens=20,
            messages=[{"role": "user", "content": "בדיקת חיבור. ענה במילה אחת בלבד: 'מחובר'."}]
        )
        print("Success! Response from Claude:")
        print(response.content[0].text)
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    test_connection()