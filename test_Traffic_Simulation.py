import pytest
from Traffic_Simulation import Vehicle, Car, Road, DIR_RIGHT

# --- TESTY TŘÍDY VEHICLE ---

def test_vehicle_initialization():
    # Ověří, že se vozidlo vytvoří se správnými parametry.
    v = Vehicle(position=100, speed=20, acceleration=2, direction=DIR_RIGHT)
    assert v.position == 100
    assert v.speed == 20
    assert v.direction == DIR_RIGHT
    assert v.stopped is False

def test_vehicle_movement():
    # Ověří fyziku pohybu (s = v * t).
    v = Vehicle(position=0, speed=10, acceleration=0, direction=DIR_RIGHT)
    v.move(dt=1.0)
    assert v.position == 10.0
    
    v.move(dt=0.5)
    assert v.position == 15.0  # 10 + (10 * 0.5)

def test_vehicle_stop():
    # Ověří funkci zastavení.
    v = Vehicle(position=0, speed=20, acceleration=0, direction=DIR_RIGHT)
    v.stop()
    assert v.stopped is True
    assert v.speed == 0

def test_acceleration_limit():
    # Ověří, že auto nepřekročí svou maximální rychlost.
    v = Vehicle(position=0, speed=10, acceleration=0, direction=DIR_RIGHT)
    v.max_speed = 15  # Limit
    
    # Zkusíme zrychlit o 10 (na 20), ale limit je 15
    v.accelerate(acceleration=10, dt=1.0)
    assert v.speed == 15

def test_braking():
    # Ověří zpomalování a že rychlost neklesne pod nulu.
    v = Vehicle(position=0, speed=10, acceleration=0, direction=DIR_RIGHT)
    
    # Zpomalíme o 5
    v.brake(deceleration=5, dt=1.0)
    assert v.speed == 5
    assert v.is_braking is True
    
    # Zpomalíme o dalších 10 (mělo by skončit na 0, ne -5)
    v.brake(deceleration=10, dt=1.0)
    assert v.speed == 0

# --- TESTY INTERAKCÍ (Mezery) ---

def test_get_distance_to():
    # Ověří výpočet mezery mezi auty.
    # Vzorec: Pozice_vpředu - Moje_pozice - Délka_auta_vpředu
    # Zadní auto na pozici 0
    car_rear = Car(speed=0, position=0, direction=DIR_RIGHT)
    
    # Přední auto na pozici 50. Car má délku 10.
    car_front = Car(speed=0, position=50, direction=DIR_RIGHT)
    
    # Očekáváme: 50 - 0 - 10 = 40
    gap = car_rear.get_distance_to(car_front)
    assert gap == 40.0

def test_distance_no_vehicle_ahead():
    # Ověří, že metoda vrátí velké číslo, pokud vpředu nic není.
    car = Car(speed=0, position=0, direction=DIR_RIGHT)
    assert car.get_distance_to(None) > 9000

# --- TESTY TŘÍDY ROAD ---

def test_road_add_vehicle():
    # Ověří, že se auto správně přidá do seznamu na silnici.
    road = Road(length=1000)
    car = Car(speed=10, position=0, direction=DIR_RIGHT)
    
    road.add_vehicle(car)
    
    assert len(road.vehicles) == 1
    assert road.vehicles[0] == car

def test_cars_finished_counter():
    # Ověří, zda silnice počítá auta, která dojela do cíle.
    road = Road(length=100)
    # Auto těsně před cílem (délka 10, pozice 95, zadek na 85)
    car = Car(speed=20, position=95, direction=DIR_RIGHT) 
    road.add_vehicle(car)
    
    # 1. Update - auto popojede, ale ještě je na silnici
    road.update(dt=0.1) 
    assert road.stats_cars_finished == 0
    
    # 2. Update - auto odjede daleko za cíl
    car.position = 200 # Teleport za cíl
    road.update(dt=0.1)
    
    assert road.stats_cars_finished == 1
    assert len(road.vehicles) == 0 # Mělo by zmizet ze silnice