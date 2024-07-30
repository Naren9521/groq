apiToken = "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"
import requests
from bs4 import BeautifulSoup
from minify_html import minify
from urllib.parse import urljoin
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    Prompt: str
    Url:str
    
chunkPrompt = """You are a webScraper you are given with one chunk of html code of a website and the user will give you a prompt,
you need to understand the prompt and analyse that part of the chunk. If any of the part in chunk fulfills the chunk you need to give response according to it.
If the chunk doesnt have any information about the prompt in that chunk you can resonse with nothing found.
"""
mergePrompt = "You are a webScraper earlier you have scraped multiple chunks of a website and given me multiple responses for each chunk with the same prompt, now your task is to analyse all the responses given by you earlier for each chunk and give me a one final response in which all the information is present that user asked for, Here is the prompt and the responses you gave earlier"
def getGroqResponse(api_key, prompt, model="llama3-8b-8192"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model
    }

    response = requests.post(url, headers=headers, json=data)
    try:
        return response.json()['choices'][0]['message']['content']
    except:
        return "Error occured while fetching groqresponse"

def cleanup_html(html_content: str, base_url: str) -> str:
    """
    Processes HTML content by removing unnecessary tags, minifying the HTML, and extracting the title and body content.

    Args:
        html_content (str): The HTML content to be processed.

    Returns:
        str: A string combining the parsed title and the minified body content. If no body content is found, it indicates so.

    Example:
        >>> html_content = "<html><head><title>Example</title></head><body><p>Hello World!</p></body></html>"
        >>> remover(html_content)
        'Title: Example, Body: <body><p>Hello World!</p></body>'

    This function is particularly useful for preparing HTML content for environments where bandwidth usage needs to be minimized.
    """

    soup = BeautifulSoup(html_content, 'html.parser')

    # Title Extraction
    title_tag = soup.find('title')
    title = title_tag.get_text() if title_tag else ""

    # Script and Style Tag Removal
    for tag in soup.find_all(['script', 'style']):
        tag.extract()

    # Links extraction
    link_urls = [urljoin(base_url, link['href']) for link in soup.find_all('a', href=True)]

    # Images extraction
    images = soup.find_all('img')
    image_urls = []
    for image in images:
        if 'src' in image.attrs:
            # if http or https is not present in the image url, join it with the base url
            if 'http' not in image['src']:
                image_urls.append(urljoin(base_url, image['src']))
            else:
                image_urls.append(image['src'])

    # Body Extraction (if it exists)
    body_content = soup.find('body')
    if body_content:
        # Minify the HTML within the body tag
        minimized_body = minify(str(body_content))
        return title, minimized_body, link_urls, image_urls

    else:
        raise ValueError(f"No HTML body content found, please try setting the 'headless' flag to False in the graph configuration. HTML content: {html_content}")
    
def getHtmlContent(url):
    try:
      headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
      response = requests.get(url, headers=headers)
      response.raise_for_status()
    except requests.exceptions.RequestException as e:
      print(f"Error fetching {url}: {e}")
      return ""
    soup = BeautifulSoup(response.text, 'html.parser')
    print("Actual length of html was",len(str(soup)))
    return soup

def chunk_of_text(text):
  result = []
  string_of_text = str(text)
  i = 0
  while i < len(string_of_text):
    chunk = string_of_text[i:i+10000]
    result.append(chunk)
    i += 10000
  return result

def combineResponse(all_chunks,promptActual):
    prompt = chunkPrompt + "Prompt:-" + promptActual +" website chunk :- "
    combinedResponse = ""
    for i in all_chunks:
        tempResponse = getGroqResponse(apiToken,prompt+i)
        combinedResponse += tempResponse
    mergeP = mergePrompt + "Prompt"+promptActual+"Earlier responses :-"+combinedResponse
    finalResponse = getGroqResponse(apiToken,mergeP)
    return finalResponse

@app.post("/query-response/")
async def query_response(request: PromptRequest):
    try:
        url = request.Url
        html = getHtmlContent(url)
        cleaned_html = cleanup_html(str(html),url)
        chunks = chunk_of_text(cleaned_html)
        responsebyGroq = combineResponse(chunks,request.Prompt)
        return responsebyGroq
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
