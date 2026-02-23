# InvalidRequestError: context_length_exceeded
> Encountering InvalidRequestError: context_length_exceeded means your prompt exceeds the model's maximum token limit; this guide explains how to fix it.

## What This Error Means

When you encounter `InvalidRequestError: context_length_exceeded` from the OpenAI API, it means the total number of tokens in your request's input has surpassed the maximum limit defined for the specific model you are using. This isn't a transient network issue or a server-side bug; it's a hard limit imposed by the model's architecture. Every model, from `gpt-3.5-turbo` to various `gpt-4` iterations, has a fixed "context window" which determines how much information it can process in a single request. If your input – comprising the system message, the user's prompt, and any prior turns in a conversation – translates into more tokens than this window allows, the API will reject the request with this error.

## Why It Happens

At its core, the problem stems from how large language models process text. They don't see raw characters or words but rather "tokens." A token can be as short as a single character (like a comma) or as long as a word (like "hello" or "apple"). Complex words or phrases might break down into multiple tokens. The crucial point is that each model has a fixed memory, or "context window," measured in tokens. For example, some models might have a 4k token limit, others 8k, 16k, 32k, or even 128k.

When you send a request to the API, all the text in your `messages` array (for chat completions) or `prompt` (for older completion endpoints) is first tokenized. If the sum of these tokens exceeds the model's maximum context length, the `context_length_exceeded` error is returned. In my experience, this is particularly common in conversational applications where chat history accumulates over time, or when attempting to feed very large documents directly into a prompt.

## Common Causes

I've seen this error pop up in production and development for a few recurring reasons:

*   **Excessive Chat History:** In interactive or conversational applications, if you're sending the entire history of a chat session with every API call, the cumulative token count can quickly exceed the limit. This is, by far, the most frequent culprit.
*   **Overly Verbose Prompts:** Directly embedding very long documents, large code snippets, or extensive datasets into a single prompt string without summarization or truncation.
*   **Detailed Instructions and Examples:** While good prompt engineering often involves providing examples or elaborate instructions, including too many can eat into the token budget, especially if the user's actual query is also long.
*   **Combined System and User Content:** A lengthy system message, coupled with a long user prompt and previous assistant responses, pushes the total token count over the edge.
*   **Poor Token Estimation:** Not accurately calculating or estimating the token count of your input before sending it to the API. It's easy to underestimate how many tokens a seemingly short string of text can consume.

## Step-by-Step Fix

Addressing `context_length_exceeded` requires a systematic approach to manage your input.

1.  **Identify Your Model's Context Limit:**
    First, confirm the exact model you are using and its corresponding `max_tokens` context window. This information is typically found in the OpenAI documentation. For instance, `gpt-3.5-turbo` often has 4k or 16k token variants, while `gpt-4` has 8k, 32k, or even 128k (e.g., `gpt-4-turbo`). Knowing your limit is crucial for effective management.

2.  **Accurately Estimate Token Usage:**
    Before sending data to the API, use OpenAI's `tiktoken` library to count the tokens in your input. This is the most reliable method, as it uses the same tokenizer models as the OpenAI API.

    ```python
    import tiktoken

    def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0125"):
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base") # Fallback for new models
        
        num_tokens = 0
        for message in messages:
            # Each message takes a few tokens for metadata (role, name)
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += -1  # role and name are always provided as a pair
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    # Example usage:
    conversation_history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about large language models and their context windows."},
        # ... more messages
    ]
    
    current_tokens = num_tokens_from_messages(conversation_history, "gpt-3.5-turbo")
    print(f"Current token count: {current_tokens}")
    ```

