from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

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
llm = AutoModelForCausalLM.from_pretrained(data_path, device_map='auto')
tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2')

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

# generate the queries on first 3 examples
gen_queries = [gq[0]['generated_text'].strip() for gq in llm_pipe(hfds_dbchat_test['test_prompt'][:3])]
len(gen_queries)
print(gen_queries)