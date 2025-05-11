from llama_cpp import Llama

llm = Llama(
    model_path="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    n_ctx=2048,
    verbose=True
)

print(llm.create_chat_completion([{"role": "user", "content": "Hello"}]))