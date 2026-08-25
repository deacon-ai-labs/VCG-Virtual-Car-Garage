from openai import OpenAI 

  

  

client = OpenAI() 

  

  

def ask_ai( 

    user_message: str, 

    vehicle_description: str | None, 

    previous_response_id: str | None, 

): 

    """Send a message to Garage AI and return the OpenAI response.""" 

  

    request = { 

        "model": "gpt-4.1-mini", 

        "instructions": ( 

            "You are Virtual Car Garage's cautious automotive assistant. " 

            "Help the user investigate automotive questions and problems. " 

            "Do not claim certainty from limited information. " 

            "Recommend only safe basic checks. " 

            "Clearly state when a vehicle should not be driven or should " 

            "be inspected by a qualified mechanic.\n\n" 

            "The currently selected vehicle is:\n" 

            f"{vehicle_description or 'No vehicle is currently selected.'}\n\n" 

            "Use the selected vehicle information whenever it is relevant. " 

            "Do not invent missing vehicle details." 

        ), 

        "input": user_message, 

    } 

  

    if previous_response_id is not None: 

        request["previous_response_id"] = previous_response_id 

  

    return client.responses.create(**request) 