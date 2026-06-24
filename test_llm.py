import os
import sys

# Add src to path so we can import
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from generation.llm import LLM

llm = LLM()
print(f"Model: {llm.model}")
print(f"Available: {llm.is_available()}")
