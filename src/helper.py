import fitz #pymupdf
import os
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def extract_text_frokm_pdf(uploaded_file):
    '''
    Extracts text from the PDF file 
    
     ARGS:
        upload_file(str): the path to PDF file.
        
        Returns:
            str : The extracted text.
    '''
    doc = fitz.open(stream = uploaded_file.read(),filetype = "pdf") # Open a PDF from memory (not from disk)
    text = ""

    for page in doc:
        text+= page.get_text()
    return text

def ask_groq(prompt,max_tokens=500):
    """
    Sends prompt to Groq and returns response

    Args:
        prompt (str): user prompt
        max_tokens (int): maximum tokens in response

    Returns:
        str: Groq response
    """
    try:
        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ],

            temperature=0.5,
            max_tokens=max_tokens

        )

        return response.choices[0].message.content

    except Exception as e:
        print(e)