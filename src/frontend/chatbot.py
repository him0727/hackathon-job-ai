import gradio as gr
import requests

def get_recommendation(message):
    url = 'https://manual-jobai-backend-p34gqsegoa-as.a.run.app/recommendations?topk=6'
    headers = {'Content-Type': 'text/plain'}
    response = requests.post(url, headers=headers, data=message)
    data = response.json()['data']
    formatted_job_rec_text = ""
    for i, job in enumerate(data, start=1):
        formatted_job_rec_text += f"{i}.\nTitle: **{job['title']}**\nCompany: **{job['company']}**\nURL: {job['url']}\n\n"
    return formatted_job_rec_text

def get_market_trend():
    url = 'https://manual-jobai-backend-p34gqsegoa-as.a.run.app/market_trend'
    response = requests.get(url)
    data = response.json()['data']
    formatted_market_trend_text = ""
    for i, trend in enumerate(data, start=1):
        formatted_market_trend_text += f"{i}.\nTitle: **{trend['title']}**\nCompany: **{trend['company']}**\nURL: {trend['url']}\n\n"
    return formatted_market_trend_text

def question_check(message, history):
    message = message.lower()
    if "title:" in message:
        all_formatted_text = "Here are the results for you:\n\n"
        recommendation_res = get_recommendation(message)
        all_formatted_text += recommendation_res
        return all_formatted_text
    else:
        return "Hello! I am Job AI. Please tell me the job title you are looking for, the skills, the categories you are interested in, and your minimum years of experience."

if __name__ == "__main__":
    gr.ChatInterface(
        question_check,
        chatbot=gr.Chatbot(height=300),
        textbox=gr.Textbox(placeholder="Ask me a yes or no question", container=False, scale=7),
        title="Job AI",
        description="Ask Yes Man any question",
        theme="soft",
        examples=["Hello", "Am I cool?", "Are tomatoes vegetables?"],
        cache_examples=True,
        retry_btn=None,
        undo_btn="Delete Previous",
        clear_btn="Clear",
    ).launch()