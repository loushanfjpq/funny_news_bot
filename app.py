import os
import time
import requests
from flask import Flask, request, render_template
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        article = ' '.join(p.get_text() for p in paragraphs if len(p.get_text()) > 40)
        return article.strip()[:3000]
    except Exception as e:
        return f"Error extracting text: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            start_time = time.time()

            input_text = request.form.get("news", "")
            input_url = request.form.get("url", "")

            if input_url:
                news = extract_text_from_url(input_url)
                if news.startswith("Error"):
                    return f"<h2>⚠️ {news}</h2>"
            else:
                news = input_text

            total_input_tokens = 0
            total_output_tokens = 0

            summary_en_prompt = f"Summarize this news in 3 short sentences:\n\n{news}"
            summary_en_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": summary_en_prompt}]
            )
            summary_en = summary_en_response.choices[0].message.content.strip()
            usage = summary_en_response.usage
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

            summary_zh_prompt = f"请用三句中文总结这则新闻：\n\n{news}"
            summary_zh_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": summary_zh_prompt}]
            )
            summary_zh = summary_zh_response.choices[0].message.content.strip()
            usage = summary_zh_response.usage
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

            funny_prompt_en = (
                f"The following is a news summary:\n'{summary_en}'\n\n"
                f"Write a funny, sarcastic viral-style comment under 25 words as if posting on Twitter."
            )
            comment_en_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": funny_prompt_en}]
            )
            comment_en = comment_en_response.choices[0].message.content.strip()
            usage = comment_en_response.usage
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

            funny_prompt_zh = (
                f"这是新闻的中文摘要:\n'{summary_zh}'\n\n"
                f"请用调侃或发人深省的方式写一句适合发朋友圈或微博的中文评论。"
            )
            comment_zh_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": funny_prompt_zh}]
            )
            comment_zh = comment_zh_response.choices[0].message.content.strip()
            usage = comment_zh_response.usage
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

            image_prompt_request = f"Write a surreal, creative image prompt for DALL·E based on this comment: '{summary_en}'. Do not include any text in the image."
            image_prompt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": image_prompt_request}]
            )
            image_prompt = image_prompt_response.choices[0].message.content.strip()
            usage = image_prompt_response.usage
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

            image_response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = image_response.data[0].url

            elapsed_time = round(time.time() - start_time, 2)

            gpt_input_cost = total_input_tokens / 1000 * 0.01
            gpt_output_cost = total_output_tokens / 1000 * 0.03
            dalle_cost = 0.04
            total_cost = round(gpt_input_cost + gpt_output_cost + dalle_cost, 4)

            return render_template(
                "index.html",
                input_text=news,
                summary_en=summary_en,
                summary_zh=summary_zh,
                comment_en=comment_en,
                comment_zh=comment_zh,
                image_url=image_url,
                elapsed_time=elapsed_time,
                total_cost=total_cost
            )

        except Exception as e:
            return f"<h2>⚠️ Error occurred:</h2><pre>{str(e)}</pre>"

    return render_template("index.html")
