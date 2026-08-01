from openai import OpenAI



client = OpenAI()



print("=" * 50)

print("         VIRTUAL CAR GARAGE AI")

print("=" * 50)

print("Describe your car problem.")

print("Type 'quit' when you are finished.\n")



previous_response_id = None



while True:

    user_input = input("You: ").strip()



    if user_input.lower() == "quit":

        print("\nVirtual Car Garage AI: Goodbye!")

        break



    if not user_input:

        print("Please enter a question or type 'quit'.\n")

        continue



    request = {

        "model": "gpt-4.1-mini",

        "instructions": (

            "You are Virtual Car Garage AI, a cautious automotive assistant. "

            "Help the user investigate car problems by asking relevant questions. "

            "Do not claim certainty when information is limited. "

            "Explain likely possibilities clearly and recommend safe basic checks. "

            "State when the vehicle should not be driven or should be inspected "

            "by a qualified mechanic."

        ),

        "input": user_input,

    }



    if previous_response_id is not None:

        request["previous_response_id"] = previous_response_id



    try:

        response = client.responses.create(**request)



        print("\nVirtual Car Garage AI:")

        print(response.output_text)

        print()



        previous_response_id = response.id



    except Exception as error:

        print("\nSomething went wrong:")

        print(error)

        print()