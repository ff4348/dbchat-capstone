from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import time
import os
from google.cloud import storage
import psutil
import re
# !pip install trl accelerate bitsandbytes peft datasets -qU

# To get to memory and cpu information
split_bar = '='*20
memory_info = psutil.virtual_memory()._asdict()
print(f"{split_bar} Memory Usage {split_bar}")
for k,v in memory_info.items():
  print(k, v)
print(f"{split_bar} CPU Usage {split_bar}")
print(f"CPU percent: {psutil.cpu_percent()}%")

# load model and tokenizer (may fail due to OOM errors depending on RAM available - Doesn't run with free GPU on colab)
# Get the current working directory
current_dir = os.getcwd()
# Move two directories back
data_path = os.path.join(current_dir, '..', '..')
# Normalize the path to resolve any '..'
data_path = os.path.normpath(data_path)
data_path = data_path + '/mistral7b_ft_hypm5_10e_dbchat'
print('data path:',data_path)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'dbchatcapstone-key.json'

# Instantiates a client
storage_client = storage.Client()
print("client instantiated")

print('starting model download...')
start_time = time.time()
print(start_time)
llm = AutoModelForCausalLM.from_pretrained(data_path, device_map='auto', offload_folder='/model_offload')
end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
print('starting tokenizer download...')
tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2', padding_side='left')
print('finished tokenizer')

print('create pipeline')
# create the pipeline - NO sampling (temp=0)
llm_pipe = pipeline(
    "text-generation",
    model=llm,
    tokenizer=tokenizer,
    do_sample=False,
    return_full_text=False,
    max_new_tokens=2_048
)
print('pipeline created...')

# generate the queries on first 3 examples
#gen_queries = [gq[0]['generated_text'].strip() for gq in llm_pipe(hfds_dbchat_test['test_prompt'][:3])]

db_type = 'mysql'
schema_info = 'CREATE TABLE customer (customer_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,store_id TINYINT UNSIGNED NOT NULL,first_name VARCHAR(45) NOT NULL,last_name VARCHAR(45) NOT NULL,email VARCHAR(50) DEFAULT NULL,address_id SMALLINT UNSIGNED NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,create_date DATETIME NOT NULL,last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,PRIMARY KEY  (customer_id),KEY idx_fk_store_id (store_id),KEY idx_fk_address_id (address_id),KEY idx_last_name (last_name),CONSTRAINT fk_customer_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,CONSTRAINT fk_customer_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'
q = 'how many customers do we have?'

basic_prompt_template = """
### INSTRUCTIONS
You are a tool to generate a {db_type} SQL statement based on the given question and database schema.
Your answer should ONLY be a SQL statement, and strictly no other content. If you can't generate an answer with the given schema, return "NOT SURE" only.

### SCHEMA
{db_schema}

### QUESTION
{question}

### ANSWER
"""

def format_basic_prompt(q, schema, prompt, db_type='mysql', test=False):
  """Create prompt for inference - NO query included"""
  prompt_fmt = prompt.format(
      db_type=db_type,
      question=q,
      db_schema=schema,
  ).strip()
  if test:
    prompt_fmt = '[INST] \n' + prompt_fmt + ' [/INST]\n'
    return re.sub(r'\n\n\n+', '\n\n', prompt_fmt).strip()
  if prompt_fmt[-1] != ';':
    prompt_fmt += ';'
  prompt_fmt = '<s> [INST] \n' + prompt_fmt + ' </s>'
  # prompt_fmt = re.sub(r'\s+', ' ', prompt_fmt).strip()
  prompt_fmt = re.sub(r'\n\n\n+', '\n\n', prompt_fmt).strip()
  return re.sub(r'### ANSWER', '### ANSWER [/INST]', prompt_fmt).strip()

# create the prompt

prompt_str = format_basic_prompt(q,schema_info,basic_prompt_template)
print("prompt:")
print(prompt_str)

print('starting model inference...')
start_time = time.time()
print(start_time)
gen_queries = llm_pipe(prompt_str)
final_query = gen_queries[0]['generated_text'].strip()
end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
print(gen_queries)
print('final query:')
print(final_query)
print('test')