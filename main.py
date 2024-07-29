import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = Groq(api_key= "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")
# Define the Request Body schema
class PromptRequest(BaseModel):
    Prompt: str
    Url:str
    
JenaAPi  = "jina_4830ef6354c04fff963452bf5b00eecbzJUBSo5vIwez1unnNzf5_sCFQbnN"

import requests
def scrape_jina_ai(url: str) -> str:
  response = requests.get("https://r.jina.ai/" + url)
  return response.text

def groqResponse(prompt):
  client = Groq(api_key="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")
  chat_completion = client.chat.completions.create(
  messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    model="llama3-8b-8192")
  return (chat_completion.choices[0].message.content)

def chunk_of_text(text):
  result = []
  string_of_text = str(text)
  i = 0
  while i < len(string_of_text):
    chunk = string_of_text[i:i+10000]
    result.append(chunk)
    i += 10000
  return result

def Response(text,prompt):
  result = []
  chunk = chunk_of_text(text)
  for i in chunk:
    result.append(groqResponse(prompt+i))
  clear_response = ""
  for i in result:
    if not 'unable' in i:
      clear_response+=i
  return groqResponse("Given This text and give response according to this prompt "+prompt+clear_response)
    
def extract_urls_and_text(input_string):
    # Define a regular expression pattern to match URLs
    url_pattern = re.compile(r'(https?://\S+)')
    
    # Find the first URL in the input string
    url_match = url_pattern.search(input_string)
    
    if url_match:
        url = url_match.group(0)
        # Remove the URL from the input string to get the remaining text
        text_without_url = url_pattern.sub('', input_string, 1).strip()
    else:
        url = ''
        text_without_url = input_string
    
    return {
        "url": url,
        "text": text_without_url
    }


def QueryResponse(Prompt):
    UrlandPrompt = extract_urls_and_text(Prompt)
    url = UrlandPrompt['url']
    text = UrlandPrompt['text']
    JenaResponse = scrape_jina_ai(url)
    FinalResponse = Response(JenaResponse,Prompt)
    return {"response":FinalResponse}
    
@app.post("/query-response/")
async def query_response(request: PromptRequest):
    try:
        Prompt = request.Prompt
        print(Prompt)
        url = request.Url
        print(url)
        JenaResponse = scrape_jina_ai(url)
        FinalResponse = Response(JenaResponse,Prompt)
        print(FinalResponse)
        return FinalResponse
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
