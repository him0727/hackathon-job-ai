const PORT = 8000
const express = require('express')
const cors = require('cors')
require('dotenv').config()
const app = express()
app.use(express.json())
app.use(cors())

const API_KEY = process.env.API_KEY

app.post('/completions', async (req, res) => {
    const options = {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: "gpt-4-turbo",
            messages: [
                {
                    role: "system",
                    content: "The user is a DevOps Engineer with 5 years of experience in Google Cloud, located in Singapore, Give a market insight of the user input of the job, and recommend 2 jobs in singapore to the user based on the profile."
                },
                {
                    role: "user",
                    content: req.body.message
                }
            ],
            max_tokens: 1500,
            temperature: 0.5,
            top_p: 1.0,
            frequency_penalty: 0.0,
            presence_penalty: 0.0
        })
    }
    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', options)
        const data = await response.json()
        res.send(data)
    } catch(error) {
        console.error(error)
    }
})

console.log('hi')
app.listen(PORT, () => console.log('Your server is running on PORT' + PORT))