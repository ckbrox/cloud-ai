from google.adk.agents import Agent
from google.adk.tools import ToolContext, AgentTool
from ..workday import workday_client
from vertexai.preview.reasoning_engines import AdkApp
from datetime import datetime, UTC
from google.genai import types
from .ds_agent import ds_agent
import json
import asyncio



async def search_workers(query: str, tool_context: 'ToolContext'):
    """Searches workers in Workday

    Args:
        query (str): The search query for the worker.

    Returns:
        dict: returns the search results of worker objects that includes details about each worker.
    """

    workers = workday_client.rest_request(
        method='GET', 
        service='absenceManagement', 
        version='v2', 
        path=f'workers?search={query}'
    )
    
    workers = list(map(lambda worker: {k:v for k,v in worker.items() if k not in ['workerId']}, workers.get('data', [])))
    return workers


async def get_worker_details(worker_id:str, tool_context: 'ToolContext'):
    """Retrieves the details for the specified worker ID.
    Args:
        
        worker_id (str): The id of the worker. If you do not have the id but have the name, use the search workers tool. If you have neither, ask the user which worker they're referring to? Defaults to 'me' if not provided.
    Returns:
        dict: returns the details for the specified worker ID including their personal information.
    """

    # Get the Worker
    worker = workday_client.rest_request(
        method='GET', 
        service='absenceManagement', 
        version='v2', 
        path=f'workers/{worker_id}',
    )

    # Get the Person and enrich the Worker data
    person_id = worker.get('person').get('id')
    person = workday_client.rest_request(
        method='GET', 
        service='person', 
        version='v4', 
        path=f'people/{person_id}/personalInformation',
    )
    worker['person'] = person['data']

    return worker



def get_worker_timeoff(worker_id:str, from_date:str, to_date:str):
    """Retrieves the Time Off Entries for the specified worker ID. 

    Args:
        worker_id (str): The id of the worker. If you do not have the id but have the name, use the search workers tool. If you have neither, ask the user which worker they're referring to? If the user is asking about themselve, use "me". Defaults to 'me'.
        from_date (str): (Optional) The start of a date range filter using the yyyy-mm-dd format. Defaults to '2025-01-01' but can be any date (even before or after this date).
        to_date (str): (Optional) The end of a date range filter using the yyyy-mm-dd format. Defaults to '2025-05-29' but can be any date.

    Returns:
        dict: returns all Time Off Entries for the specified worker ID.
    """
    return workday_client.rest_request(
        method='GET', 
        service='absenceManagement', 
        version='v2', 
        path=f'workers/{worker_id}/timeOffDetails',
        params={
            'fromDate': from_date,
            'toDate': to_date
        }
    )


def get_expenses(from_date:str, to_date:str):
    """Retrieves the expenses for the specified date range.
    Args:
        from_date (str): (Optional) The start of a date range filter using the yyyy-mm-dd format. Defaults to '2025-01-01' but can be any date.
        to_date (str): (Optional) The end of a date range filter using the yyyy-mm-dd format. Defaults to '2025-05-29' but can be any date.

    Returns:
        dict: returns all expenses for the specified date range.
    """
    return workday_client.rest_request(
        method='GET',
        service='expense',
        version='v1',
        path='entries',
        params={
            'fromDate': from_date,
            'toDate': to_date
        }
    )



async def get_org_chart(worker_id:str, tool_context: 'ToolContext'):
    '''
    Gets an org chart (including subordinates and superiors) for a particular worker

    Args:
        worker_id (str): The id of the worker. If you do not have the id but have the name, use the search workers tool. If you have neither, ask the user which worker they're referring to? Defaults to 'me' if not provided.

    Returns:

    '''
    worker = await get_worker_details(worker_id, tool_context=tool_context)
    supervisory_org_id = worker.get('primaryJob', {}).get('supervisoryOrganization', {}).get('id')

    supervisory_org_chart = workday_client.rest_request(
        method='GET', 
        service='staffing', 
        version='v7', 
        path=f'supervisoryOrganizations/{supervisory_org_id}/orgChart',
        # pp=True'
    )

    data = supervisory_org_chart.get('data', [{}])[0]
    subordinates = data.get('subordinates', [])
    superior = data.get('superior', {})
    
    found_subordinate = None
    for subordinate in subordinates:
        managers = subordinate.get('managers', [])
        for manager in managers:
            manager_id = manager.get('id')
            if manager_id == worker_id:
                print(f'Manager ID ({manager_id}) matches worker ID ({worker_id})')
                found_subordinate = subordinate
                break
        if found_subordinate:
            break

    workday_client.pp(found_subordinate)

    subordinate_id = found_subordinate.get('id')
    print(subordinate_id, 'SUBORDINATE ID')


    return workday_client.rest_request(
        method='GET', 
        service='staffing', 
        version='v7', 
        path=f'supervisoryOrganizations/{supervisory_org_id}/orgChart/{subordinate_id}',
        pp=True
    )


