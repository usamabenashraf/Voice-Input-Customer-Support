# ---------- agents.py ----------
from langchain.agents import Tool
from pydantic.v1 import BaseModel, Field
import re
import requests
from langchain.chains import RetrievalQA
from knowledge import build_rag
from langchain_community.llms import LlamaCpp
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from typing import Optional
import json

class OrderTrackerInput(BaseModel):
    order_id: str = Field(..., description="Order ID to track")

class ReturnPolicyInput(BaseModel):
    query: str = Field(..., description="User query about return policies")
Key="<Replace with your Llama API key>"
class CoordinatorAgent:
    def __init__(self, order_tracking_agent, returns_agent):
        self.order_tracking_agent = order_tracking_agent
        self.returns_agent = returns_agent
        self.parser = JsonOutputParser()
        self.extraction_llm = ChatGroq(model="llama3-70b-8192", api_key=Key)
        
        self.general_responses = [
            "I specialize in order tracking and returns. For other inquiries, please contact support@example.com",
            "I can help with order status and returns. For other questions, visit our FAQ at example.com/help",
            "My expertise is order management. For product questions, try our live chat support"
        ]
        
        # Routing prompt
        self.routing_prompt = ChatPromptTemplate.from_template("""
            # Strictly follow these categories:
                - OrdersAgent: Order status/shipping questions
                - ReturnsAgent: Returns/refunds/exchanges
                - GeneralAgent: Other inquiries


            # Must follow instruction:
            - Please make sure spellings are correct
            - Must follow JSON output format:                                               
            {{
            "Category": "OrdersAgent|ReturnsAgent|GeneralAgent",
            "Reasoning": "Reasoning for the category choice"
            }}
            Query: {input}
            Response:"""
        )
        # Order_id extraction prompt
        self.extraction_prompt = ChatPromptTemplate.from_template("""
            Extract order ID from query or respond with null.
            
            Query: {input}
            Order ID (only the ID or null):"""
        )

    def route(self, query: str, current_order_id: str = None) -> dict:
        try:
            chain = self.routing_prompt | self.extraction_llm | StrOutputParser()
            raw_output = chain.invoke({"input": query})  

            # Clean up any code block formatting
            if raw_output.startswith("```"):
                raw_output = re.sub(r"```[a-z]*", "", raw_output).replace("```", "").strip()

            # Attempt to parse JSON strictly
            result = json.loads(raw_output)
            print(result)
            # Validate and normalize output
            category = result.get("Category", "").strip()
            reasoning = result.get("Reasoning", "").strip()

            if category not in ["OrdersAgent", "ReturnsAgent", "GeneralAgent"]:
                raise ValueError(f"Unexpected category: {category}")

            return {
                "agent": category,
                "reasoning": reasoning or "Automatic routing"
            }

        except Exception as e:
            return {
                "agent": "GeneralAgent",
                "reasoning": f"Routing failed: {str(e)}"
            }

    def extract_order_id(self, text: str) -> Optional[str]:
        # First try fast regex extraction
        text = re.sub(r'(\d)[,\s]+(?=\d)', r'\1', text)
        regex_id = self._regex_extraction(text)
        
        if regex_id:
            return regex_id
            
        # Fallback to LLM extraction
        try:
            chain = self.extraction_prompt | self.extraction_llm | StrOutputParser()
            response = chain.invoke({"input": text}).strip()
            return response if response.lower() != "null" else None
        except:
            return None
        
    @staticmethod
    def _regex_extraction(text: str) -> Optional[str]:
        patterns = [
            r'\b(?:ORD|ORDER)[-_ ]?(\d{3,})\b',  # ORD123 or ORDER-456
            r'\bID[-_ ]?(\d{3,})\b',             # ID-789
            r'\b([A-Z]{3}\d{3,})\b',             # ABC123 format
            r'(?<=\border\s)(\d{3,})\b',          # After "order" keyword
            r'(?<=\btracking\s)(\d{3,})\b'        # After "tracking" keyword
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None

class OrderTrackingAgent:

    
    def __init__(self):
        self.tools = [
            Tool.from_function(
                func=self.get_order_status,
                name="order_status",
                description="Get order status by ID",
                args_schema=OrderTrackerInput
            )
        ]

    def process(self, query: str, current_order_id: str = None) -> dict:
        order_id = current_order_id
        try:
            if not order_id or len(order_id) < 5:  # Basic validation
                return {
                    "response": "Please provide a valid order number (e.g. 123456)",
                    "order_id": None
                }
            
            result = self.tools[0].run({"order_id": order_id})
            if str(result):
                return {
                "response": f"Order {order_id}: {result}",
                "order_id": order_id
                }
            return {
                "response": f"Order {order_id}: {result}",
                "order_id": order_id
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    "response": f"No order found with ID {order_id}. Please check and try again.",
                    "order_id": order_id
                }
            return {
                "response": f"HTTP error: {str(e)}",
                "order_id": order_id
            }
        except Exception as e:
            return {
                "response": f"Unexpected error: {str(e)}",
                "order_id": order_id
            }

    def get_order_status(self, order_id: str) -> str:
        response = requests.get(f"http://localhost:8000/order/{order_id}")
        print(response)
        response.raise_for_status()
        data = response.json()
        if data['days_shipped'] >=30:
            return "Your order is not eleigible for return, it has been more than 30 days since it was shipped"
        return data['status']

class ReturnsAgent:
    
    def __init__(self):
        self.rag = build_rag()
        self.llm = ChatGroq(model="llama3-70b-8192", api_key=Key)
        self.tools = [
            Tool.from_function(
                func=self.check_return_policy,  # Now properly bound
                name="check_return_policy",
                description="Check return eligibility using policy knowledge base",
                args_schema=ReturnPolicyInput
            ),
            Tool.from_function(
                func=self.get_order_status,  # Now properly bound
                name="get_order_return_eligibility",
                description="Check return eligibility by checking if the item has been shipped not more than 30 days ago",
                args_schema=ReturnPolicyInput
            )
        ]
        self.return_template = ChatPromptTemplate.from_template("""
                You are a helpful customer service assistant. Use the following return policy information to answer the customer's question.

                {context}

                Question: {question}
                Answer:
                """
            )

    def process(self, query: str, order_id: Optional[str] = None) -> dict:
        try:
            result = self.tools[0].run({"query": query})
            return {
                "response": result,
                "order_id": None
            }
        except Exception as e:
            return {
                "response": f"Error checking policies: {str(e)}",
                "order_id": None
            }
        try:
            result = self.tools[1].run({"query": order_id})
            return {
                "response": result,
                "order_id": None
            }
        except Exception as e:
            return {
                "response": f"Please provide order id",
                "order_id": None
            }
    # Use RetrievalQA to generate focused answers from policies
    def check_return_policy(self, query: str) -> str:
        try:
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.rag.as_retriever(search_kwargs={"k": 2}),
                return_source_documents=False,
                chain_type="stuff",
                chain_type_kwargs={
                    "prompt": self.return_template
                }
            )
            result = qa_chain.run(query)
            return result.strip()
        except Exception as e:
            return f"Policy check error: {str(e)}"

    def get_order_status(self, order_id: str) -> str:
        response = requests.get(f"http://localhost:8000/order/{order_id}")
        print(response)
        response.raise_for_status()
        data = response.json()
        if data['days_shipped'] >=30:
            return "Your order is not eleigible for return, it has been more than 30 days since it was shipped"
        return {
            "status": data['status'],
            "data": data['days_shipped']
        }
