import random
import pygame

# --- 1. RODIČOVSKÉ TŘÍDY (Dědičnost) ---
class Vehicle:
    """
    Základní třída pro všechna vozidla.
    Ostatní auta (Car, Truck, Bus) z ní budou dědit.
    """
    def __init__(self, position, speed, acceleration):
        self.position = position  # Pozice v metrech
        self.speed = speed        # Rychlost v m/s
        self.max_speed = speed    # Maximální rychlost pro opětovné rozjetí
        self.acceleration = acceleration
        self.stopped = False      # Zda auto stojí
        self.color = "red"        # Jen pro vizualizaci

    def get_length(self):
        """Tuto metodu přepíšeme v potomcích (Car, Truck...)."""
        return 0.0

    def move(self, dt):
        """
        Fyzika pohybu.
        Pokud auto nestojí, posuneme ho.
        """
        if not self.stopped:
            # Dráha = rychlost * čas
            self.position += self.speed * dt

    def stop(self):
        self.stopped = True
        self.speed = 0


# --- 2. KONKRÉTNÍ VOZIDLA ---

class Car(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 5.0)
        self.color = (0, 100, 255) # Modrá

    def get_length(self):
        return 4.5  # Osobák je nejkratší


class Bus(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 2.5)
        self.color = (255, 255, 0) # Žlutá

    def get_length(self):
        return 10.0 # Autobus je střední délky


class Truck(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 1.5)
        self.color = (0, 255, 0) # Zelená

    def get_length(self):
        return 12.0 # Kamion je nejdelší


# --- 3. SEMAFORY (Polymorfismus) ---

class TrafficLight:
    """
    Základní třída pro semafor (Rozhraní).
    """
    def __init__(self, position):
        self.position = position
        self.is_green = True

    def update(self, dt, vehicles):
        """
        Metoda update nově přijímá i seznam vozidel,
        aby 'chytré' semafory mohly reagovat na provoz.
        """
        pass


class CyclicTrafficLight(TrafficLight):
    """
    Klasický semafor - přepíná časově, auta ignoruje.
    """
    def __init__(self, position, interval):
        super().__init__(position)
        self.interval = interval
        self.timer = 0.0

    def update(self, dt, vehicles):
        # Tento semafor seznam 'vehicles' ignoruje, řídí se jen časem
        self.timer += dt
        if self.timer >= self.interval:
            self.is_green = not self.is_green
            self.timer = 0.0
            state = "ZELENÁ" if self.is_green else "ČERVENÁ"
            print(f"Cyklický semafor ({self.position}m) přepnul na: {state}")


class SmartTrafficLight(TrafficLight):
    """
    Inteligentní semafor.
    Defaultně je červená. Zelenou pustí jen, když se blíží auto.
    """
    def __init__(self, position, detection_range=50.0):
        super().__init__(position)
        self.detection_range = detection_range # Jak daleko semafor "vidí"
        self.is_green = False # Šetříme energii, defaultně červená :)

    def update(self, dt, vehicles):
        # 1. Zjistíme, jestli je nějaké auto v zóně před semaforem
        car_detected = False
        
        for vehicle in vehicles:
            distance = self.position - vehicle.position
            # Auto je před semaforem (distance > 0) A zároveň v dosahu senzoru
            if 0 < distance <= self.detection_range:
                car_detected = True
                break # Stačí nám jedno auto, abychom pustili zelenou
        
        # 2. Reakce semaforu
        if car_detected and not self.is_green:
            self.is_green = True
            print(f"SmartSemafor ({self.position}m): Auto detekováno -> ZELENÁ")
        
        elif not car_detected and self.is_green:
            self.is_green = False
            print(f"SmartSemafor ({self.position}m): Prázdno -> ČERVENÁ")


# --- 4. SILNICE (Řízení simulace) ---

