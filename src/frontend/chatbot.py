import requests
import gradio as gr

HELP_MSG = """
<table style="width:100%">
  <tr>
    <th>Command</th>
    <th>Usage</th>
    <th>Response</th>
  </tr>
  <tr>
    <td>/match {ANY_TEXT}</td>
    <td>{ANY_TEXT} is a text that describes your background, like academic background, work experience, skills, what are you looking for, expected salary, etc.</td>
    <td>Return top 6 jobs that best matches your background and some market trends for those jobs' industry.</td>
  </tr>
  <tr>
    <td>/ask {JOB_URL}</td>
    <td>{JOB_URL} is the job link retrieved from /match. Just pick your interested job's link.</td>
    <td>Return 5 potential interview questions with hints for the answers for that role that covers its company values and job requirements.</td>
  </tr>
  <tr>
    <td>/help</td>
    <td>No extra argument.</td>
    <td>Help menu.</td>
  </tr>
</table>
"""

WELCOME_MSG = f"""
<strong>Welcome to Job AI!</strong>
<i>Our cutting-edge solution harnesses the immense power of Large Language and Machine Learning models to revolutionize the job-seeking experience.</i><br>
<strong>Data-Driven Insights</strong> + <strong>Tailored Recommendations</strong> + <strong>Guided Journey</strong>
<br><br>
Get started:
{HELP_MSG}
"""

BACKEND_HOST = "https://jobai-backend-p34gqsegoa-as.a.run.app"
MARKET_TREND_DATA = {}


def get_recommendation(message):
    url = f"{BACKEND_HOST}/recommendations?topk=6"
    headers = {"Content-Type": "text/plain"}
    response = requests.post(url, headers=headers, data=message)
    data = response.json()["data"]
    return data


def generate_question(message):
    url = f"{BACKEND_HOST}/questions_answers/{message}"
    return requests.get(url).content.decode("utf-8")


def get_market_trend():
    global MARKET_TREND_DATA
    url = f"{BACKEND_HOST}/trends"
    response = requests.get(url)
    for data in response.json()["data"]:
        MARKET_TREND_DATA[data["category"]] = data["summary"]


def msg_handler(message, history):
    message = message.strip()
    if message.lower().startswith("/match"):
        resp = "Here are some recommended jobs for you:<br>"
        recommendations = get_recommendation(message[6:])
        unique_categories = set()
        resp += "<ul style=\"text-indent:-20px; margin-left:20px\">"
        for i, job in enumerate(recommendations):
            resp += (
              f"<li><span><i>Title:</i><b> {job['title']}</b><br>"
              f"<i>Company:</i><b> {job['company']}</b><br>"
              f"<i>Category:</i> {', '.join(job['categories'])}<br>"
              f"<i>Link:</i> {job['url']}</span></li>"
            )
            for category in job["categories"]:
                unique_categories.add("Food and Beverage" if category == "F&B" else category)
        resp += "</ul><br>"
        resp += "Market trends and skills for those industries:<br>"
        for category in unique_categories:
            resp += f"<strong>{category}</strong>"
            if category in MARKET_TREND_DATA:
                resp += f"<ul style=\"text-indent:-20px; margin-left:20px\">"
                resp += "".join([f"<li>{x}</li>" for x in MARKET_TREND_DATA[category]["trends"]])
                resp += f"<li>Top common skills include {', '.join(MARKET_TREND_DATA[category]['skills'])}</li></ul>"
            else:
                resp += "<br>- N/A<br>"
        return resp
    elif message.lower().startswith("/ask"):
        resp = "Here are some potential interview questions for the role:<br><br>"
        resp += generate_question(message.split('-')[-1])
        return resp
    elif message.lower() == "/help":
        return HELP_MSG
    return "Sorry I don't understand your instructions. You may type */help* to find the correct command."


gr.ChatInterface(
    msg_handler,
    chatbot=gr.Chatbot(height=650, placeholder=WELCOME_MSG, value=get_market_trend, container=False),
    textbox=gr.Textbox(placeholder="Tell me your background? Type /help for more information.", container=False, scale=7),
    title="Job AI",
    description="Your ultimate ally in the job market in Singapore. Join the future of job hunting with us. Your success story starts here.",
    theme=gr.themes.Soft(),
    retry_btn=None,
    undo_btn=None,
    clear_btn="Clear Conversation"
).launch()
