from openai import OpenAI



client = OpenAI()





def ask_ai(user_input, vehicle_description, previous_response_id):

    """

    Send a question to OpenAI and return the response.

    """



    request = {

        "model": "gpt-4.1-mini",

        "instructions": (

            "You are Virtual Car Garage AI, "

            "a cautious automotive assistant. "

            f"The user's vehicle is: {vehicle_description}. "

            "Use that information whenever it is relevant. "

            "Do not pretend to know things you cannot know. "

            "Always explain your reasoning."

        ),

        "input": user_input,

    }



    if previous_response_id:

        request["previous_response_id"] = previous_response_id



    response = client.responses.create(**request)



    return response