from langchain_openai import ChatOpenAI
from src.config import settings

async def generate_chat_name(question: str, answer: str) -> str:
    """
    Generates a short chat name based on the first two messages.
    
    Args:
        question: The user's first question
        answer: The assistant's first answer
        
    Returns:
        str: A short chat name (no more than 12 tokens)
    """
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",
        max_tokens=12
    )
    
    prompt = f"""Based on the following dialogue, create a short chat name (maximum 12 tokens):

Question: {question}
Answer: {answer}

Create a very short and informative name that reflects the essence of the conversation.
The name should be no longer than 12 tokens.
"""

    response = await llm.ainvoke(prompt)
    return response.content.strip() 