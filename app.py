import os
import requests
import time
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
            input_text = request.form.get("news", "")
            input_url = request.form.get("url", "")
            start_time = time.time()

            if input_url:
                news = extract_text_from_url(input_url)
                if news.startswith("Error"):
                    return f"<h2>⚠️ {news}</h2>"
            else:
                news = input_text

            # Summarize in English
            summary_prompt_en = f"Summarize this news in 3 short sentences:\n\n{news}"
            summary_en_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt_en}]
            )
            summary_en = summary_en_response.choices[0].message.content.strip()

            # Summarize in Chinese
            summary_prompt_zh = f"请用三句中文总结这则新闻：\n\n{news}"
            summary_zh_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt_zh}]
            )
            summary_zh = summary_zh_response.choices[0].message.content.strip()

            # Funny comment in English
            funny_prompt_en = (
                f"The following is a one-sentence summary of a news story:\n"
                f"'{summary_en}'\n\n"
                f"Act like a witty internet personality with knowledge of recent memes, pop culture, and sarcastic humor. "
                f"Write a short, hilarious comment (under 25 words) about this news as if posting it on Reddit or Twitter."
            )
            funny_comment_en = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": funny_prompt_en}]
            ).choices[0].message.content.strip()

            # Funny comment in Chinese
            funny_prompt_zh = (
                f"这是文章的总结:\n"
                f"'{summary_zh}'\n\n"
                f"请用调侃幽默或富有哲理的话语，写一句微博或微信风格的评论。"
            )
            funny_comment_zh = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": funny_prompt_zh}]
            ).choices[0].message.content.strip()

            elapsed_time = round(time.time() - start_time, 2)
            total_cost = round(4 * len(news) / 1000 * 0.0015, 4)  # 4 rounds, $0.0015/1k tokens

            return render_template(
                "index.html",
                input_text=news,
                summary_en=summary_en,
                summary_zh=summary_zh,
                comment_en=funny_comment_en,
                comment_zh=funny_comment_zh,
                image_url=None,
                elapsed_time=elapsed_time,
                total_cost=total_cost
            )

        except Exception as e:
            return f"<h2>⚠️ An error occurred:</h2><pre>{str(e)}</pre>"

    return render_template("index.html")
