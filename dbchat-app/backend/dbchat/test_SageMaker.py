


def input_fn(runtime, user_question = 'how many customers do we have?', table_metadata_string_DDL_statements = 'create table customers (id int, first_name text, last_name text)'):
    prompt = f'''
    ### Task
    Generate a SQL query to answer [QUESTION]{user_question}[/QUESTION]
    -- Make sure to use aliases for all columns extracted
    --- If you do not know how to answer the question only answer with 'I cannot answer the question. Please try again.'

    ### Database Schema
    The query will run on a database with the following schema:
    {table_metadata_string_DDL_statements}

    ### Answer
    [SQL]
    '''
    # Invoke the endpoint using the `invoke_endpoint` method of the SageMaker runtime client object
    response = runtime.invoke_endpoint(EndpointName='huggingface-pytorch-tgi-inference-2024-03-26-18-38-12-716',
                                   ContentType='application/json',
                                   Body=json.dumps({'inputs':prompt}))
    # result = predictor.predict({"inputs":prompt})[0]['generated_text']
    # sql_query = result.split('[SQL]')[1].replace('\n','').strip()

    # Parse the output data returned by the endpoint
    output_data = json.loads(response['Body'].read().decode())[0]['generated_text']
    sql_query = output_data.split('\n')[-1].strip()
    return sql_query
    


# Prepare your input data in the appropriate format for your model
input_data = {'inputs': "how many customers do we have?"}


x = input_fn(runtime)
print(x)

