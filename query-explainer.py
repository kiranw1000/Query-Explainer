
# Setup 

import google.generativeai as gai
import json, requests, os
# Gemini API Key import
gemini_key = json.load(open('keys.json'))['gemini']['api-key']
gai.configure(api_key=gemini_key)
MODEL = gai.GenerativeModel('gemini-pro')
import sqlite3 as sql

# Define helper functions

def is_sql(line:str):
    first_word = line.strip().split(" ")[0]
    return first_word == first_word.upper()

def reformat_response(resp):
    return "\n".join([line for line in resp.text.split('\n') if line.split()[0]==line.split()[0].upper() and line!="\n" and "`" not in line])

def get_sql_from_llm(assignment,model):
    chat = model.start_chat(history=[])
    return chat.send_message(f'You have a database with the following tables: {tables}. Those tables have the following columns: {table_columns}. Using as many new lines as is reasonable, generate a sql query such that it satisfies the following: '+assignment+ ". Do not explain and give no other text and put each sql command on a new line. If such a query does not make sense in the context of the database or if any requested columns do not exist return the phrase 'Invalid prompt'."), chat

def execute_query(query:str, cur):
    try:
        return cur.execute(query).fetchall()
    except:
        return "Invalid prompt"

def get_instructions(assignment, model, cur):
    response, chat = get_sql_from_llm(assignment,model)
    if "\n" not in response.text:
        response = chat.send_message("Please put each query command on a new line.")
    # Check if the prompt is valid
    if "Invalid prompt" in response.text or not any([is_sql(line) for line in response.text.split('\n')]):
        return ["None"],["Please enter a question that makes sense in the context of the database."], chat
    instructions = []
    query = "\n".join([line for line in reformat_response(response).split('\n') if is_sql(line)])
    invalid, try_count = True,0
    while invalid and try_count<5:
        results = execute_query(query, cur)
        # Check if the generated query is valid
        if results == "Invalid prompt":
            print(f"Generated query {try_count+1} did not make sense in the context of the database. Trying new query.")
            response, chat = get_sql_from_llm(assignment,model)
            query = "\n".join([line for line in reformat_response(response).split('\n') if is_sql(line)])
        else:
            invalid = False
        try_count+=1
    if invalid:
        # Return an error message if no valid query could be generated
        return ["None"],["A valid query could not be generated. Please try again."], chat
    if len(results)<1:
        # Return an error message if the query did not return any results
        return ["None"],["The generated query did not return any results. Please enter a valid prompt."], chat
    for query_line in query.split('\n'):
        if is_sql(query_line):
            instructions+= [query_line+" ["+chat.send_message("Explain what the command "+query_line+"is doing in one sentence on one line without any formatting. Be specific about any tables, columns, or values that are used.").text.split("\n")[0]+"]"]
    return results, instructions, chat

def show_instructions_and_results(instructions, results):
    # Display results of the query
    ret = "Results: \n"
    for r, result in enumerate(results):
        ret+=f"{result.__str__()}\n"
    # Display instructions for the query
    ret += f"Instructions: \n"
    for i, instruction in enumerate(instructions):
        ret+=f"{instruction}\n"
    return ret

# Run
if __name__ == "__main__":
    database_uri = input("Enter the path to the database: ").replace("blob", "raw")

    # Download the database file
    response = requests.get(database_uri).content if 'http' in database_uri else open(database_uri, "rb").read()
    with open("temp.db", "wb") as file:
        file.write(response)
    # Connect to the database
    conn = sql.connect("temp.db")
    cur = conn.cursor()
    # Create a list of all the tables in the database
    tables = [table_tuple[0] for table_tuple in cur.execute("SELECT name FROM sqlite_master  WHERE type='table';").fetchall()]
    # Create a dictionary of all the columns in each table in the database
    table_columns = {}
    for table in tables:
        table_columns[table] = [column[0] for column in cur.execute(f"SELECT * FROM {table}").description]
    prompt = input("Enter the prompt: ")
    while prompt != "q":
        results,instructions,chat = get_instructions(prompt, MODEL, cur)
        print(show_instructions_and_results(instructions, results))
        prompt = input("Enter the prompt: ")
    print("Goodbye!")
    os.remove("temp.db")




