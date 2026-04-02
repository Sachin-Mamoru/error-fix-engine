# InvalidRequestError: context_length_exceeded
> Encountering InvalidRequestError: context_length_exceeded means your prompt or conversation history has exceeded the maximum token limit for the model; this guide explains how to fix it.

## What This Error Means

When working with the OpenAI API for language models, `InvalidRequestError: context_length_exceeded` is a clear signal: the total length of your input has surpassed the model's capacity. Think of it like trying to fit a novel into a short story slot. Every interaction with an OpenAI model, particularly for chat completions, involves sending a "context window" of information. This window has a finite size, measured in "tokens."

Tokens are the fundamental units of text that language models process. A token can be a word, a part of a word, or even punctuation. For example, "token" might be one token, while "tokens" could be "token" + "s". The API takes your entire input (system message, user messages, assistant responses in a conversation, tool outputs) and tokenizes it. If the sum of these tokens exceeds the model's defined context limit, you hit this error.

## Why It Happens

The core reason for this error is the architectural limitation of transformer models, which underpin OpenAI's offerings. These models are designed to process a fixed-size sequence of tokens. While models have become increasingly capable and context windows have grown significantly, they are not infinite. Each model version (e.g., `gpt-3.5-turbo`, `gpt-4`, `gpt-4-32k`) comes with a specific, hard-coded maximum context length.

When you make an API call, the OpenAI endpoint calculates the total token count of your `messages` array, including all `role`s (system, user, assistant, tool). It then compares this against the chosen model's maximum allowed input token limit. If `total_input_tokens > model_max_input_tokens`, the `context_length_exceeded` error is returned instantly, preventing the model from even attempting to process the request. It's a pre-flight check to ensure the input fits the model's operational constraints.

It's important to distinguish this from the `max_tokens` parameter you might set in your API request. The `max_tokens` parameter controls the *maximum length of the model's generated output*. While the total number of tokens (input + output) must also fit within the model's overall context window, `context_length_exceeded` specifically indicates that the *input alone* is too large.

## Common Causes

In my experience, this error typically stems from a few recurring scenarios:

*   **Cumulative Conversation History in Chatbots:** This is perhaps the most frequent culprit. In interactive applications, especially chatbots or virtual assistants, developers often maintain a history of past turns to provide continuity. If this history isn't pruned or summarized, it can grow indefinitely, eventually pushing the total context size beyond the limit. I've seen this in production when state management for conversations isn't robust.
*   **Overly Long User Prompts:** Users sometimes paste entire documents, lengthy logs, or highly detailed specifications directly into a prompt. While beneficial for context, if the input is too large for the chosen model, it will fail.
*   **Verbose System Instructions:** The `system` role message provides crucial guidance to the model. However, excessively long or redundant system prompts can consume valuable context tokens, leaving less room for user input or conversation history.
*   **Large Tool Outputs:** When utilizing OpenAI's function calling feature, the `tool` role messages carry the output from external tools. If these tool outputs (e.g., database query results, complex API responses, parsed documents) are very large, they can quickly exhaust the context window.
*   **Direct Embedding of Documents:** Attempting to feed entire articles, reports, or large codebases directly into the prompt without prior summarization or retrieval-augmented generation (RAG) strategies. This is an inefficient and often impossible approach for anything beyond short texts.
*   **Development and Debugging Artifacts:** Sometimes, during development, extra debugging information or verbose logging might inadvertently be included in the prompt, especially when constructing it dynamically.

## Step-by-Step Fix

Addressing `context_length_exceeded` involves understanding your token usage and strategically reducing your input.

### 1. Identify Your Current Token Usage

The first step is always to measure. You need to know how many tokens your current problematic request consumes. OpenAI provides a tokenization library called `tiktoken` which is crucial for this.

```python
import tiktoken

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo": # note: future models might need different logic
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += -1  # role/name are always 1 token less
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}.
        See https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb""")

# Example usage:
example_messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "Paris is the capital of France."},
    {"role": "user", "content": "Tell me more about it."}
]

model_to_use = "gpt-3.5-turbo"
tokens = num_tokens_from_messages(example_messages, model=model_to_use)
print(f"Total tokens for messages: {tokens}")
# Compare this `tokens` value with the actual limit of your chosen model.
# e.g., gpt-3.5-turbo has a 4096 token context window (as of early 2023)
```

By accurately counting tokens, you can pinpoint which parts of your input are consuming the most space.

### 2. Prioritize and Prune Conversation History

For chatbots, the conversation history is the primary growth vector for context length. Implement a strategy to manage it:

