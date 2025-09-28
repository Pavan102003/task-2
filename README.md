Serverless News Summarizer API (Challenge 2)

This project creates a scalable, on-demand REST API using AWS Lambda and API Gateway that summarizes any news article URL using an external NLP model.

Public Service URL : https://312hnv8mfb.execute-api.us-east-1.amazonaws.com/prod/summarize

Test Command : curl -X POST "https://312hnv8mfb.execute-api.us-east-1.amazonaws.com/prod/summarize" -H "Content-Type: application/json" -d "{\"url\": \"https://www.gutenberg.org/files/2701/2701-h/2701-h.htm\"}"

Live Demo : 


Serverless Stack : AWS Lambda, Amazon API Gateway, AWS DynamoDB (for caching).

AI Tooling : NLP Cloud (BART-Large-CNN model).

Bonus Feature : Caching: Results for repeated URLs are stored and retrieved from the DynamoDB table, marked by "cached": true.


#Project Gutenberg (PG) URLs contain static, plain HTML files of books and documents. 


#Short Reflection on the Project
I learned that building robust cloud solutions often involves battling external dependencies more than internal code logic. The trickiest part was successfully configuring the communication between the Python Lambda runtime, the strict NLP Cloud API limits, and reliable web scraping heuristics, requiring several rounds of deployment to find the correct, safe input size. This process reinforced the importance of IAM granularity and error logging in serverless development.



#AI Tooling Configuration and Usage

AI tooling was used in two key aspects of this project:

1. Core Service Tooling (NLP Summarization)
Tool: NLP Cloud (BART-Large-CNN Model)

Usage: This model serves as the core intelligence, performing abstractive text summarization (condensing the article text).

Configuration: 
The secure API Token was configured via a deployment parameter override (--parameter-overrides NLP_API_KEY='...') and stored as an environment variable in the Lambda function. The Lambda handles the API's specific requirements (e.g., sending raw text, using the Authorization: Token header, and limiting the payload size to avoid 413 errors).

2. Development Tooling (Code Generation/Debugging)
Tool: AI Assistants (e.g., Google's Gemini, GitHub Copilot)

Usage: 
Used to quickly generate boilerplate code, specifically for the DynamoDB Caching logic (boto3 functions for put_item and get_item) and complex commands like the robust HTML scraping heuristics in extract_main_text.

Result: 
This accelerated development by allowing focus to remain on infrastructure deployment and API integration, rather than manual SDK syntax construction.





#FINAL RESULT LOOKS LIKE

Example Successful Output (Cache Miss):

JSON

{
  "url": "https://www.freecodecamp.org/news/what-is-serverless-architecture-and-why-is-it-important/",
  "summary": "...", 
  "cached": false  <-- Confirms it called the external API
}

Example Successful Output (Cache Hit - Bonus Challenge):

JSON

{
  "url": "https://www.freecodecamp.org/news/what-is-serverless-architecture-and-why-is-it-important/",
  "summary": "...", 
  "cached": true   <-- Confirms the cache was used  # including the bonus challenge  DynamoDB Table
}


# Results looks like in Command Prompt

C:\Users\pavan\OneDrive\Desktop\Task 2>curl -X POST "https://312hnv8mfb.execute-api.us-east-1.amazonaws.com/prod/summarize" -H "Content-Type: application/json" -d "{\"url\": \"https://www.gutenberg.org/files/2701/2701-h/2701-h.htm\"}"
{"url": "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm", "summary": "This text is a combination of etexts, one from the now-defunct ERIS project at Virginia Tech and one from Project Gutenberg\u2019s archives. The resulting etext was compared with a public domain hard copy version of the text. \u201cA whale-fish is to be called in our tongue, leaving out, through ignorance, the letter H, which almost alone maketh up the signification of the word.\u201d \u2014Hackluyt.", "cached": false}



C:\Users\pavan\OneDrive\Desktop\Task 2>curl -X POST "https://312hnv8mfb.execute-api.us-east-1.amazonaws.com/prod/summarize" -H "Content-Type: application/json" -d "{\"url\": \"https://www.gutenberg.org/files/2701/2701-h/2701-h.htm\"}"
{"url": "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm", "summary": "This text is a combination of etexts, one from the now-defunct ERIS project at Virginia Tech and one from Project Gutenberg\u2019s archives. The resulting etext was compared with a public domain hard copy version of the text. \u201cA whale-fish is to be called in our tongue, leaving out, through ignorance, the letter H, which almost alone maketh up the signification of the word.\u201d \u2014Hackluyt.", "cached": false}

