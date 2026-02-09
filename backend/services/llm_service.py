"""
LLM service for response generation.
Supports OpenAI, Google Gemini, and Groq.
"""
import os
from typing import List, Dict, Optional


class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "500"))

        if self.provider == "google":
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is not set")
            genai.configure(api_key=api_key)
            self.model_name = os.getenv("GOOGLE_MODEL", "gemini-pro")
            self.client = genai.GenerativeModel(self.model_name)
            self.model = self.model_name
        elif self.provider == "groq":
            from openai import OpenAI
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        else:  # openai
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using LLM."""
        if not system_prompt:
            system_prompt = os.getenv(
                "SYSTEM_PROMPT",
                "You are a helpful AI assistant for this website. Answer questions based on the provided context. "
                "If you cannot find the answer in the context, politely say that you don't have that information."
            )

        try:
            if self.provider == "google":
                # Build prompt for Gemini
                prompt_parts = [system_prompt, "\n\n"]

                if conversation_history:
                    for msg in conversation_history[-10:]:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        prompt_parts.append(f"{role}: {msg['content']}\n")

                prompt_parts.append(f"\nContext information:\n{context}\n\n")
                prompt_parts.append(f"User question: {query}\n\n")
                prompt_parts.append("Please answer based on the context provided.")

                prompt = "".join(prompt_parts)

                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens,
                    }
                )
                return response.text

            else:  # openai or groq (both use OpenAI-compatible API)
                # Construct messages for OpenAI/Groq
                messages = [
                    {"role": "system", "content": system_prompt}
                ]

                if conversation_history:
                    messages.extend(conversation_history[-10:])

                user_message = f"""Context information:
{context}

User question: {query}

Please answer the question based on the context provided above. If the information needed to answer the question is not in the context, clearly state that you don't have that information available."""

                messages.append({"role": "user", "content": user_message})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating response with {self.provider}: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    def generate_response_stream(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ):
        """Generate streaming response using LLM."""
        system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            "You are a helpful AI assistant. Answer questions based on the provided context."
        )

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if conversation_history:
            messages.extend(conversation_history[-10:])

        user_message = f"""Context:\n{context}\n\nQuestion: {query}"""
        messages.append({"role": "user", "content": user_message})

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"Error generating streaming response: {e}")
            yield "I apologize, but I'm having trouble generating a response right now."


# Usage example
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    service = LLMService()

    test_context = """
    Our company offers three pricing plans:
    - Basic: $9/month with 10GB storage
    - Pro: $29/month with 100GB storage
    - Enterprise: Custom pricing with unlimited storage
    """

    test_query = "What pricing plans do you offer?"

    response = service.generate_response(test_query, test_context)
    print("Response:", response)