class Road:
    def __init__(self, length):
        self.length = length
        self.vehicles = []       # Seznam vozidel
        self.traffic_lights = [] # Seznam semaforů

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_traffic_light(self, light):
        self.traffic_lights.append(light)

    def update(self, dt):
        # 1. Aktualizace semaforů
        for light in self.traffic_lights:
            light.update(dt, self.vehicles)

        # DŮLEŽITÉ: Seřadíme vozidla podle pozice (od nejvzdálenějšího po nejbližší)
        # Díky tomu přesně víme, že vehicles[i+1] je auto PŘED vehicles[i]
        self.vehicles.sort(key=lambda v: v.position)

        # 2. Hlavní smyčka pro každé vozidlo
        for i in range(len(self.vehicles)):
            vehicle = self.vehicles[i]
            
            # --- A) Resetování stavu a Akcelerace ---
            if vehicle.stopped:
                 # Pokud auto stojí (brzdí), nic neděláme, dokud nedostane pokyn k rozjezdu
                 pass 
            else:
                # Pokud auto jede pomaleji než je jeho maximálka, zrychlujeme
                if vehicle.speed < vehicle.max_speed:
                    # Vzorec: rychlost = rychlost + zrychlení * čas
                    vehicle.speed += vehicle.acceleration * dt
                    
                    # Pojistka: nesmíme překročit maximálku
                    if vehicle.speed > vehicle.max_speed:
                        vehicle.speed = vehicle.max_speed

            # --- B) Reakce na semafory ---
            should_stop_at_light = False
            for light in self.traffic_lights:
                distance = light.position - vehicle.position
                # Pokud je semafor blízko (méně než 10m) a je červená
                if 0 < distance < 10 and not light.is_green:
                    should_stop_at_light = True
                    break
            
            if should_stop_at_light:
                vehicle.stop()
            elif vehicle.stopped:
                # Pokud stálo, ale už je zelená, rozjedeme ho
                # Tady využíváme max_speed
                vehicle.stopped = False

            # --- C) Reakce na vozidla (Adaptivní tempomat) ---
            # Podíváme se, jestli je před námi nějaké auto
            # i + 1 je index auta před námi (protože jsme je seřadili)
            if i < len(self.vehicles) - 1:
                vehicle_ahead = self.vehicles[i+1]
                
                # Vypočítáme mezeru (od čumáku našeho auta k zadku auta před námi)
                # vehicle_ahead.get_length() je důležité, abychom do něj nevjeli polovinou
                gap = vehicle_ahead.position - vehicle.position - vehicle_ahead.get_length()
                
                # Bezpečná vzdálenost (např. 15 metrů)
                safe_distance = 15.0
                
                if gap < safe_distance:
                    # HROZÍ SRÁŽKA!
                    
                    if vehicle_ahead.stopped or vehicle_ahead.speed == 0:
                        # Pokud auto před námi stojí a jsme fakt blízko -> Zastavíme taky
                        if gap < 2.0: # 2 metry od nárazníku
                            vehicle.stop()
                        else:
                            # Dojíždíme ho, zpomalíme drasticky na 5 m/s
                            vehicle.speed = min(vehicle.speed, 5.0) 
                    else:
                        # Auto před námi jede, ale pomaleji -> přizpůsobíme rychlost
                        # Jedeme max tak rychle, jako auto před námi
                        if vehicle.speed > vehicle_ahead.speed:
                            vehicle.speed = vehicle_ahead.speed

            # 3. Aplikace pohybu
            vehicle.move(dt)


# --- 5. GENERÁTOR DOPRAVY ---

class TrafficGenerator:
    """
    Třída, která se stará o automatické generování dopravy.
    """
    def __init__(self, road, min_delay=3.0, max_delay=5.0):
        self.road = road
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timer = 0.0
        self.next_spawn_time = 0.0 # Hned na začátku zkusíme něco vygenerovat

    def update(self, dt):
        self.timer += dt
        
        # Pokud uplynul čas pro další auto
        if self.timer >= self.next_spawn_time:
            # Zkusíme přidat auto, pokud je místo
            if self.spawn_vehicle():
                # Pokud se to povedlo, resetujeme časovač a vylosujeme nový interval
                self.timer = 0.0
                self.next_spawn_time = random.uniform(self.min_delay, self.max_delay)

    def spawn_vehicle(self):
        """Vytvoří náhodné vozidlo a přidá ho na silnici, pokud je volno."""
        
        # 1. Kontrola, zda je na startu místo (abychom se nenaspawnovali do jiného auta)
        # Seřadíme auta, abychom našli to, co je nejblíž začátku (index 0)
        self.road.vehicles.sort(key=lambda v: v.position)
        
        if len(self.road.vehicles) > 0:
            first_vehicle = self.road.vehicles[0]
            # Pokud je první auto příliš blízko startu (např. méně než 15 metrů), negenerujeme nic
            if first_vehicle.position < 15.0:
                return False 

        # 2. Výběr typu vozidla (Vážený výběr - více aut než kamionů)
        # choices vrátí seznam, my chceme první prvek [0]
        vehicle_type = random.choices([Car, Truck, Bus], weights=[45, 30, 25], k=1)[0]

        # 3. Náhodná rychlost (trochu se liší od ideální)
        speed = 0
        if vehicle_type == Car:
            speed = random.uniform(22.0, 38.0)
        elif vehicle_type == Bus:
            speed = random.uniform(27.0, 23.0)
        else: # Truck
            speed = random.uniform(12.0, 18.0)

        # 4. Vytvoření instance a přidání na silnici
        new_vehicle = vehicle_type(position=-5.0, speed=speed) # Startujeme těsně před mapou
        self.road.add_vehicle(new_vehicle)
        
        # Pro debug vypíšeme info
        print(f"Generátor: Přidáno {vehicle_type.__name__} (Rychlost: {speed:.1f} m/s)")
        return True


