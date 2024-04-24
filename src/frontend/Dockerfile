FROM python:3.11-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV PORT 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

WORKDIR $APP_HOME
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE $PORT
CMD python chatbot.py