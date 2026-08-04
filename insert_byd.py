from database import add_vehicle, get_vehicles





vehicle = {

    "profile_name": "Scott's BYD",

    "manufacturer": "BYD",

    "model": "Seal Excellence",

    "year": 2026,

    "engine": "530ps Dual Motor",

    "mileage": 1000,

    "modifications": "",

}



saved_vehicle = add_vehicle(vehicle)



print("Saved vehicle:")

print(saved_vehicle)



print("\nAll vehicles:")

for saved_vehicle in get_vehicles():

    print(saved_vehicle)