async def get_team_details(worker_id:str, tool_context: 'ToolContext'):
    '''
    Gets the details of a worker's team including their personal information and time off data.

    Args:
        worker_id (str): The id of the worker. If you do not have the id but have the name, use the search workers tool. If you have neither, ask the user which worker they're referring to? Defaults to 'me' if not provided.

    Returns:
        dict: returns the details of a worker's team including their personal information and time off data.
    '''
    if worker_id == 'me':
        worker = await get_worker_details('me', tool_context=tool_context)
        worker_id = worker.get('id')

    org_chart = await get_org_chart(worker_id, tool_context)
    subordinates = org_chart.get('subordinates', [])


    tasks = []
    for subordinate in subordinates:
        if managers := subordinate.get('managers'):
            subordinate_worker_id = managers[0].get('id')
            tasks.append(get_worker_details(worker_id=subordinate_worker_id, tool_context=tool_context))


    subordinates = await asyncio.gather(*tasks)
    org_chart['subordinates'] = subordinates
    return org_chart




async def get_team_time_off_data(worker_id:str, question:str, from_date:str, to_date:str, tool_context: 'ToolContext'):
    '''
    Gets information about the time off of a worker's team.


    Args:
        worker (str): The id of the worker. If you do not have the id but have the name, use the search workers tool. If you have neither and the user is asking about themselves, use the get_worker_details tool first to get the id. Else, ask the user which worker they're referring to? Defaults to 'me' if not provided.

        question (str): The question to answer about the time off data
        
        from_date (str): (Optional) The start of a date range filter using the yyyy-mm-dd format. Defaults to '2025-01-01' but can be any date.
        
        to_date (str): (Optional) The end of a date range filter using the yyyy-mm-dd format. Defaults to '2025-05-29' but can be any date.

    Returns:
        dict: returns the time off data for the specified worker's team.
    '''

    if worker_id == 'me':
        worker = await get_worker_details('me', tool_context=tool_context)
        worker_id = worker.get('id')


    org_chart = await get_org_chart(worker_id, tool_context)

    subordinates = org_chart.get('subordinates', [])
    team_time_off = []
    for subordinate in subordinates:
        if managers := subordinate.get('managers'):
            subordinate_worker_id = managers[0].get('id')
            worker_name = managers[0].get('descriptor')
            time_off = get_worker_timeoff(worker_id=subordinate_worker_id, from_date=from_date, to_date=to_date)
            subordinate['time_off'] = time_off
            subordinate['worker_name'] = worker_name
            team_time_off.append({
                'worker_name': worker_name,
                'time_off': time_off
            })
    
    workday_client.pp(team_time_off)

    tool_context.state['team_time_off'] = team_time_off

    return {
        'team_time_off': team_time_off,
        'internal_message': f'The team time off data has been saved in state. The state key is "team_time_off".'
    }

    response = await call_data_scientist_agent(data=team_time_off, question=question, tool_context=tool_context)
    return response


async def call_data_scientist_agent(state_key:str, question: str, tool_context: ToolContext):
        """
        Tool to call data science (nl2py) agent. Useful for queries that require plotting, graphing or quantitative predictive analysis.

        Args:
            state_key (str): The key in the state where the data is stored.
            question (str): the question to ak about the data
        """

        data = tool_context.state[state_key]
        if not data:
            return {
                'success': False,
                'message': f'No data found for key: {state_key}. This data may no be compatiable with the data scientist agent. Just try answering the question based on what you know.'
            }


        question_with_data = f"""
    Question to answer: {question}

    Actual data to analyze prevoius quesiton is already in the following:
    {data}
    """

        agent_tool = AgentTool(agent=ds_agent)

        ds_agent_output = await agent_tool.run_async(
            args={"request": question_with_data}, tool_context=tool_context
        )
        tool_context.state["ds_agent_output"] = ds_agent_output
        return ds_agent_output


def request_time_off(date:str):
    f"""Requests time off for the user.

    Args:
        date (str): The date the user is requesting time off for in the format YYYY-MM-DD. You may need to calculate based on today's date.
    Returns:
        dict: returns the response from the Workday API.
    """

    data ={
        "days": [
            {
            "date": date,
            "dailyQuantity": 8,
            "timeOffType": {
                "id": "e7363fe834bd4c2883d36652ac6c979a" # Vacation
            },
            "start": f"{date}T08:00:00.000Z",
            "end": f"{date}T17:00:00.000Z",
            "comment": "Requested via Workday Agent."
            }
        ],
    }
    return workday_client.rest_request(
        method='POST',
        service='absenceManagement',
        version='v2',
        path='workers/me/requestTimeOff',
        json=data
    )


