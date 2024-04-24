import gradio as gr
import requests

market_trend_data = None

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
    global market_trend_data
    url = 'https://manual-jobai-backend-p34gqsegoa-as.a.run.app/trends'
    response = requests.get(url)
    market_trend_data = response.json()['data']

def question_check(message, history):
    message = message.lower()
    if "title:" in message:
        all_formatted_text = "Here are the results for you:\n\n"
        if market_trend_data != None:
            all_formatted_text += "Market Trends:\n\n"
            # all_formatted_text += market_trend_data[0]
            print(f"Market Trends: {market_trend_data[0]}")
        recommendation_res = get_recommendation(message)
        all_formatted_text += recommendation_res
        return all_formatted_text
    else:
        return "Hello! I am Job AI. Please tell me the job title you are looking for, the skills, the categories you are interested in, and your minimum years of experience."

if __name__ == "__main__":
    get_market_trend()
    gr.ChatInterface(
        question_check,
        chatbot=gr.Chatbot(height=700),
        textbox=gr.Textbox(placeholder="Tell me about your career background, please start with `title:` you looking for.", container=False, scale=7),
        title="Job AI",
        description="JobAI help you to look for a job match with your profile and provide market insights to get you prepare for the job",
        theme="soft",
        examples=["Hello", "Am I cool?", "Are tomatoes vegetables?"],
        cache_examples=True,
        retry_btn=None,
        undo_btn="Delete Previous",
        clear_btn="Clear",
    ).launch()