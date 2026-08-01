from openai import OpenAI



client = OpenAI()



car_problem = input("Describe the car problem: ")



response = client.responses.create(

    model="gpt-4.1-mini",

    instructions=(

        "You are a cautious automotive assistant. "

        "Help the user describe and investigate a car problem. "

        "Do not claim certainty from limited information. "

        "Give likely possibilities, safe basic checks, and explain when "

        "the car should be inspected by a qualified mechanic."

    ),

    input=car_problem,

)



print("\nCar Garage AI:\n")

print(response.output_text)