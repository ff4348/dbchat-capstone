from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import time
import os
# !pip install trl accelerate bitsandbytes peft datasets -qU

# To get to memory and cpu information
import psutil
split_bar = '='*20
memory_info = psutil.virtual_memory()._asdict()
print(f"{split_bar} Memory Usage {split_bar}")
for k,v in memory_info.items():
  print(k, v)
print(f"{split_bar} CPU Usage {split_bar}")
print(f"CPU percent: {psutil.cpu_percent()}%")

# load model and tokenizer (may fail due to OOM errors depending on RAM available - Doesn't run with free GPU on colab)
print('starting model download...')
start_time = time.time()

# Get the current working directory
current_dir = os.getcwd()
# Move two directories back
data_path = os.path.join(current_dir, '..', '..')
# Normalize the path to resolve any '..'
data_path = os.path.normpath(data_path)
data_path = data_path + '/mistral7b_ft_hypm5_10e_dbchat'
print('data paht:',data_path)


print(start_time)
llm = AutoModelForCausalLM.from_pretrained(data_path, device_map='auto')
end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
print('starting tokenizer download...')
tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2')
print('finished tokenizer')

print('create pipeline')
# create the pipeline - NO sampling (temp=0)
llm_pipe = pipeline(
    "text-generation",
    model=llm,
    tokenizer=tokenizer,
    do_sample=False,
    return_full_text=False,
    max_new_tokens=2_048,
    temperature=0
)
print('pipeline created...')

# # generate the queries on first 3 examples
# gen_queries = [gq[0]['generated_text'].strip() for gq in llm_pipe(hfds_dbchat_test['test_prompt'][:3])]
# len(gen_queries)
# print(gen_queries)
print('test')
#gen_query = [gq[0]['generated_text'].strip() for gq in llm_pipe(hfds_dbchat_test['test_prompt'][:3])]