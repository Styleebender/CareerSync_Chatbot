import os
import logging
from typing import Annotated, Any, Literal, List, Optional
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.types import Command
from langgraph.graph import MessagesState, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.tools import TavilySearchResults
from pydantic import BaseModel, Field
# Local imports
from data_process import format_chat_data, process_job_data, process_linkedin_data
import agents_prompts
import linkedin_scraper
from dotenv import load_dotenv
load_dotenv()


# Logging Configuration
logging.basicConfig(
    filename='app.log',  # Log messages will be stored in 'app.log'
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# LLM
# gemini-2.0-flash-exp, gemini-1.5-pro, gemini-2.0-flash, gemini-1.5-flash, gemini-2.0-flash-thinking-exp-01-21
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=1,
    # streaming=True,
)

# Tools
#Web Search Tool
web_searcher_tool = TavilySearchResults(max_results=5)

@tool
def get_linkedin_profile_data(linkedin_url: str) -> dict:
    """
    Extract person's profile data from LinkedIn URL.
    Args:
        linkedin_url (str): Valid LinkedIn profile URL in format:
                            https://www.linkedin.com/in/xxxxxxxxxxxxx/
    Returns:
        dict: Response JSON containing profile data
    """
    # Validate URL input
    if not linkedin_url:
        return {"success": False, "title": "Invalid Input", "msg": "No LinkedIn Profile URL provided." }
    try:
        logging.info("getting data from get_linkedin_profile_data tool")
        profile_data = linkedin_scraper.get_profile_data(linkedin_url)
        if profile_data['success'] == False:
            return profile_data
        photo, background, formatted_data = process_linkedin_data(profile_data)
        return formatted_data
    except Exception as e:
        logging.exception("Error retrieving LinkedIn Profile data ")
        return {"success": False, "title": "Error", "msg": f"Error retrieving Linkedin Profile data: {str(e)}"}

@tool
def get_job_description_data(linkedin_job_url: str) -> dict:
    """
    Extract Job data from LinkedIn Job URL.
    Args:
        linkedin_job_url (str): Valid LinkedIn URL of the job with the following formats: 
        https://www.linkedin.com/jobs/collections/recommended/?currentJobId=XXXXXXXXXX, 
        https://www.linkedin.com/jobs/search/?currentJobId=XXXXXXXXXX or 
        https://www.linkedin.com/jobs/view/XXXXXXXXXX/.
    Returns:
        dict: Response JSON containing job data
    """
    if not linkedin_job_url:
        return {"success": False, "title": "Invalid Input", "msg": "No LinkedIn Job URL provided." }
    try:
        logging.info("getting data from get_job_description_data tool")
        profile_data = linkedin_scraper.get_Job_data(linkedin_job_url)
        if profile_data['success'] == False:
            return profile_data
        formatted_data = process_job_data(profile_data)
        return formatted_data
    except Exception as e:
        logging.exception("Error retrieving Job description data")
        return {"success": False, "title": "Error", "msg": f"Error retrieving job description data: {str(e)}"}
    

# Custom state for the graph.
class GraphsState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages] # Final message will be added
    user_query: str # contain the user query along with chat history data
    next: str # Next route
    output: str # Contain output of workers with tag

class Router(BaseModel):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["general_chat_handler", "linkedin_profile_analyst", "job_fit_analyst", "career_advisor", "cover_letter_generator", "opportunity_tracker", 'FINISH']

class GeneralChatAgent(BaseModel):
    reponse: str


# Helper function to create and execute a react agent node and return final output.
def execute_react_agent(
    state: GraphsState,
    react_template: str,
    prompt_template_str: str,
    tools: List[Any],
    worker_label: str,
    verbose = True,
    handle_parsing_errors = True,
    max_iterations = 5
) -> str:
    """
    Args:
    :state: current state of the graph.
    :react_template: template to create the query.
    :prompt_template_str: main prompt string for the agent.
    :tools: list of tools the agent can call.
    :worker_label: label for the worker.
    :verbose: logs.
    :handle_parsing_errors: parsing issues.
    :max_iterations: max llm steps
    :return: A formatted output.
    """
    if state.get("output", "") == "No outputs yet":
        state["output"] = ""

    inputs = {
        "user_query_details": state["user_query"],
        "worker_outputs": state["output"],
    }
    query = react_template.format(**inputs)
    main_prompt = PromptTemplate.from_template(prompt_template_str)
    
    try:
        agent = create_react_agent(llm=llm, tools=tools, prompt=main_prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=verbose,
            handle_parsing_errors=handle_parsing_errors,
            max_iterations = max_iterations
        )
        response = agent_executor.invoke({"input": query})
        worker_output = response.get("output", "").strip()
    except Exception as e:
        logging.exception(f"Error in {worker_label}: {e}")
        worker_output = f"[Error in {worker_label}: {e}]"
    
    # Append the worker's output to the state's output.
    new_output = f"{state['output']}\nWorker-{worker_label}:\n{worker_output}"
    return new_output


# Function to decide whether to continue worker/agent usage or end the process by routing to FINISH
def supervisor_node(state: GraphsState) -> Command[Literal["general_chat_handler", "linkedin_profile_analyst", "__end__"]]:
    """
    The supervisor node decides which worker should be called next,
    or whether the chain should end.
    """
    logging.info("Executing supervisor_node...")
    superviso_data = {
        "supervisor_prompt": agents_prompts. SUPERVISOR_PROMPT,
        "user_query_details": state['user_query'],
        "worker_output": state['output']

    }
    response = llm.with_structured_output(Router).invoke(agents_prompts.FINAL_SUPERVISOR_PROMPT.format(**superviso_data))
    print(type(response))
    goto = response.next
    final_resp = ""
    if goto == "FINISH":
        inputs = {
            "user_query_details": state['user_query'],
            "worker_outputs": state['output']
        }
        final_resp = llm.invoke(agents_prompts.FINAL_OUTPUT_FORMATTER.format(**inputs))
        logging.info("FINISH node...")
        # goto = END
        return Command(goto=END, update={"next": goto,
                                      "messages": [ AIMessage(content=final_resp.content, name="supervisor")] })
    
    return Command(goto=goto, update={"next": goto,})

