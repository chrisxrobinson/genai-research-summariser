import logging
from typing import Dict, List

import mistralai.client
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self):
        settings = get_settings()
        # Initialize OpenAI if API key is available
        if settings.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
        else:
            logger.warning("OpenAI API key not found in settings.")
            self.llm = None
        # Initialize Mistral if API key is available
        if settings.mistral_api_key:
            self.mistral_client = mistralai.client.MistralClient(
                api_key=settings.mistral_api_key
            )
        else:
            logger.warning("Mistral API key not found in settings.")
            self.mistral_client = None
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",  # Most cost-effective embedding model
            dimensions=settings.embedding_dimension,
        )
        # Setup prompts
        self.summary_prompt = PromptTemplate.from_template(
            """You are an expert in summarizing academic research papers.
            Create a concise but comprehensive summary of the following research paper.
            Focus on the main contributions, methodologies, and results.
            {text}
            Summary:"""
        )
        self.insights_prompt = PromptTemplate.from_template(
            """Analyze the following research paper and identify:
            1. Key innovations or breakthroughs
            2. Technical limitations or challenges
            3. Potential applications in industry
            Provide a structured analysis highlighting these aspects.
            {text}
            Analysis:"""
        )
        self.opportunities_prompt = PromptTemplate.from_template(
            """Based on the following research paper, identify:
            1. Future research directions
            2. Potential commercial applications
            3. Technological gaps that could be addressed
            Be specific and practical in your assessment.
            {text}
            Opportunities:"""
        )
        # Setup chains
        self.summary_chain = self.summary_prompt | self.llm | StrOutputParser()
        self.insights_chain = (
            self.insights_prompt | self.llm | StrOutputParser()
        )
        self.opportunities_chain = (
            self.opportunities_prompt | self.llm | StrOutputParser()
        )

    async def generate_summary(self, text: str) -> str:
        """Generate a summary of the document text"""
        return await self.summary_chain.ainvoke({"text": text})

    async def generate_insights(self, text: str) -> str:
        """Generate insights from the document text"""
        return await self.insights_chain.ainvoke({"text": text})

    async def generate_opportunities(self, text: str) -> str:
        """Generate opportunities from the document text"""
        return await self.opportunities_chain.ainvoke({"text": text})

    async def process_document(self, text: str) -> Dict[str, str]:
        """Process document text to generate summary, insights and opportunities"""
        # Truncate text if too large (OpenAI has context limits)
        if len(text) > 25000:  # Arbitrary limit to fit in context window
            text = text[:25000]
        summary = await self.generate_summary(text)
        insights = await self.generate_insights(text)
        opportunities = await self.generate_opportunities(text)
        return {
            "summary": summary,
            "insights": insights,
            "opportunities": opportunities,
        }

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for text chunks"""
        return await self.embeddings.aembed_documents(texts)

    async def answer_question(
        self, question: str, context_chunks: List[str]
    ) -> str:
        """Answer a question using retrieved context chunks"""
        # Combine context chunks
        context = "\n\n".join(context_chunks)
        qa_prompt = PromptTemplate.from_template(
            """You are an AI assistant helping to answer questions about research papers.
            Use the following context to answer the question. If you don't know the answer
            based on the context, say "I don't have enough information to answer this question."
            Context:
            {context}
            Question: {question}
            Answer:"""
        )
        qa_chain = qa_prompt | self.llm | StrOutputParser()
        return await qa_chain.ainvoke(
            {"context": context, "question": question}
        )


# Initialize LLM service singleton
llm_service = LLMService()
