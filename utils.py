from pypdf import PdfReader
from langchain.schema import Document
from langchain_openai.embeddings import AzureOpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAI
from langchain.prompts import PromptTemplate
from langchain_openai.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from parsers import ResumeEvaluation
from langchain_community.vectorstores import FAISS
import os
from config import config

api_key = config['api_key']
azure_endpoint = config['azure_endpoint']
api_version = config['api_version']

os.environ["AZURE_OPENAI_API_KEY"] = api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint

openaimodel = AzureChatOpenAI(
        model_name="gpt-35-turbo-16k",
        deployment_name="gpt-35-turbo-16k",
        openai_api_key= api_key,
        azure_endpoint= azure_endpoint,
        openai_api_type="azure",
        openai_api_version="2023-03-15-preview"
    )

def create_embeddings():
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="fyp-embedding-model",
        openai_api_version="2023-05-15"
    )

    return embeddings


# def create_llm_model():
#     llm = AzureChatOpenAI(
#         model_name="gpt-35-turbo-16k",
#         deployment_name="openaidemo-15999-16k",
#         openai_api_type="azure",
#         openai_api_version="2023-03-15",
#     )
#     return llm


def get_pdf_text(pdf_doc):
    text = ""
    pdf_reader = PdfReader(pdf_doc)
    for page in pdf_reader.pages:
        text += page.extract_text()

    return text


def create_docs(user_pdf_list, unique_id):
    docs = []

    for filename in user_pdf_list:
        chunks = get_pdf_text(filename)

        docs.append(Document(
            page_content=chunks,
            metadata={"name": filename.name,
                      "type": filename.type,
                      "size": filename.size,
                      "unique_id": unique_id}
        ))

    print(f"\nTotal Files: {len(docs)}\n")
    return docs


def create_chroma_db(function_embeddings, embedding_docs):
    # db = Chroma.from_documents(embedding_docs, function_embeddings, collection_name="resume_collection",
    #                            persist_directory="./Resume_Files")
    db = FAISS.from_documents(embedding_docs, function_embeddings)
    db.save_local("faiss_index")


def similar_docs(query, limit, function_embeddings, unique_id):
    # db = Chroma(persist_directory="./Resume_Files", collection_name="resume_collection",
    #             embedding_function=function_embeddings)
    db = FAISS.load_local("faiss_index", function_embeddings,allow_dangerous_deserialization=True)
    docs = db.similarity_search_with_score(query, int(limit), {"unique_id": unique_id})
    return docs


# Helps us get the summary of a document
def get_summary_of_resume(current_doc):
    model = openaimodel
    # llm = HuggingFaceHub(repo_id="bigscience/bloom", model_kwargs={"temperature":1e-10})
    chain = load_summarize_chain(model, chain_type="map_reduce")
    summary = chain.run([current_doc])

    return summary


def generate_resume_reasoning(resume, job_description):
    template_string = """
    You are an experienced technical recruiter and your task is to review the provided resume against the job description.
    You will share your professional evaluation on how the candidate is aligned with the job requirements
    by highlight the strengths and weaknesses of the applicant
    in relation to the specified job requirements.
    In the end also tell your verdict that should the candidate be hired
    for this specific job description or not.
    Also rate the resume on the scale of 1-10 according to job description.
    Your evaluation will help company to whether hire the candidate for the specified job description or not.

    Job Description: {job_description}

    Resume of Candidate: {resume}

    Evaluation:
    {format_instructions}
    """

    # template_string = """
    # You are an experienced technical recruiter and your task is to review the provided resume against the job description.
    # You will share your professional evaluation on how the candidate is aligned with the job requirements
    # by highlight the strengths and weaknesses of the applicant
    # in relation to the specified job requirements.
    # In the end also tell your verdict that should the candidate be hired
    # for this specific job description or not.
    # Also rate the resume on the scale of 1-10 according to job description.
    # Your evaluation will help company to whether hire the candidate for the specified job description or not.
    #
    # Job Description: {job_description}
    #
    # Resume of Candidate: {resume}
    #
    # Evaluation:
    # <evaluation>
    # <strengths>
    # <weakness>
    # <rating>
    # """

    json_parser = JsonOutputParser(pydantic_object=ResumeEvaluation)

    prompt_template = ChatPromptTemplate.from_template(template_string,
                                                       partial_variables={
                                                           "format_instructions": json_parser.get_format_instructions()})

    model = openaimodel

    chain = prompt_template | model | json_parser
    # chain = prompt_template | model

    resume_evaluations = chain.invoke({
        "job_description": job_description,
        "resume": resume
    })

    return resume_evaluations


def generate_job_description(jd_requirements):
    experience = jd_requirements["years_of_exp"]
    domain = jd_requirements["domain"] + " " + jd_requirements["sub_domain"]
    other_skills = jd_requirements["other_skills"]

    template_string = """
    You are a job description writer. I will give you some parameters and by keeping those parameters in context
    You will write a job description.

    Parameters:
    Years of Experience: {experience}
    Skill required: {domain}
    Other skills required: {skill}

    Please follow the following guidelines and you will be punished if you will not follow
    the guidelines

    1. You will not add any benefits or extra text from your own.
    2. The output should completely based on requirements mentioned in the parameters.
    3. Start directly with job description and do not add any location, company name etc. in it.
    4. Job description should must be aligned with Years of Experience.

    Job Description:
    """
    #
    prompt_template = ChatPromptTemplate.from_template(template_string)

    model = openaimodel
    chain = prompt_template | model

    generated_jd = chain.invoke({
        "experience": experience,
        "domain": domain,
        "skill": other_skills
    })
    return generated_jd.content