*   **Fixed-Window Truncation:** The simplest method. Keep only the `N` most recent messages. When the `num_tokens_from_messages` exceeds a threshold (e.g., 75% of the model's limit), pop the oldest messages from the `messages` array until it fits.

    ```python
    MAX_TOKENS_FOR_MODEL = 4000 # Example for gpt-3.5-turbo (adjust for your model)
    HISTORY_BUFFER = 500 # Leave some room for new user input and assistant response

    def prune_messages(messages, model="gpt-3.5-turbo"):
        current_tokens = num_tokens_from_messages(messages, model)
        while current_tokens > (MAX_TOKENS_FOR_MODEL - HISTORY_BUFFER) and len(messages) > 1:
            # We assume the system message is important and should stay.
            # Pop the second element, which is typically the oldest user/assistant message.
            if messages[1]["role"] in ["user", "assistant", "tool"]: # Ensure we don't remove the system prompt
                messages.pop(1)
            else: # If the second element is not conversational, then something is wrong or system message is duplicated
                break
            current_tokens = num_tokens_from_messages(messages, model)
        return messages

    # In your chat loop:
    # messages.append({"role": "user", "content": user_input})
    # messages = prune_messages(messages, model_to_use)
    # response = client.chat.completions.create(model=model_to_use, messages=messages)
    ```

*   **Summarization:** A more sophisticated approach. Instead of simply deleting old messages, summarize them periodically. When the history grows too long, take a block of older messages, send them to the model for summarization, and replace the original block with a single, concise summary message. This retains more context than raw truncation. I've found this to be extremely effective in maintaining long-running conversations.

### 3. Optimize System Instructions and User Prompts

*   **Be Concise:** Review your system prompt. Can it be shorter without losing essential directives? Remove any filler or overly polite language.
*   **Dynamic Prompting:** Instead of including all possible context always, dynamically insert relevant information based on the user's current query.
*   **Input Pre-processing:** If users are providing large texts, consider pre-processing them.
    *   **Extraction:** Extract key entities, dates, or keywords.
    *   **Summarization:** Use a smaller, faster model (or even the target model in a separate call) to summarize large user inputs *before* sending them into the main chat context.
    *   **Chunking:** Break large documents into smaller chunks and process them sequentially or use a retrieval system.

### 4. Choose an Appropriate Model

OpenAI offers models with different context window sizes.

*   `gpt-3.5-turbo`: Typically 4k tokens.
*   `gpt-3.5-turbo-16k`: A larger context version, 16k tokens.
*   `gpt-4`: 8k tokens.
*   `gpt-4-32k`: A much larger context version, 32k tokens.

If your use case inherently requires processing vast amounts of information, upgrading to a model with a larger context window (e.g., from `gpt-3.5-turbo` to `gpt-3.5-turbo-16k` or `gpt-4-32k`) might be the most straightforward solution, assuming the cost implications are acceptable. Always verify the current context limits from OpenAI's official documentation.

### 5. Account for Output Tokens

Remember that the total tokens (input + expected output) must fit within the model's limit. While `context_length_exceeded` is about input, if you set `max_tokens` (for output) to a very high value when your input is already large, you might eventually hit the *total* context limit. It's good practice to leave a reasonable buffer for the model's response.

```python
# Calculate remaining tokens for output
# (MAX_TOKENS_FOR_MODEL - current_input_tokens) - small_buffer_for_safety
remaining_tokens = MAX_TOKENS_FOR_MODEL - num_tokens_from_messages(messages, model_to_use) - 100
# Then pass remaining_tokens to the max_tokens parameter
# response = client.chat.completions.create(model=model_to_use, messages=messages, max_tokens=remaining_tokens)
```

## Code Examples

Here are concise, copy-paste ready examples focusing on core fixes.

### Truncating Conversation History (Python)

This example shows how to keep the `system` message and truncate older `user`/`assistant` messages to fit within a `MAX_TOKENS_FOR_MODEL` budget.

```python
import tiktoken

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Accurately counts tokens for a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    # Specific logic for gpt-3.5-turbo for exact counting, adjust for other models
    if model == "gpt-3.5-turbo":
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if value is not None:
                    num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += -1  # role/name are always 1 token less
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        # Fallback for other models or simpler estimation
        return sum(len(encoding.encode(msg["content"])) for msg in messages if "content" in msg)


def truncate_chat_history(messages, model_limit, buffer_tokens=150, model="gpt-3.5-turbo"):
    """
    Truncates message history to fit within model_limit - buffer_tokens.
    Keeps the initial system message if present.
    """
    if not messages:
        return []

    # Ensure system message is always the first if it exists
    system_message = messages[0] if messages[0].get("role") == "system" else None
    conversational_messages = messages[1:] if system_message else messages[:]

    current_tokens = num_tokens_from_messages(messages, model)
    target_token_limit = model_limit - buffer_tokens

    # If already within limits, return as is
    if current_tokens <= target_token_limit:
        return messages

    # Truncate conversational messages from oldest
    while current_tokens > target_token_limit and conversational_messages:
        conversational_messages.pop(0) # Remove the oldest conversational message
        
        # Reconstruct messages with system message for token counting
        temp_messages = [system_message] + conversational_messages if system_message else conversational_messages
        current_tokens = num_tokens_from_messages(temp_messages, model)

    final_messages = [system_message] + conversational_messages if system_message else conversational_messages
    return final_messages


# --- Usage Example ---
MAX_GPT_3_5_TURBO_TOKENS = 4096

initial_messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "This is a very long initial message. " * 100}, # Simulate long message
    {"role": "assistant", "content": "Okay, I understand. " * 50},
    {"role": "user", "content": "What about the weather today?"},
    {"role": "assistant", "content": "It's sunny."},
    {"role": "user", "content": "And yesterday?"},
    {"role": "assistant", "content": "Yesterday it was cloudy."},
    {"role": "user", "content": "Tell me more about yesterday's weather conditions, " * 70} # Another long one
]

print(f"Initial tokens: {num_tokens_from_messages(initial_messages)}")

# Simulate adding a new user message that would exceed the limit
new_user_message = {"role": "user", "content": "Summarize our conversation so far about the weather. " * 20}
initial_messages.append(new_user_message)

print(f"Tokens after new message (before truncation): {num_tokens_from_messages(initial_messages)}")

# Now truncate
truncated_messages = truncate_chat_history(initial_messages, MAX_GPT_3_5_TURBO_TOKENS, buffer_tokens=500)
print(f"Tokens after truncation: {num_tokens_from_messages(truncated_messages)}")
print("\nTruncated messages:")
for msg in truncated_messages:
    print(f"- {msg['role']}: {msg['content'][:50]}...") # Print truncated content for brevity
```

## Environment-Specific Notes

The fundamental solution to `context_length_exceeded` remains the same across environments, but certain aspects of implementation or observation can differ.

*   **Cloud (e.g., AWS Lambda, GCP Cloud Functions):**
    *   **Payload Size Limits:** Be aware that beyond OpenAI's token limits, your cloud provider's API Gateway (if applicable) might have its own payload size limits (e.g., AWS API Gateway has a 10MB limit). While typical API requests to OpenAI models rarely hit this for text, it's a consideration if you're encoding very large prompt data within the request body itself.
    *   **Logging:** In serverless environments, robust logging is critical. Ensure you're logging the full `messages` payload (or at least its token count and a hash of its content) when an error occurs. This allows you to reconstruct the problematic request without having to redeploy or debug locally. Just be mindful of sensitive data in logs.
    *   **Performance:** Truncation or summarization logic adds a small amount of compute overhead. In highly scaled serverless functions, optimize this logic to avoid latency spikes.

*   **Docker:**
    *   **Container Resources:** If your Docker container is managing long-term conversation state (e.g., in-memory history), ensure the container has sufficient memory allocated. While token limits are about *request size*, keeping massive message histories in application memory can lead to out-of-memory errors in resource-constrained containers.
    *   **Observability:** Docker's logging mechanisms (e.g., `docker logs`) are your primary source for debugging. Similar to cloud environments, log relevant details of the API request when this error occurs.

*   **Local Development:**
    *   **Debugging Ease:** Local development typically offers the easiest debugging. You can print full request payloads directly to your console, step through code, and experiment with `tiktoken` without deployment cycles.
    *   **Resource Availability:** Your local machine likely has more available RAM than a serverless function, so you might not immediately hit application-level memory constraints if holding large histories, but the API error will still persist. Use this flexibility to thoroughly test your truncation/summarization strategies.

## Frequently Asked Questions

**Q: Is `max_tokens` (for output) related to `context_length_exceeded`?**
**A:** Indirectly. `context_length_exceeded` specifically means your *input* (`messages` array) is too large. However, the *total* number of tokens (input + output) must also fit within the model's overall context window. If your input is already near the limit, and you request a large `max_tokens` for the output, the API might not even start processing because it can infer the total would exceed. Best practice is to ensure sufficient room for both.

**Q: How do I know the exact token limit for my specific OpenAI model?**
**A:** Always refer to OpenAI's official documentation for the most up-to-date token limits for each model (e.g., `gpt-3.5-turbo`, `gpt-4`). While `tiktoken` helps with counting, the documentation is the definitive source for model capacity.

**Q: Can I simply increase the context window size for my model?**
**A:** No, the context window size is a fixed parameter for each specific model variant. You cannot arbitrarily "increase" it. Your options are to reduce your input data or switch to a different model that offers a larger context window (e.g., `gpt-3.5-turbo-16k`, `gpt-4-32k`).

**Q: Does setting `temperature` or `top_p` affect the context length?**
**A:** No. `temperature` and `top_p` are parameters that control the randomness and diversity of the model's output generation. They have no impact on the maximum number of input tokens the model can accept.

**Q: My application uses embedding models. Do they also have `context_length_exceeded`?**
**A:** Yes, embedding models also have their own specific input token limits, although the error message might vary slightly or be framed differently depending on the client library. The principle remains: the text you send for embedding cannot exceed that model's maximum input token length. However, the `InvalidRequestError: context_length_exceeded` error specifically discussed here is most commonly encountered with chat completion models due to their conversational nature.

## Related Errors