3.  **Implement Input Truncation Strategies:**
    This is your primary method for mitigation.

    *   **Sliding Window for Conversations:** For chatbots, maintain a buffer of recent messages. When the token count exceeds a threshold (e.g., 80% of the model's limit), remove the oldest messages until the count is acceptable. I've often implemented this by prioritizing system messages and the most recent user/assistant turns.

    *   **Summarization:** Instead of discarding old messages entirely, periodically summarize earlier parts of the conversation and replace the verbose history with its concise summary. This preserves context without blowing up the token count.

    *   **Chunking Large Documents:** If you're processing large text documents, don't send the entire document at once. Break it into smaller, manageable chunks. You can then process each chunk iteratively, or use retrieval-augmented generation (RAG) techniques to fetch only the most relevant sections for a given query.

    *   **Pruning Irrelevant Details:** Review your system prompts and user inputs. Are there redundant instructions, verbose examples, or unnecessary data points that can be removed without losing critical context?

4.  **Upgrade to a Larger Context Model:**
    If truncating your input compromises the quality of the model's response, consider switching to an OpenAI model with a larger context window. For example, moving from `gpt-3.5-turbo` (4k tokens) to `gpt-4-turbo` (128k tokens) can significantly alleviate this constraint. Be mindful of the associated cost increase.

5.  **Refactor Prompt Engineering:**
    Sometimes, the issue isn't just the sheer volume but *how* the information is presented. Can you restructure your queries? Instead of providing a full database schema for every query, perhaps a summary or only relevant table definitions could be provided. Break down complex tasks into multiple API calls, each focusing on a specific sub-problem.

6.  **Implement Server-Side Validation:**
    Build token count checks into your application logic *before* making the API call. This allows you to handle the error gracefully on your end, perhaps by prompting the user to shorten their input, summarizing history automatically, or indicating that a larger model is needed.

## Code Examples

### 1. Basic Chat History Truncation (Python)

This example shows how to trim the oldest messages from a chat history to fit within a target token limit, prioritizing the system message and recent interactions.

```python
import tiktoken

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0125"):
    # (Same function as above, omitted for brevity)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens

def truncate_chat_history(messages, max_tokens, model="gpt-3.5-turbo-0125"):
    """
    Truncates the chat history to fit within max_tokens, prioritizing system message
    and recent interactions.
    """
    current_tokens = num_tokens_from_messages(messages, model)
    if current_tokens <= max_tokens:
        return messages

    print(f"Warning: Current tokens ({current_tokens}) exceed max_tokens ({max_tokens}). Truncating history.")

    truncated_messages = []
    # Always keep system message if present
    system_message = next((m for m in messages if m["role"] == "system"), None)
    if system_message:
        truncated_messages.append(system_message)
        # Account for system message tokens if it's kept
        max_tokens -= num_tokens_from_messages([system_message], model)

    # Add messages from newest to oldest until max_tokens is reached
    # Skip the system message if it was already added
    messages_to_add = [m for m in messages if m["role"] != "system"]
    
    # We add from the back (most recent) to the front (older)
    # Then reverse at the end to maintain original order
    temp_list = []
    for message in reversed(messages_to_add):
        message_tokens = num_tokens_from_messages([message], model)
        if num_tokens_from_messages(truncated_messages + temp_list + [message], model) <= max_tokens:
             temp_list.insert(0, message) # Insert at beginning to maintain original order after reversal
        else:
            print(f"Skipping message due to token limit: {message['content'][:50]}...")
            break # Stop adding if next message would exceed limit
            
    truncated_messages.extend(temp_list)
    
    return truncated_messages

# Example usage:
long_history = [
    {"role": "system", "content": "You are a friendly assistant."},
    {"role": "user", "content": "Hi, how are you? " * 50},
    {"role": "assistant", "content": "I'm doing well, thanks for asking! " * 60},
    {"role": "user", "content": "Can you summarize the history of the internet for me, focusing on key milestones and technologies?" * 100},
    {"role": "assistant", "content": "The internet began with ARPANET in the late 1960s, a project by the US Department of Defense. It evolved through various stages, including the development of TCP/IP, DNS, and the World Wide Web by Tim Berners-Lee in the early 1990s. Early technologies included packet switching and email. Key milestones include the release of Mosaic browser, dot-com boom, and the rise of social media. " * 200},
    {"role": "user", "content": "That's a lot of information! Can you tell me more about the impact of the World Wide Web specifically?"},
]

model_max_context = 4096 # Example for gpt-3.5-turbo
truncated_conversation = truncate_chat_history(long_history, model_max_context, "gpt-3.5-turbo")

print("\n--- Original Conversation ---")
for msg in long_history:
    print(f"{msg['role']}: {msg['content'][:70]}...")
print(f"Original tokens: {num_tokens_from_messages(long_history, 'gpt-3.5-turbo')}")

print("\n--- Truncated Conversation ---")
for msg in truncated_conversation:
    print(f"{msg['role']}: {msg['content'][:70]}...")
print(f"Truncated tokens: {num_tokens_from_messages(truncated_conversation, 'gpt-3.5-turbo')}")
```

### 2. Shell Command for Estimating Tokens (using `tiktoken`)

You can also quickly estimate tokens from the command line if you have `tiktoken` installed.

```bash
python -c "import tiktoken; enc = tiktoken.encoding_for_model('gpt-3.5-turbo'); print(len(enc.encode('Your very long prompt string goes here, and it will be tokenized.')))"
```

## Environment-Specific Notes

*   **Cloud Functions/Serverless (AWS Lambda, Google Cloud Functions, Azure Functions):**
    When deploying applications that use `tiktoken` in serverless environments, be mindful of package sizes and cold start times. `tiktoken` is a C extension, so ensure your deployment package includes the correct compiled binaries for the target runtime environment (e.g., `manylinux` wheels for Linux-based functions). Pre-loading the encoder can help mitigate cold start latency if invoked frequently. I've often seen performance issues here if not properly managed.

*   **Docker Containers:**
    Docker provides a consistent environment, which is great for `tiktoken`. Just ensure your `Dockerfile` includes `pip install tiktoken` and any other necessary dependencies. Make sure the Python version in your container matches your development environment to avoid unexpected C extension build issues.

*   **Local Development:**
    Debugging `context_length_exceeded` is typically easiest in a local development environment. You can rapidly iterate on truncation logic, test different prompt strategies, and use `tiktoken` interactively. Leverage your IDE's debugging tools to step through token counting and message truncation functions.

## Frequently Asked Questions

**Q: Does the `max_tokens` parameter in the API call prevent `context_length_exceeded`?**
**A:** No. The `max_tokens` parameter you set in the API request (`client.chat.completions.create(..., max_tokens=200)`) controls the maximum *length of the model's response*, not the maximum length of your input prompt. The `context_length_exceeded` error relates solely to the input side.

**Q: Is there a way to get "more" tokens for my model's context window?**
**A:** Not directly for a given model. The context window is a fixed architectural limit. Your options are to implement effective input truncation strategies, or to switch to a different OpenAI model that inherently offers a larger context window (e.g., moving from `gpt-3.5-turbo` to `gpt-4-turbo`).

**Q: How accurate is `tiktoken` for counting tokens?**
**A:** `tiktoken` is highly accurate because it's the official tokenizer library used by OpenAI. It precisely replicates how the API will tokenize your input, making it the gold standard for pre-flight token estimation.

**Q: Should I always trim from the beginning of the conversation history?**
**A:** Not always. While common, the optimal trimming strategy depends on your application's needs. Sometimes, older parts of the conversation might contain critical context (like initial user preferences). In my experience, a good approach is to always preserve the system message, then prioritize the most recent user/assistant turns, potentially summarizing older parts rather than just discarding them.

**Q: Can I catch this error and retry automatically?**
**A:** You can catch the `InvalidRequestError`, but retrying *without modifying the input* will only result in the same error. You must implement logic to reduce the token count of your request before attempting a retry.

## Related Errors

*   [openai-429](/errors/openai-429.html)
*   [openai-400](/errors/openai-400.html)