import json

from pathlib import Path



from openai import OpenAI





PROFILE_FILE = Path("vehicle_profile.json")



client = OpenAI()





def load_vehicle_profile():

    """Load an existing vehicle profile, or create a new one."""



    if PROFILE_FILE.exists():

        with PROFILE_FILE.open("r", encoding="utf-8") as file:

            return json.load(file)



    print("\nNo vehicle profile found. Let's create one.\n")



    profile = {

        "manufacturer": input("Manufacturer: ").strip(),

        "model": input("Model: ").strip(),

        "year": input("Year: ").strip(),

        "engine": input("Engine: ").strip(),

    }



    with PROFILE_FILE.open("w", encoding="utf-8") as file:

        json.dump(profile, file, indent=4)



    print("\nVehicle profile saved.\n")



    return profile





def describe_vehicle(profile):

    """Create a readable vehicle description."""



    return (

        f"{profile['year']} "

        f"{profile['manufacturer']} "

        f"{profile['model']}, "

        f"engine: {profile['engine']}"

    )





vehicle = load_vehicle_profile()

vehicle_description = describe_vehicle(vehicle)



print("=" * 50)

print("         VIRTUAL CAR GARAGE AI")

print("=" * 50)

print(f"Loaded vehicle: {vehicle_description}")

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

            f"The user's vehicle is: {vehicle_description}. "

            "Use that vehicle information when relevant. "

            "Help the user investigate car problems by asking useful questions. "

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