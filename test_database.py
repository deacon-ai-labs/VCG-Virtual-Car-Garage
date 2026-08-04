from database import add_vehicle, get_vehicles





vehicle = {

    "profile_name": "Deacon's EP3",

    "manufacturer": "Honda",

    "model": "Civic Type R EP3",

    "year": 2004,

    "engine": "2.0-litre K20A2",

    "mileage": 151500,

    "modifications": "BC Racing Coilovers, K100 ECU stage 1, 421 Exhaust Manifold, CatBack Exhaust Ram Air Intake",

}



saved_vehicle = add_vehicle(vehicle)



print("Saved vehicle:")

print(saved_vehicle)



print("\nAll vehicles:")

for saved_vehicle in get_vehicles():

    print(saved_vehicle)