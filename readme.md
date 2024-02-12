# Query Explainer
Shows a query, its results, and the purpose of each statement in it given a database and a prompt.
## Setup
Create a file called keys.json in the same directory as query-explainer.py. It should have the form
``` json
{"gemini":
    {
        "api-key": "your_api_key"
    }
}
```
## Run
 To run, use <em> python query-explainer.py</em> and follow the commands. The database used must either be hosted locally or on github.