# --- 6. VIZUALIZACE (Pygame) ---

class Visualizer:
    """
    Třída starající se o vykreslování simulace pomocí Pygame.
    Odděluje logiku (Road) od grafiky (Pygame).
    """
    def __init__(self, road, generator=None, width=1200, height=400):
        self.road = road
        self.generator = generator
        self.width = width
        self.height = height
        self.scale = 1  # 1 metr = 1 pixel
        
        # Inicializace Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dopravní Simulace - OOP Semestrální práce")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

    def draw_road(self):
        # Nakreslíme šedý pruh jako silnici uprostřed okna
        road_y = self.height // 2 - 20
        pygame.draw.rect(self.screen, (50, 50, 50), (0, road_y, self.road.length, 40))
        
        # Čáry na silnici
        pygame.draw.line(self.screen, (255, 255, 255), (0, self.height // 2), (self.road.length, self.height // 2), 2)

    def draw_vehicles(self):
        road_y = self.height // 2
        
        for v in self.road.vehicles:
            # Převod pozice na pixely
            x = v.position * self.scale
            y = road_y + 7 # Aby auto jelo v pruhu
            
            # Barva vozidla
            color = v.color
            
            if v.stopped:
                color = (100, 0, 0) # Tmavá, když stojí
            
            # Vykreslení (obdélník)
            # pygame.Rect(x, y, šířka, výška)
            pygame.draw.rect(self.screen, color, (x, y, v.get_length() * self.scale, 10))

    def draw_lights(self):
        road_y = self.height // 2 + 30 # Semafor bude pod silnicí
        
        for light in self.road.traffic_lights:
            x = light.position * self.scale
            
            # Barva světla
            color = (0, 255, 0) if light.is_green else (255, 0, 0)
            
            # Kolečko semaforu
            pygame.draw.circle(self.screen, color, (int(x), road_y), 8)
            
            # Detekční zóna pro Smart Semafor (jen pro debug)
            if isinstance(light, SmartTrafficLight):
                 pygame.draw.circle(self.screen, (255, 255, 255), (int(x), road_y), 3, 1)

    def run(self):
        running = True
        dt = 0.016 # Cca 60 FPS
        
        while running:
            # 1. Zpracování vstupů (zavření okna)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Zde můžeš přidat ovládání (např. mezerník pro pauzu)

            # 2. Aktualizace logiky simulace
            if self.generator:
                self.generator.update(dt)
            self.road.update(dt)

            # 3. Vykreslení
            self.screen.fill((30, 30, 30)) # Tmavé pozadí
            
            self.draw_road()
            self.draw_lights()
            self.draw_vehicles()
            
            # Výpis času
            time_text = self.font.render(f"Simulace běží...", True, (255, 255, 255))
            self.screen.blit(time_text, (10, 10))

            # Překlopení bufferu (zobrazení snímku)
            pygame.display.flip()
            
            # Čekání na další snímek
            self.clock.tick(60) # 60 FPS

        pygame.quit()


# --- SPUŠTĚNÍ ---

if __name__ == "__main__":
    # 1. Vytvoření logiky (Model)
    road = Road(1200) # Silnice dlouhá 1200m
    
    # Semafory
    road.add_traffic_light(CyclicTrafficLight(400, 5.0))      # Obyčejný na 400m, čas přepnutí 5s
    road.add_traffic_light(SmartTrafficLight(800, 50.0))     # Chytrý na 800m, dosah 50m
    
    # Auta
    """ road.add_vehicle(Car(30, 25))      # Auto
    road.add_vehicle(Truck(200, 15))     # Kamion
    road.add_vehicle(Bus(120, 20))    # Autobus """

    # Bude generovat auto každých 1.5 až 3.5 sekundy
    traffic_generator = TrafficGenerator(road, min_delay=1.5, max_delay=3.5)

    # 2. Spuštění vizualizace (View/Controller)
    app = Visualizer(road, generator=traffic_generator)
    app.run()