# general_chat_handler node
def general_chat_handler(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    A simple general chat handler that directly uses the LLM with structured output.
    """
    logging.info("Executing general_chat_handler agent...")
    inputs = {
        "user_query_details": state['user_query'],
        "worker_outputs": state['output']
    }
    response = llm.with_structured_output(GeneralChatAgent).invoke(agents_prompts.GENERAL_CHAT_AGENT.format(**inputs))
    if state['output'] == "No outputs yet":
        state['output'] = ""
    formatted_output = state["output"] + "\nWorker-general_chat_handler: \n" + response.reponse
    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

# linkedin_profile_analyst node
def linkedin_profile_analyst(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    Worker node for analyzing LinkedIn profile data.
    """
    logging.info("Executing linkedin_profile_analyst agent...")

    formatted_output =  execute_react_agent(
        state=state,
        react_template=agents_prompts.REACT_INVOKE_TEMPLATE,
        prompt_template_str=agents_prompts.LINKEDIN_PROFILE_ANALYST_AGENT,
        tools=[get_linkedin_profile_data],
        worker_label="linkedin_profile_analyst",
    )

    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

# job_fit_analyst node
def job_fit_analyst(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    Worker node for analyzing job fit using LinkedIn profile and job description data.
    """
    logging.info("Executing job_fit_analyst agent...")

    formatted_output = execute_react_agent(
        state=state,
        react_template=agents_prompts.REACT_INVOKE_TEMPLATE,
        prompt_template_str=agents_prompts.JOB_FIT_ABALYSIS_PROMPT,
        tools=[get_linkedin_profile_data, get_job_description_data],
        worker_label="job_fit_analyst",
    )

    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

# career_advisor node
def career_advisor(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    Worker node for providing career advice using LinkedIn data and web search.
    """
    logging.info("Executing career_advisor agent...")

    formatted_output = execute_react_agent(
        state=state,
        react_template=agents_prompts.REACT_INVOKE_TEMPLATE,
        prompt_template_str=agents_prompts.CAREER_ADVISOR_PROMPT,
        tools=[get_linkedin_profile_data, web_searcher_tool],
        worker_label="career_advisor",
    )

    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

# cover_letter_generator node
def cover_letter_generator(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    Worker node for generating cover letters using LinkedIn and job description data.
    """
    logging.info("Executing cover_letter_generator agent...")

    formatted_output = execute_react_agent(
        state=state,
        react_template=agents_prompts.REACT_INVOKE_TEMPLATE,
        prompt_template_str=agents_prompts.COVER_LETTER_GENERATOR_PROMPT,
        tools=[get_linkedin_profile_data, get_job_description_data],
        worker_label="cover_letter_generator",
    )

    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

# opportunity_tracker node
def opportunity_tracker(state: GraphsState) -> Command[Literal["supervisor"]]:
    """
    Worker node for tracking opportunities using web search and LinkedIn data.
    """
    logging.info("Executing opportunity_tracker agent...")

    formatted_output = execute_react_agent(
        state=state,
        react_template=agents_prompts.REACT_INVOKE_TEMPLATE,
        prompt_template_str=agents_prompts.OPPORTUNITY_TRACKER_PROMPT,
        tools=[web_searcher_tool, get_linkedin_profile_data],
        worker_label="opportunity_tracker",
    )

    return Command(
        update={
            "output": formatted_output
        },
        # We want workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


# -----------------------------------------------------------------------------
# Build and Compile the State Graph
# -----------------------------------------------------------------------------
# Define the structure (nodes and directional edges between nodes) of the graph
graph = StateGraph(GraphsState)

graph.add_node("supervisor", supervisor_node)
graph.add_node("general_chat_handler", general_chat_handler)
graph.add_node("linkedin_profile_analyst", linkedin_profile_analyst)

graph.add_node("job_fit_analyst", job_fit_analyst)
graph.add_node("career_advisor", career_advisor)
graph.add_node("cover_letter_generator", cover_letter_generator)
graph.add_node("opportunity_tracker", opportunity_tracker)

graph.add_edge(START, "supervisor")


# Compile the state graph into a runnable object
graph_runnable = graph.compile()

# To generate the graph image
# from IPython.display import Image, display
# display(Image(graph_runnable.get_graph().draw_mermaid_png(output_file_path="graph.png")))


# Invoke Functions
# Without streaming
def invoke_our_graph(st_messages, callables):
    st_messages = format_chat_data(st_messages)
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    return graph_runnable.invoke({"user_query": st_messages, "output": "No outputs yet"}, config={"callbacks": callables})


# test invoke
def test_invoke_our_graph(st_messages):
    return graph_runnable.invoke({"user_query": st_messages, "output": "No outputs yet"})

# Test Query
def main() -> None:
    """
    For testing the graph.
    """
    test_query = """
    Chat History: "No chat history"
    Current User Question: "Can you find some AI events or networking opportunities in Pune India"
    """
    result = test_invoke_our_graph(test_query)
    print(result)

if __name__ == "__main__":
    main()
