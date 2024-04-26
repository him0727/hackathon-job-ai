# Job AI
Revolutionizing Job Search in the APAC Region, save time and effort for optimal job matching that fulfills both employer and employee objectives

Link: https://jobai-frontend-p34gqsegoa-as.a.run.app/

## Features
AI-driven platform to match job seekers with ideal job opportunities based on their profiles and interests. Provides valuable insights into market trends and required skills for specific roles.
- **Market trend analysis and skillset demands**: Show the market trends and most in-demand skills for 43 industries
- **AI-powered job recommendations**: Input your background and goal in any text format to get tailored job rcommendations
- **Customized potential interview questions**: Generate potential interview questions with hints for the answers for your interested role's company values, background and role requirements

## Demo
![Breif Architecture](/docs/demo.gif)

## Architecture
Job AI is a serverless and cloud native solution hosted on Google Cloud Platform (GCP). It harnesses the immense power of Generative AI to revolutionize the job-seeking and interview preparation experience. All raw, preprocessed and refeined data is stored in BigQuery.
![Breif Architecture](/docs/architecture.png)

#### Trend Analysis
- Get embedding results for each industry category from Cloud Storage (export from BigQuery)
- Use K-means clustering to divide all jobs into K clusters
- Find the closest job to the centroid for each cluster and sort them ascendingly
- Use map-reduce technique to aggregate the summary results for those jobs retrieved from Large Language Model (Google PaLM 2 for Text) by prompt engineering

#### Recommendations
- Get embedding result for user's input by Natural Language Processing (Google Text Embedding Model)
- Perform vector search on BigQuery pre-generated job embeddings table
- Find the top K records with shortest distance to user's input embedding

#### Interview Questions Generation
- Retrieve the requested job from BigQuery
- Get interview questions and hints for the answers generated from Large Language Model (Google PaLM 2 for Text) by prompt engineering